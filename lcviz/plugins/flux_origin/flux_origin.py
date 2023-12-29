from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin,
                                        DatasetSelectMixin)
from jdaviz.core.user_api import PluginUserApi

from lcviz.components import FluxOriginSelectMixin

__all__ = ['FluxOrigin']


@tray_registry('flux-origin', label="Flux Origin")
class FluxOrigin(PluginTemplateMixin, FluxOriginSelectMixin, DatasetSelectMixin):
    """
    See the :ref:`Flux Origin Plugin Documentation <flux-origin>` for more details.

    Only the following attributes and methods are available through the
    public plugin API.

    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to bin.
    """
    template_file = __file__, "flux_origin.vue"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def user_api(self):
        expose = ['dataset', 'flux_origin']
        return PluginUserApi(self, expose=expose)
