from jdaviz.core.helpers import ConfigHelper

__all__ = ['LCviz']


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
        'tray': ['g-metadata-viewer', 'g-plot-options', 'HelloWorldPlugin'],
        'viewer_area': [{'container': 'col',
                         'children': [{'container': 'row',
                                       'viewers': [{'name': 'time-viewer',
                                                    'plot': 'lcviz-time-viewer',
                                                    'reference': 'time-viewer'}]}]}]}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._default_time_viewer_reference_name = 'time-viewer'

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
