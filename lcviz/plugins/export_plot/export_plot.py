from jdaviz.configs.default.plugins import ExportViewer
from jdaviz.core.registries import tray_registry

__all__ = ['ExportViewer']


@tray_registry('lcviz-export-plot', label="Export Plot")
class ExportViewer(ExportViewer):
    """
    See the :ref:`Export Plot Plugin Documentation <export-plot>` for more details.

    Only the following attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    * ``viewer`` (:class:`~jdaviz.core.template_mixin.ViewerSelect`):
      Viewer to select for exporting the figure image.
    * :meth:`save_figure`
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#export-plot"
