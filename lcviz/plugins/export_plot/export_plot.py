from jdaviz.configs.default.plugins import ExportViewer
from jdaviz.core.registries import tray_registry

__all__ = ['ExportViewer']


@tray_registry('lcviz-export-plot', label="Export Plot")
class ExportViewer(ExportViewer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#export-plot"
