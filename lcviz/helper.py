import astropy.units as u
import ipyvue
import os

from lightkurve import LightCurve

from glue.config import settings as glue_settings
from glue.core.component_id import ComponentID
from glue.core.link_helpers import LinkSame
from glue.core.units import unit_converter
from jdaviz.core.helpers import ConfigHelper

from lcviz import __version__
from lcviz.viewers import TimeScatterView

__all__ = ['LCviz']


@unit_converter('custom-lcviz')
class UnitConverter:
    def equivalent_units(self, data, cid, units):
        return set(list(map(str, u.Unit(units).find_equivalent_units(include_prefix_units=True))))

    def to_unit(self, data, cid, values, original_units, target_units):
        # for some reason, glue is trying to request a change for cid='flux' from d to electron / s
        if target_units not in self.equivalent_units(data, cid, original_units):
            return values
        return (values * u.Unit(original_units)).to_value(u.Unit(target_units))


glue_settings.UNIT_CONVERTER = 'custom-lcviz'

custom_components = {'plugin-ephemeris-select': 'components/plugin_ephemeris_select.vue'}

# Register pure vue component. This allows us to do recursive component instantiation only in the
# vue component file
for name, path in custom_components.items():
    ipyvue.register_component_from_file(None, name,
                                        os.path.join(os.path.dirname(__file__), path))


def _get_range_subset_bounds(self, subset_state, *args, **kwargs):
    viewer = self._jdaviz_helper.default_time_viewer._obj
    light_curve = viewer.data()[0]
    reference_time = light_curve.meta['reference_time']
    if viewer:
        # TODO: use display units once implemented in Glue for ScatterViewer
        # units = u.Unit(viewer.state.x_display_unit)
        units = u.Unit(viewer.time_unit)
    else:  # pragma: no cover
        raise ValueError("Unable to find time axis units")

    region = reference_time + u.Quantity([subset_state.lo * units, subset_state.hi * units])

    return [{"name": subset_state.__class__.__name__,
             "glue_state": subset_state.__class__.__name__,
             "region": region,
             "subset_state": subset_state}]


def _link_new_data(app, reference_data=None, data_to_be_linked=None):
    dc = app.data_collection
    ref_data = dc[reference_data] if reference_data else dc[0]
    linked_data = dc[data_to_be_linked] if data_to_be_linked else dc[-1]

    new_link = LinkSame(
        cid1=ref_data.world_component_ids[0],
        cid2=linked_data.world_component_ids[0],
        data1=ref_data,
        data2=linked_data,
        labels1=ref_data.label,
        labels2=linked_data.label
    )

    dc.add_link(new_link)
    return


def _get_display_unit(app, axis):
    if app._jdaviz_helper is None or app._jdaviz_helper.plugins.get('Unit Conversion') is None:  # noqa
        # fallback on native units (unit conversion is not enabled)
        if axis == 'time':
            return u.d
        elif axis == 'flux':
            return app._jdaviz_helper.default_time_viewer._obj.data()[0].flux.unit
        else:
            raise ValueError(f"could not find units for axis='{axis}'")
    try:
        # TODO: need to implement and add unit conversion plugin for this to be able to work
        return getattr(app._jdaviz_helper.plugins.get('Unit Conversion')._obj,
                       f'{axis}_unit_selected')
    except AttributeError:
        raise ValueError(f"could not find display unit for axis='{axis}'")


class LCviz(ConfigHelper):
    _default_configuration = {
        'settings': {'configuration': 'lcviz',
                     'visible': {'menu_bar': False,
                                 'toolbar': True,
                                 'tray': True,
                                 'tab_headers': True},
                     'dense_toolbar': False,
                     'context': {'notebook': {'max_height': '600px'}}},
        'toolbar': ['g-data-tools', 'g-subset-tools', 'g-viewer-creator', 'lcviz-coords-info'],
        'tray': ['lcviz-metadata-viewer', 'flux-column',
                 'lcviz-plot-options', 'lcviz-subset-plugin',
                 'lcviz-markers', 'time-selector',
                 'stitch', 'flatten', 'frequency-analysis', 'ephemeris',
                 'binning', 'lcviz-export'],
        'viewer_area': [{'container': 'col',
                         'children': [{'container': 'row',
                                       'viewers': [{'name': 'flux-vs-time',
                                                    'plot': 'lcviz-time-viewer',
                                                    'reference': 'flux-vs-time'}]}]}]}

    _component_ids = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # override jdaviz behavior to support temporal subsets
        self.app._get_range_subset_bounds = (
            lambda *args, **kwargs: _get_range_subset_bounds(self.app, *args, **kwargs)
        )

        self.app._link_new_data = (
            lambda *args, **kwargs: _link_new_data(self.app, *args, **kwargs)
        )

        self.app._get_display_unit = (
            lambda *args, **kwargs: _get_display_unit(self.app, *args, **kwargs)
        )

        # inject custom css from lcviz_style.vue (on top of jdaviz styles)
        self.app._add_style((__file__, 'lcviz_style.vue'))

        # set the link to read the docs
        self.app.vdocs = 'latest' if 'dev' in __version__ else 'v'+__version__
        self.app.docs_link = f"https://lcviz.readthedocs.io/en/{self.app.vdocs}"
        for plugin in self.plugins.values():
            # NOTE that plugins that need to override upstream docs_link should do so in
            # an @observe('vdocs') rather than the init, since plugin instances have
            # already been initialized
            plugin._obj.vdocs = self.app.vdocs

    def load_data(self, data, data_label=None):
        """
        Load data into LCviz.

        Parameters
        ----------
        data : obj or str
            File name or object to be loaded. Supported formats include:

            * ``'filename.fits'`` (or any extension that ``astropy.io.fits``
              supports)
            * `~lightkurve.LightCurve` (extracts the default flux column)
        data_label : str or `None`
            Data label to go with the given data. If not given, this is
            automatically determined from filename or randomly generated.
            The final label shown in LCviz may have additional information
            appended for clarity.
        """
        super().load_data(
            data=data,
            parser_reference='light_curve_parser',
            data_label=data_label
        )

    def get_data(self, data_label=None, cls=LightCurve, subset=None):
        """
        Returns data with name equal to data_label of type cls with subsets applied from
        subset_to_apply.

        Parameters
        ----------
        data_label : str, optional
            Provide a label to retrieve a specific data set from data_collection.
        cls : light curve class, optional
            The type that data will be returned as.
        subset : str, optional
            Subset that is to be applied (as a mask) to the data before it is returned.

        Returns
        -------
        data : cls
            Data is returned as type cls with subsets applied.
        """
        return super()._get_data(data_label=data_label, mask_subset=subset, cls=cls)

    @property
    def default_time_viewer(self):
        tvs = [viewer for vid, viewer in self.app._viewer_store.items()
               if isinstance(viewer, TimeScatterView)]
        if not len(tvs):
            raise ValueError("no time viewers exist")
        return tvs[0].user_api

    @property
    def _has_cube_data(self):
        for data in self.app.data_collection:
            if data.ndim == 3:
                return True
        return False

    @property
    def _tray_tools(self):
        """
        Access API objects for plugins in the app toolbar.

        Returns
        -------
        plugins : dict
            dict of plugin objects
        """
        # TODO: provide user-friendly labels, user API, and move upstream to be public
        # for now this is just useful for dev-debugging access to toolbar entries
        from ipywidgets.widgets import widget_serialization
        return {item['name']: widget_serialization['from_json'](item['widget'], None)
                for item in self.app.state.tool_items}

    def _get_clone_viewer_reference(self, reference):
        base_name = reference.split("[")[0]
        name = base_name
        ind = 0
        while name in self.viewers.keys():
            ind += 1
            name = f"{base_name}[{ind}]"
        return name

    def _phase_comp_lbl(self, component):
        return f'phase:{component}'

    def _set_data_component(self, data, component_label, values):
        if component_label in self._component_ids:
            component_id = self._component_ids[component_label]
        else:
            existing_components = [component.label for component in data.components]
            if component_label in existing_components:
                component_id = data.components[existing_components.index(component_label)]
            else:
                component_id = ComponentID(component_label)
                self._component_ids[component_label] = component_id

        if component_id in data.components:
            data.update_components({component_id: values})
        else:
            data.add_component(values, component_id)
