import numpy as np

from jdaviz.configs.default.plugins import Markers
from jdaviz.core.registries import tray_registry

__all__ = ['Markers']


@tray_registry('lcviz-markers', label="Markers")
class Markers(Markers):
    """
    See the :ref:`Markers Plugin Documentation <markers>` for more details.

    Only the following attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    * :meth:`clear_table`
    * :meth:`~jdaviz.core.template_mixin.TableMixin.export_table`
    """
    _default_table_values = {'time': np.nan,
                             'time:unit': '',
                             'phase': np.nan,
                             'ephemeris': '',
                             'pixel': (np.nan, np.nan),
                             'value': np.nan,
                             'value:unit': ''}

    def __init__(self, *args, **kwargs):
        kwargs['headers'] = ['time', 'time:unit', 'phase', 'ephemeris',
                             'pixel', 'value', 'value:unit', 'viewer']
        super().__init__(*args, **kwargs)
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#markers"

    @property
    def coords_info(self):
        return self.app.session.application._tools['lcviz-coords-info']
