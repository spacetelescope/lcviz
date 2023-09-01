from jdaviz.configs.default.plugins import SubsetPlugin
from jdaviz.core.registries import tray_registry

__all__ = ['SubsetPlugin']


@tray_registry('lcviz-subset-plugin', label="Subset Tools")
class SubsetPlugin(SubsetPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#subset-tools"
