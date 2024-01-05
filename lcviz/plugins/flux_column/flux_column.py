from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin,
                                        DatasetSelectMixin)
from jdaviz.core.user_api import PluginUserApi

from lcviz.components import FluxColumnSelectMixin

__all__ = ['FluxColumn']


@tray_registry('flux-column', label="Flux Column")
class FluxColumn(PluginTemplateMixin, FluxColumnSelectMixin, DatasetSelectMixin):
    """
    See the :ref:`Flux Column Plugin Documentation <flux-column>` for more details.

    Only the following attributes and methods are available through the
    public plugin API.

    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to bin.
    * ``flux_column`` (:class:`~lcviz.components.FluxColumnSelect`)
    """
    template_file = __file__, "flux_column.vue"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def user_api(self):
        expose = ['dataset', 'flux_column']
        return PluginUserApi(self, expose=expose)
