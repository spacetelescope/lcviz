import astropy.units as u

from lightkurve import LightCurve

from jdaviz.core.helpers import ConfigHelper
from lcviz.plugins import StyleWidget

__all__ = ['LCviz']


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
    else:
        raise ValueError("Unable to find time axis units")

    region = reference_time + u.Quantity([subset_state.lo * units, subset_state.hi * units])

    return [{"name": subset_state.__class__.__name__,
             "glue_state": subset_state.__class__.__name__,
             "region": region,
             "subset_state": subset_state}]


class LCviz(ConfigHelper):
    _default_configuration = {
        'settings': {'configuration': 'lcviz',
                     'visible': {'menu_bar': False,
                                 'toolbar': True,
                                 'tray': True,
                                 'tab_headers': False},
                     'dense_toolbar': False,
                     'context': {'notebook': {'max_height': '600px'}}},
        'toolbar': ['g-data-tools', 'g-subset-tools'],
        'tray': [
            'g-metadata-viewer', 'lcviz-plot-options', 'g-subset-plugin',
            'HelloWorldPlugin', 'g-export-plot'
        ],
        'viewer_area': [{'container': 'col',
                         'children': [{'container': 'row',
                                       'viewers': [{'name': 'flux-vs-time',
                                                    'plot': 'lcviz-time-viewer',
                                                    'reference': 'flux-vs-time'}]}]}]}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._default_time_viewer_reference_name = 'flux-vs-time'

        # override jdaviz behavior to support temporal subsets
        self.app._get_range_subset_bounds = (
            lambda *args, **kwargs: _get_range_subset_bounds(self.app, *args, **kwargs)
        )

        # inject the style widget to override app-css from lcviz_style.vue
        style_widget = StyleWidget()
        self.app.state.style_widget = "IPY_MODEL_" + style_widget.model_id

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

    def get_data(self, data_label=None, cls=LightCurve, subset_to_apply=None):
        """
        Returns data with name equal to data_label of type cls with subsets applied from
        subset_to_apply.

        Parameters
        ----------
        data_label : str, optional
            Provide a label to retrieve a specific data set from data_collection.
        cls : light curve class, optional
            The type that data will be returned as.
        subset_to_apply : str, optional
            Subset that is to be applied to data before it is returned.

        Returns
        -------
        data : cls
            Data is returned as type cls with subsets applied.
        """
        return super()._get_data(data_label=data_label, cls=cls, subset_to_apply=subset_to_apply)
