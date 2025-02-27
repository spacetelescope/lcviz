from glue.core.subset import Subset
from glue.config import data_translator
from glue.core import BaseData
from glue.core.exceptions import IncompatibleAttribute
from glue.core.roi import RangeROI
from glue.core.subset_group import GroupedSubset

from glue_jupyter.bqplot.scatter import BqplotScatterView

from astropy import units as u
from astropy.time import Time

from jdaviz.core.events import NewViewerMessage
from jdaviz.core.registries import viewer_registry
from jdaviz.configs.cubeviz.plugins.viewers import (CubevizImageView,
                                                    WithSliceIndicator, WithSliceSelection)
from jdaviz.configs.default.plugins.viewers import JdavizViewerMixin
from jdaviz.configs.specviz.plugins.viewers import SpecvizProfileView

from lcviz.state import ScatterViewerState

from lightkurve import LightCurve

__all__ = ['TimeScatterView', 'PhaseScatterView', 'CubeView']


class CloneViewerMixin:
    def _get_clone_viewer_reference(self):
        base_name = self.reference.split("[")[0]
        name = base_name
        ind = 0
        while name in self.jdaviz_helper.viewers.keys():
            ind += 1
            name = f"{base_name}[{ind}]"
        return name

    def clone_viewer(self):
        name = self.jdaviz_helper._get_clone_viewer_reference(self.reference)

        self.jdaviz_app._on_new_viewer(NewViewerMessage(self.__class__,
                                                        data=None,
                                                        sender=self.jdaviz_app),
                                       vid=name, name=name)

        nv = self.jdaviz_helper.viewers.get(name)

        visible_layers = self.data_menu.data_labels_visible
        for layer in self.data_menu.data_labels_loaded:
            visible = layer in visible_layers
            nv.data_menu.add_data(layer)
            nv.data_menu.set_layer_visibility(layer, visible)
            # TODO: don't revert color when adding same data to a new viewer
            # (same happens when creating a phase-viewer from ephemeris plugin)

        new_viewer = self.jdaviz_app.get_viewer(name)
        if hasattr(self, 'ephemeris_component'):
            new_viewer._ephemeris_component = self._ephemeris_component
        for k, v in self.state.as_dict().items():
            if k in ('layers',):
                continue
            setattr(new_viewer.state, k, v)

        for this_layer_state, new_layer_state in zip(self.state.layers, new_viewer.state.layers):
            for k, v in this_layer_state.as_dict().items():
                if k in ('layer',):
                    continue
                setattr(new_layer_state, k, v)

        return new_viewer.user_api


@viewer_registry("lcviz-time-viewer", label="flux-vs-time")
class TimeScatterView(JdavizViewerMixin, CloneViewerMixin, WithSliceIndicator, BqplotScatterView):
    # categories: zoom resets, zoom, pan, subset, select tools, shortcuts
    tools_nested = [
                    ['jdaviz:homezoom', 'jdaviz:prevzoom'],
                    ['jdaviz:boxzoom', 'jdaviz:xrangezoom', 'jdaviz:yrangezoom'],
                    ['jdaviz:panzoom', 'jdaviz:panzoom_x', 'jdaviz:panzoom_y'],
                    ['bqplot:xrange', 'bqplot:yrange', 'bqplot:rectangle'],
                    ['jdaviz:selectslice'],
                    ['lcviz:viewer_clone', 'jdaviz:sidebar_plot', 'jdaviz:sidebar_export']
                ]
    default_class = LightCurve
    _state_cls = ScatterViewerState

    _native_mark_classnames = ('Image', 'ImageGL', 'Scatter', 'ScatterGL')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.display_mask = False
        self.time_unit = kwargs.get('time_unit', u.d)
        self.initialize_toolbar(default_tool_priority=['jdaviz:selectslice'])
        self._subscribe_to_layers_update()
        # hack to inherit a small subset of methods from SpecvizProfileView
        # TODO: refactor jdaviz so these can be included in some mixin
        self._show_uncertainty_changed = lambda value: SpecvizProfileView._show_uncertainty_changed(self, value)  # noqa
        self._plot_uncertainties = lambda: SpecvizProfileView._plot_uncertainties(self)
        # TODO: _plot_uncertainties in specviz is hardcoded to look at spectral_axis and so crashes
        self._clean_error = lambda: SpecvizProfileView._clean_error(self)
        self.density_map = kwargs.get('density_map', False)

    @property
    def slice_component_label(self):
        # label of the component in the lightcurves corresponding to the slice axis
        # calling data_collection_item.get_component(slice_component_label) must work
        return 'dt'

    @property
    def slice_display_unit_name(self):
        return 'time'

    def data(self, cls=None):
        data = []

        # TODO: generalize upstream in jdaviz.
        # This method is generalized from
        # jdaviz/configs/specviz/plugins/viewers.py
        # to support non-spectral viewers.
        for layer_state in self.state.layers:
            if hasattr(layer_state, 'layer'):
                lyr = layer_state.layer
                # For raw data, just include the data itself
                if isinstance(lyr, BaseData):
                    _class = cls or self.default_class

                    if _class is not None:
                        cache_key = lyr.label
                        if cache_key in self.jdaviz_app._get_object_cache:
                            layer_data = self.jdaviz_app._get_object_cache[cache_key]
                        else:
                            layer_data = lyr.get_object(cls=_class)
                            self.jdaviz_app._get_object_cache[cache_key] = layer_data

                        data.append(layer_data)

                # For subsets, make sure to apply the subset mask to the layer data first
                elif isinstance(lyr, (Subset, GroupedSubset)):
                    layer_data = lyr

                    if _class is not None:
                        handler, _ = data_translator.get_handler_for(_class)
                        try:
                            layer_data = handler.to_object(layer_data)
                        except IncompatibleAttribute:
                            continue
                    data.append(layer_data)

        return data

    def _apply_layer_defaults(self, layer_state):
        if getattr(layer_state.layer, 'meta', {}).get('Plugin', None) == 'Binning':
            # increased size of binned results, by default
            layer_state.size = 5
        layer_state.points_mode = 'markers'

    def set_plot_axes(self):
        # set which components should be plotted
        dc = self.jdaviz_app.data_collection
        component_labels = [comp.label for comp in dc[0].components]

        # Get data to be used for axes labels
        light_curve = self.data()[0]
        self._set_plot_x_axes(dc, component_labels, light_curve)
        self._set_plot_y_axes(dc, component_labels, light_curve)

    def _set_plot_x_axes(self, dc, component_labels, light_curve=None, reference_time=None):
        self.state.x_att = dc[0].components[component_labels.index('dt')]

        x_unit = self.time_unit

        if light_curve is not None and reference_time is None:
            reference_time = light_curve.meta.get('reference_time', None)
        elif reference_time is None:
            reference_time = dc[0].coords.reference_time

        xlabel = f'{str(x_unit.physical_type).title()} from {reference_time.iso} ({x_unit})'

        self.figure.axes[0].label = xlabel
        self.figure.axes[0].num_ticks = 5

    def _set_plot_y_axes(self, dc, component_labels, light_curve):
        self.state.y_att = dc[0].components[component_labels.index('flux')]

        y_unit = light_curve.flux.unit
        y_unit_physical_type = str(y_unit.physical_type).title()

        common_count_rate_units = (u.electron / u.s, u.dn / u.s, u.ct / u.s)

        if y_unit_physical_type == 'Unknown':
            if y_unit.is_equivalent(common_count_rate_units):
                y_unit_physical_type = 'Flux'
        if y_unit_physical_type == 'Dimensionless':
            y_unit_physical_type = 'Relative Flux'

        ylabel = f'{y_unit_physical_type}'

        if not y_unit.is_equivalent(u.dimensionless_unscaled):
            ylabel += f' ({y_unit})'

        self.figure.axes[1].label = ylabel

        # Make it so y axis label is not covering tick numbers (sometimes)
        self.figure.axes[1].label_offset = "-50"

        # Set (X,Y)-axis to scientific notation if necessary:
        self.figure.axes[0].tick_format = 'g'
        self.figure.axes[1].tick_format = 'g'

        self.figure.axes[1].num_ticks = 5

    def _expected_subset_layer_default(self, layer_state):
        super()._expected_subset_layer_default(layer_state)

        layer_state.linewidth = 3

        # optionally prevent subset from being rendered
        # as a density map, rather than shaded markers over data:
        layer_state.density_map = self.density_map

    def add_data(self, data, color=None, alpha=None, **layer_state):
        """
        Overrides the base class to handle subset styling defaults.

        Parameters
        ----------
        data : :class:`glue.core.data.Data`
            Data object with the light curve.
        color : obj
            Color value for plotting.
        alpha : float
            Alpha value for plotting.

        Returns
        -------
        result : bool
            `True` if successful, `False` otherwise.
        """
        result = super().add_data(data, color, alpha, **layer_state)

        for layer in self.layers:
            # optionally render as a density map
            layer.state.density_map = self.density_map

        # Set default linewidth on any created subset layers
        for layer in self.state.layers:
            if "Subset" in layer.layer.label and layer.layer.data.label == data.label:
                layer.linewidth = 3

        # update viewer limits when data are added
        self.set_plot_axes()
        self.state.reset_limits()

        return result

    def _show_uncertainty_changed(*args, **kwargs):
        # method required by jdaviz
        pass

    def apply_roi(self, roi, use_current=False):
        if isinstance(roi, RangeROI):
            # allow ROIs describing times to be applied with min and max defined as:
            #  1. floats, representing bounds in units of ``self.time_unit``
            #  2. Time objects, which get converted to work like (1) via the reference time
            if isinstance(roi.min, Time) or isinstance(roi.max, Time):
                reference_time = self.data()[0].meta.get('reference_time', 0)
                roi = roi.transformed(xfunc=lambda x: (x - reference_time).to_value(self.time_unit))

        super().apply_roi(roi, use_current=use_current)


@viewer_registry("lcviz-phase-viewer", label="flux-vs-phase")
class PhaseScatterView(TimeScatterView):
    def __init__(self, *args, **kwargs):
        self._ephemeris_component = 'default'
        super().__init__(*args, **kwargs)

    @property
    def ephemeris(self):
        ephem = self.jdaviz_helper.plugins.get('Ephemeris', None)
        if ephem is None:
            raise ValueError("must have ephemeris plugin loaded to access ephemeris")
        return ephem.ephemerides.get(self._ephemeris_component)

    def _set_plot_x_axes(self, dc, component_labels, light_curve):
        # setting of y_att will be handled by ephemeris plugin
        self.state.x_att = dc[0].components[component_labels.index(f'phase:{self._ephemeris_component}')]  # noqa
        self.figure.axes[0].label = 'phase'
        self.figure.axes[0].num_ticks = 5

    def times_to_phases(self, times):
        ephem = self.jdaviz_helper.plugins.get('Ephemeris', None)
        if ephem is None:
            raise ValueError("must have ephemeris plugin loaded to convert")

        return ephem.times_to_phases(times, ephem_component=self._ephemeris_component)

    def _set_slice_indicator_value(self, value):
        # NOTE: on first call, this will initialize the indicator itself
        self.slice_indicator.value = self.times_to_phases(value)


@viewer_registry("lcviz-cube-viewer", label="cube")
class CubeView(CloneViewerMixin, CubevizImageView, WithSliceSelection):
    # categories: zoom resets, zoom, pan, subset, select tools, shortcuts
    tools_nested = [
                    ['jdaviz:homezoom', 'jdaviz:prevzoom'],
                    ['jdaviz:boxzoom'],
                    ['jdaviz:panzoom'],
                    ['bqplot:rectangle'],
                    ['lcviz:viewer_clone', 'jdaviz:sidebar_plot', 'jdaviz:sidebar_export']
                ]
    # TODO: can we vary this default_class based on Kepler vs TESS, etc?
    # see https://github.com/spacetelescope/lcviz/pull/81#discussion_r1469721009
    default_class = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.display_mask = False
        self.time_unit = kwargs.get('time_unit', u.d)
        self.initialize_toolbar()
        self._subscribe_to_layers_update()

        # Hide axes by default
        self.state.show_axes = False

        # TODO: refactor upstream so lcviz can inherit cubeviewer methods/setup without
        # jdaviz-specific logic:
        # * _default_spectrum_viewer_reference_name
        # * _default_flux_viewer_reference_name
        # * _default_uncert_viewer_reference_name

    @property
    def slice_component_label(self):
        # label of the component in the cubes corresponding to the slice axis
        # calling data_collection_item.get_component(slice_component_label) on any
        # input cube-data must work
        return 'dt'

    @property
    def slice_index(self):
        # index in viewer.slices corresponding to the slice axis
        return 0

    @property
    def slice_display_unit_name(self):
        return 'time'

    def _initial_x_axis(self, *args):
        # Make sure that the x_att/y_att is correct on data load
        # called via a callback set upstream in CubevizImageView when reference_data is changed
        ref_data = self.state.reference_data
        if ref_data is not None:
            self.state.x_att = ref_data.id['Pixel Axis 2 [x]']
            self.state.y_att = ref_data.id['Pixel Axis 1 [y]']

    def _on_layers_update(self, layers=None):
        super()._on_layers_update(layers=layers)
        ref_data = self.state.reference_data
        if ref_data is None:
            return
        flux_comp = ref_data.id['flux']
        for layer in self.state.layers:
            if hasattr(layer, 'attribute') and layer.attribute != flux_comp:
                layer.attribute = flux_comp

    def data(self, cls=None):
        # TODO: generalize upstream in jdaviz.
        # This method is generalized from
        # jdaviz/configs/cubeviz/plugins/viewers.py
        return [layer_state.layer
                for layer_state in self.state.layers
                if hasattr(layer_state, 'layer') and
                isinstance(layer_state.layer, BaseData)]
