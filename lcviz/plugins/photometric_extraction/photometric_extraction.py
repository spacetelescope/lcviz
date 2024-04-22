from traitlets import Bool, observe

from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import (PluginTemplateMixin,
                                        DatasetSelectMixin, AddResultsMixin,
                                        skip_if_no_updates_since_last_active,
                                        with_spinner, with_temp_disable)
from jdaviz.core.user_api import PluginUserApi


__all__ = ['PhotometricExtraction']


@tray_registry('photometric-extraction', label="Photometric Extraction")
class PhotometricExtraction(PluginTemplateMixin, DatasetSelectMixin,
                            AddResultsMixin):
    """
    See the :ref:`Photometric Extraction Plugin Documentation <photometric-extraction>`
    for more details.

    Only the following attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to bin.
    * ``add_results`` (:class:`~jdaviz.core.template_mixin.AddResults`)
    * :meth:`extract`
    """
    template_file = __file__, "photometric_extraction.vue"
    uses_active_status = Bool(True).tag(sync=True)

    show_live_preview = Bool(True).tag(sync=True)

    apply_enabled = Bool(True).tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        def is_tpf(data):
            return len(data.shape) == 3
        self.dataset.add_filter(is_tpf)

    @property
    def user_api(self):
        expose = ['show_live_preview', 'dataset',
                  'add_results', 'extract']
        return PluginUserApi(self, expose=expose)

    @property
    def marks(self):
        marks = {}
        return marks

    @with_spinner()
    def extract(self, add_data=True):
        raise NotImplementedError

    def vue_apply(self, event={}):
        self.extract(add_data=True)
