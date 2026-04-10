import numpy as np

from jdaviz.configs.default.plugins import PlotOptions
from jdaviz.utils import get_subset_type

__all__ = []


def _default_tpf_stretch(self, vmin_percentile=5, vmax_percentile=99,
                         tpf_viewer_reference='image'):
    """Set a sensible log stretch for the TPF image viewer."""
    viewer = self._app.get_viewer(tpf_viewer_reference)
    image = viewer.layers[0].get_image_data()
    vmin, vmax = np.nanpercentile(image, [vmin_percentile, vmax_percentile])

    self.viewer_selected = tpf_viewer_reference
    self.stretch_function_value = 'log'
    self.stretch_vmin_value = vmin
    self.stretch_vmax_value = vmax


def _lcviz_layer_filter_factory(plugin):
    """Layer filter factory: exclude spatial subsets in scatter viewers unless CubeView active."""
    from lcviz.viewers import CubeView

    def _filter(lyr):
        if np.any([isinstance(v, CubeView) for v in plugin.layer.viewer_objs]):
            return True
        return get_subset_type(lyr) != 'spatial'

    return _filter


# Inject lcviz-specific behavior into the upstream PlotOptions via the hook API.

PlotOptions.register_layer_filter(_lcviz_layer_filter_factory)

PlotOptions.register_user_api(
    expose=[
        'marker_visible', 'marker_fill', 'marker_opacity',
        'marker_size_mode', 'marker_size', 'marker_size_scale',
        'marker_size_col', 'marker_size_vmin', 'marker_size_vmax',
        'marker_color_mode', 'marker_color', 'marker_color_col',
        'marker_colormap', 'marker_colormap_vmin', 'marker_colormap_vmax',
        'line_visible', 'line_width',
    ],
    remove=['apply_RGB_presets', 'line_as_steps', 'uncertainty_visible'],
)

# Convenience method injected onto the plugin class for TPF stretch setup.
PlotOptions._default_tpf_stretch = _default_tpf_stretch

PlotOptions._docs_link_fmt = (
    'https://lcviz.readthedocs.io/en/{vdocs}/plugins.html#plot-options'
)
