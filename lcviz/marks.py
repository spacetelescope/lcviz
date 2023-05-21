from jdaviz.core.marks import PluginLine, PluginScatter

__all__ = ['LivePreviewTrend', 'LivePreviewDetrended']


class LivePreviewTrend(PluginLine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LivePreviewDetrended(PluginScatter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default_size', 16)
        super().__init__(*args, **kwargs)
