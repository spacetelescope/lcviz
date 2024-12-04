from traitlets import observe

from jdaviz.configs.default.plugins import SubsetTools
from jdaviz.core.registries import tray_registry

__all__ = ['SubsetTools']


@tray_registry('lcviz-subset-tools', label="Subset Tools")
class SubsetTools(SubsetTools):
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
        self.can_freeze = True

        self._plugin_description = 'Tools for selecting and interacting with subsets.'

    @observe('vdocs')
    def _update_docs_link(self, *args):
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#subset-tools"  # noqa
