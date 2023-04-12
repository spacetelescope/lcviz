from jdaviz.core.helpers import ConfigHelper
from glue.core import Data


class LCviz(ConfigHelper):
    _default_configuration = {
        'settings': {'configuration': 'customviz',
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
                                       'viewers': [{'name': 'Time-viewer',
                                                    'plot': 'lcviz-time-viewer',
                                                    'reference': 'time-viewer'}]}]}]}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._default_time_viewer_reference_name = 'time-viewer'

    def load_data(self, flux, time, data_label):
        '''
        Loads two quantity arrays by constructing a glue data object

        Parameters
        ----------
        flux : astropy.units.Quantity
            An astropy quantity array designating the flux or profile axis
        time : astropy.units.Quantity
            An astropy quantity array designating the time axis
        data_label : str
            The Glue data label found in the ``DataCollection``.
        '''
        data_to_load = Data(x=time.value, flux=flux.value)
        data_to_load.get_component('x').units = str(time.unit)
        data_to_load.get_component('flux').units = str(flux.unit)
        super().load_data(data=data_to_load, parser_reference='lcviz_manual_data_parser',
                          data_label=data_label)
