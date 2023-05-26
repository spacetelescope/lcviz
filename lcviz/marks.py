from jdaviz.core.marks import PluginLine, PluginScatter

__all__ = ['LivePreviewTrend', 'LivePreviewFlattened']


class LivePreviewTrend(PluginLine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LivePreviewFlattened(PluginScatter):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default_size', 16)
        super().__init__(*args, **kwargs)
