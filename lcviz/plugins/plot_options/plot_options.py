import numpy as np

from jdaviz.configs.default.plugins import PlotOptions
from jdaviz.core.registries import tray_registry

__all__ = ['PlotOptions']


@tray_registry('lcviz-plot-options', label="Plot Options")
class PlotOptions(PlotOptions):
    """
    See the :ref:`Plot Options Plugin Documentation <plot-options>` for more details.

    For a full list of exposed attributes, call ``dir(plugin)``.  Note that some attributes are
    applicable depending on the selection of ``viewer`` and/or ``layer``.  Below are
    a list of some common attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    * ``viewer`` (:class:`~jdaviz.core.template_mixin.ViewerSelect`):
    * ``viewer_multiselect``
    * ``layer`` (:class:`~jdaviz.core.template_mixin.LayerSelect`):
    * ``layer_multiselect``
    * :meth:`select_all`
    * ``subset_color`` (:class:`~jdaviz.core.template_mixin.PlotOptionsSyncState`):
    * ``line_color`` (:class:`~jdaviz.core.template_mixin.PlotOptionsSyncState`):
    * ``line_width`` (:class:`~jdaviz.core.template_mixin.PlotOptionsSyncState`):
    * ``line_opacity`` (:class:`~jdaviz.core.template_mixin.PlotOptionsSyncState`):
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#plot-options"

    def _default_tpf_stretch(
            self, vmin_percentile=5, vmax_percentile=99, tpf_viewer_reference='image'
    ):
        viewer = self.app.get_viewer(tpf_viewer_reference)
        image = viewer.layers[0].get_image_data()
        vmin, vmax = np.nanpercentile(
            image, [vmin_percentile, vmax_percentile]
        )

        self.viewer_selected = tpf_viewer_reference
        self.stretch_function_value = 'log'
        self.stretch_vmin_value = vmin
        self.stretch_vmax_value = vmax

    @property
    def user_api(self):
        api = super().user_api
        expose = [e for e in api._expose if e not in ('apply_RGB_presets', 'line_as_steps',
                  'uncertainty_visible')]

        expose += ['marker_visible', 'marker_fill', 'marker_opacity',
                   'marker_size_mode', 'marker_size', 'marker_size_scale',
                   'marker_size_col', 'marker_size_vmin', 'marker_size_vmax',
                   'marker_color_mode', 'marker_color', 'marker_color_col',
                   'marker_colormap', 'marker_colormap_vmin', 'marker_colormap_vmax',
                   'line_visible', 'line_width']
        api._expose = expose

        return api
