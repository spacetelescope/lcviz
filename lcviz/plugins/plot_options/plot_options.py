from jdaviz.configs.default.plugins import PlotOptions
from jdaviz.core.registries import tray_registry

__all__ = ['PlotOptions']


@tray_registry('lcviz-plot-options', label="Plot Options")
class PlotOptions(PlotOptions):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def user_api(self):
        api = super().user_api
        api._expose += ['marker_visible', 'marker_fill', 'marker_opacity',
                        'marker_size_mode', 'marker_size', 'marker_size_scale',
                        'marker_size_col', 'marker_size_vmin', 'marker_size_vmax',
                        'marker_color_mode', 'marker_color',
                        'marker_colormap', 'marker_colormap_vmin', 'marker_colormap_vmax']

        return api
