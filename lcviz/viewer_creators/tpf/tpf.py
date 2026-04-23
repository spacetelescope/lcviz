from jdaviz.core.viewer_creators import BaseViewerCreator
from jdaviz.core.registries import viewer_creator_registry

from lcviz.utils import is_tpf
from lcviz.viewers import CubeView

__all__ = ['TPFViewerCreator']


@viewer_creator_registry('TPF', overwrite=False)
class TPFViewerCreator(BaseViewerCreator):
    template_file = __file__, "../base_viewer_creator.vue"

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        self.dataset.filters = [is_tpf]
        self.viewer_label_default = 'TPF'

    @property
    def viewer_class(self):
        return CubeView

    def _set_is_relevant(self):
        # Only relevant when TPF data is loaded
        self.is_relevant = len(self.dataset_items) > 0
