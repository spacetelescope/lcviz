from glue.core.subset import Subset
from glue.config import data_translator
from glue.core import BaseData
from glue.core.exceptions import IncompatibleAttribute
from glue.core.roi import RangeROI
from glue.core.subset_group import GroupedSubset

from glue_jupyter.bqplot.scatter import BqplotScatterView

from astropy import units as u
from astropy.time import Time

from jdaviz.core.registries import viewer_registry
from jdaviz.configs.default.plugins.viewers import JdavizViewerMixin
from jdaviz.configs.specviz.plugins.viewers import SpecvizProfileView

from lcviz.state import ScatterViewerState

from lightkurve import LightCurve


__all__ = ['TimeScatterView', 'PhaseScatterView']


@viewer_registry("lcviz-time-viewer", label="flux-vs-time")
class TimeScatterView(JdavizViewerMixin, BqplotScatterView):
    # categories: zoom resets, zoom, pan, subset, select tools, shortcuts
    tools_nested = [
                    ['jdaviz:homezoom', 'jdaviz:prevzoom'],
                    ['jdaviz:boxzoom', 'jdaviz:xrangezoom', 'jdaviz:yrangezoom'],
                    ['jdaviz:panzoom', 'jdaviz:panzoom_x', 'jdaviz:panzoom_y'],
                    ['bqplot:xrange', 'bqplot:yrange', 'bqplot:rectangle'],
                    ['jdaviz:sidebar_plot', 'jdaviz:sidebar_export']
                ]
    default_class = LightCurve
    _state_cls = ScatterViewerState

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.display_mask = False
        self.time_unit = kwargs.get('time_unit', u.d)
        self._subscribe_to_layers_update()
        self.initialize_toolbar()
        self._subscribe_to_layers_update()
        # hack to inherit a small subset of methods from SpecvizProfileView
        # TODO: refactor jdaviz so these can be included in some mixin
        self._show_uncertainty_changed = lambda value: SpecvizProfileView._show_uncertainty_changed(self, value)  # noqa
        self._plot_uncertainties = lambda: SpecvizProfileView._plot_uncertainties(self)
        # TODO: _plot_uncertainties in specviz is hardcoded to look at spectral_axis and so crashes
        self._clean_error = lambda: SpecvizProfileView._clean_error(self)

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

    def set_plot_axes(self):
        # set which components should be plotted
        dc = self.jdaviz_app.data_collection
        component_labels = [comp.label for comp in dc[0].components]

        # Get data to be used for axes labels
        light_curve = self.data()[0]
        self._set_plot_x_axes(dc, component_labels, light_curve)
        self._set_plot_y_axes(dc, component_labels, light_curve)

    def _set_plot_x_axes(self, dc, component_labels, light_curve):
        self.state.x_att = dc[0].components[component_labels.index('World 0')]

        x_unit = self.time_unit
        reference_time = light_curve.meta.get('reference_time', None)

        if reference_time is not None:
            xlabel = f'{str(x_unit.physical_type).title()} from {reference_time.iso} ({x_unit})'
        else:
            xlabel = f'{str(x_unit.physical_type).title()} ({x_unit})'

        self.figure.axes[0].label = xlabel

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

    def _expected_subset_layer_default(self, layer_state):
        super()._expected_subset_layer_default(layer_state)

        layer_state.linewidth = 3

    def add_data(self, data, color=None, alpha=None, **layer_state):
        """
        Overrides the base class to add markers for plotting
        uncertainties and data quality flags.

        Parameters
        ----------
        data : :class:`glue.core.data.Data`
            Data object with the spectrum.
        color : obj
            Color value for plotting.
        alpha : float
            Alpha value for plotting.

        Returns
        -------
        result : bool
            `True` if successful, `False` otherwise.
        """
        # The base class handles the plotting of the main
        # trace representing the spectrum itself.
        result = super().add_data(data, color, alpha, **layer_state)

        # Set default linewidth on any created spectral subset layers
        # NOTE: this logic will need updating if we add support for multiple cubes as this assumes
        # that new data entries (from model fitting or gaussian smooth, etc) will only be spectra
        # and all subsets affected will be spectral
        for layer in self.state.layers:
            if "Subset" in layer.layer.label and layer.layer.data.label == data.label:
                layer.linewidth = 3

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


@viewer_registry("lcviz-phase-viewer", label="phase-vs-time")
class PhaseScatterView(TimeScatterView):
    def _set_plot_x_axes(self, dc, component_labels, light_curve):
        # setting of y_att will be handled by ephemeris plugin

        self.figure.axes[0].label = 'phase'
