import numpy as np

from jdaviz.configs.default.plugins import Markers
from jdaviz.core.registries import tray_registry

__all__ = ['Markers']


@tray_registry('lcviz-markers', label="Markers")
class Markers(Markers):
    _default_table_values = {'time': np.nan,
                             'phase': np.nan,
                             'ephemeris': '',
                             'flux': np.nan}

    def __init__(self, *args, **kwargs):
        kwargs['headers'] = ['time', 'phase', 'ephemeris', 'flux', 'viewer']
        super().__init__(*args, **kwargs)
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#markers"

    @property
    def coords_info(self):
        return self.app.session.application._tools['lcviz-coords-info']
