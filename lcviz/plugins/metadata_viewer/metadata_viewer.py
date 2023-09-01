from jdaviz.configs.default.plugins import MetadataViewer
from jdaviz.core.registries import tray_registry

__all__ = ['MetadataViewer']


@tray_registry('lcviz-metadata-viewer', label="Metadata")
class MetadataViewer(MetadataViewer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#metadata-viewer"  # noqa
