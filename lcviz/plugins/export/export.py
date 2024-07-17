from traitlets import observe

from jdaviz.configs.default.plugins import Export
from jdaviz.core.registries import tray_registry

__all__ = ['Export']


@tray_registry('lcviz-export', label="Export")
class Export(Export):
    """
    See the :ref:`Export Plot Plugin Documentation <export>` for more details.

    Only the following attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    * ``viewer`` (:class:`~jdaviz.core.template_mixin.ViewerSelect`)
    * ``viewer_format`` (:class:`~jdaviz.core.template_mixin.SelectPluginComponent`)
    * ``filename``
    * :meth:`export`
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @observe('vdocs')
    def _update_docs_link(self, *args):
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#export"
