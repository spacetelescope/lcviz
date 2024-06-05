from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin,
                                        DatasetSelectMixin)
from jdaviz.core.user_api import PluginUserApi

from lcviz.components import FluxColumnSelectMixin
from lcviz.utils import is_not_tpf

__all__ = ['FluxColumn']


@tray_registry('flux-column', label="Flux Column")
class FluxColumn(PluginTemplateMixin, FluxColumnSelectMixin, DatasetSelectMixin):
    """
    See the :ref:`Flux Column Plugin Documentation <flux-column>` for more details.

    Only the following attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to bin.
    * ``flux_column`` (:class:`~lcviz.components.FluxColumnSelect`)
    """
    template_file = __file__, "flux_column.vue"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # NOTE: may eventually want to add support for choosing the column for TPFs
        self.dataset.add_filter(is_not_tpf)

    @property
    def user_api(self):
        expose = ['dataset', 'flux_column']
        return PluginUserApi(self, expose=expose)
