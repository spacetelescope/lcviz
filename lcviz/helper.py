import astropy.units as u
import ipyvue
import os

from lightkurve import LightCurve

from glue.core.component_id import ComponentID
from glue.core.link_helpers import LinkSame
from jdaviz.core.helpers import ConfigHelper

__all__ = ['LCviz']

_default_time_viewer_reference_name = 'flux-vs-time'

custom_components = {'plugin-ephemeris-select': 'components/plugin_ephemeris_select.vue'}

# Register pure vue component. This allows us to do recursive component instantiation only in the
# vue component file
for name, path in custom_components.items():
    ipyvue.register_component_from_file(None, name,
                                        os.path.join(os.path.dirname(__file__), path))


def _get_range_subset_bounds(self, subset_state, *args, **kwargs):
    # Instead of overriding the jdaviz version of this method on jdaviz.Application,
    # we could put in jdaviz by (1) checking if helper has a
    # _default_time_viewer_reference_name, (2) using the LCviz version if so, and (3)
    # using the jdaviz version otherwise.
    viewer = self.get_viewer(self._jdaviz_helper._default_time_viewer_reference_name)
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


class LCviz(ConfigHelper):
    _default_configuration = {
        'settings': {'configuration': 'lcviz',
                     'visible': {'menu_bar': False,
                                 'toolbar': True,
                                 'tray': True,
                                 'tab_headers': True},
                     'dense_toolbar': False,
                     'context': {'notebook': {'max_height': '600px'}}},
        'toolbar': ['g-data-tools', 'g-subset-tools', 'lcviz-coords-info'],
        'tray': ['lcviz-metadata-viewer', 'lcviz-plot-options', 'lcviz-subset-plugin',
                 'lcviz-markers', 'flatten', 'frequency-analysis', 'ephemeris',
                 'binning', 'lcviz-export-plot'],
        'viewer_area': [{'container': 'col',
                         'children': [{'container': 'row',
                                       'viewers': [{'name': 'flux-vs-time',
                                                    'plot': 'lcviz-time-viewer',
                                                    'reference': 'flux-vs-time'}]}]}]}

    _component_ids = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._default_time_viewer_reference_name = _default_time_viewer_reference_name

        # override jdaviz behavior to support temporal subsets
        self.app._get_range_subset_bounds = (
            lambda *args, **kwargs: _get_range_subset_bounds(self.app, *args, **kwargs)
        )

        self.app._link_new_data = (
            lambda *args, **kwargs: _link_new_data(self.app, *args, **kwargs)
        )

        # inject custom css from lcviz_style.vue (on top of jdaviz styles)
        if hasattr(self.app, '_add_style'):
            # will be guaranteed after jdaviz 3.9
            self.app._add_style((__file__, 'lcviz_style.vue'))
        else:
            self.app.set_style_template_file((__file__, 'lcviz_style.vue'))

        # set the link to read the docs
        self.app.docs_link = "https://lcviz.readthedocs.io"

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

    def _phase_comp_lbl(self, component):
        return f'phase:{component}'

    def _set_data_component(self, data, component_label, values):
        if component_label not in self._component_ids:
            self._component_ids[component_label] = ComponentID(component_label)

        if self._component_ids[component_label] in data.components:
            data.update_components({self._component_ids[component_label]: values})
        else:
            data.add_component(values, self._component_ids[component_label])

        data.add_component(values, self._component_ids[component_label])
