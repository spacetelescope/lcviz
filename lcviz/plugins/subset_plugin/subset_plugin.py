from jdaviz.configs.default.plugins import SubsetPlugin
from jdaviz.core.registries import tray_registry

__all__ = ['SubsetPlugin']


@tray_registry('lcviz-subset-plugin', label="Subset Tools")
class SubsetPlugin(SubsetPlugin):
    """
    See the :ref:`Subset Plugin Documentation <subset-tools>` for more details.

    Only the following attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#subset-tools"
        self.can_freeze = True
