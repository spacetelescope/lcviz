from lightkurve import KeplerTargetPixelFile, TessTargetPixelFile
from traitlets import Any, Bool, List, Unicode, observe

from jdaviz.core.events import SnackbarMessage
from jdaviz.core.registries import loader_importer_registry, viewer_registry
from jdaviz.core.loaders.importers import BaseImporterToDataCollection
from jdaviz.core.template_mixin import (AutoTextField,
                                        ViewerSelectCreateNew)
from jdaviz.core.user_api import ImporterUserApi

from lcviz.viewers import TimeScatterView, PhaseScatterView


__all__ = ['TPFImporter']


@loader_importer_registry('TPF')
class TPFImporter(BaseImporterToDataCollection):
    template_file = __file__, "tpf.vue"

    auto_extract = Bool(True).tag(sync=True)

    # Extracted Data
    ext_data_label_value = Unicode().tag(sync=True)
    ext_data_label_default = Unicode().tag(sync=True)
    ext_data_label_auto = Bool(True).tag(sync=True)
    ext_data_label_invalid_msg = Unicode().tag(sync=True)

    # Extracted Viewer
    ext_viewer_create_new_items = List([]).tag(sync=True)
    ext_viewer_create_new_selected = Unicode().tag(sync=True)

    ext_viewer_items = List([]).tag(sync=True)
    ext_viewer_selected = Any([]).tag(sync=True)
    ext_viewer_multiselect = Bool(True).tag(sync=True)

    ext_viewer_label_value = Unicode().tag(sync=True)
    ext_viewer_label_default = Unicode().tag(sync=True)
    ext_viewer_label_auto = Bool(True).tag(sync=True)
    ext_viewer_label_invalid_msg = Unicode().tag(sync=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_valid:
            return

        def viewer_in_registry_names(supported_viewers):
            def viewer_filter(viewer):
                classes = [viewer_registry.members.get(item.get('reference')).get('cls')
                           for item in supported_viewers]
                return isinstance(viewer, tuple(classes))
            return viewer_filter

        self.data_label_default = f"{self.input.meta.get('OBJECT', 'Light curve')} [TPF]"

        self.ext_data_label = AutoTextField(self,
                                            'ext_data_label_value',
                                            'ext_data_label_default',
                                            'ext_data_label_auto',
                                            'ext_data_label_invalid_msg')

        self.ext_viewer = ViewerSelectCreateNew(self,
                                                'ext_viewer_items',
                                                'ext_viewer_selected',
                                                'ext_viewer_create_new_items',
                                                'ext_viewer_create_new_selected',
                                                'ext_viewer_label_value',
                                                'ext_viewer_label_default',
                                                'ext_viewer_label_auto',
                                                'ext_viewer_label_invalid_msg',
                                                multiselect='ext_viewer_multiselect',
                                                default_mode='empty')
        supported_viewers = [{'label': 'flux-vs-time',
                              'reference': 'lcviz-time-viewer'}]
        self.ext_viewer_create_new_items = supported_viewers

        self.ext_viewer.add_filter(viewer_in_registry_names(supported_viewers))
        self.ext_viewer.select_default()

    @property
    def user_api(self):
        expose = ['auto_extract', 'ext_data_label']
        return ImporterUserApi(self, expose)

    @property
    def is_valid(self):
        if self.app.config not in ('deconfigged', 'lcviz'):
            # NOTE: temporary during deconfig process
            return False
        return isinstance(self.input, (KeplerTargetPixelFile, TessTargetPixelFile))

    @staticmethod
    def _get_supported_viewers():
        return [{'label': 'image', 'reference': 'lcviz-cube-viewer'}]

    @property
    def ignore_viewers_with_cls(self):
        # time viewers do support manually loading TPF data, but we do not want to
        # load automatically and instead default to creating and loading into
        # an image viewer
        return (TimeScatterView, PhaseScatterView)

    @observe('data_label_value')
    def _data_label_changed(self, msg={}):
        self.ext_data_label_default = f"{self.data_label_value} (auto-extracted)"

    def __call__(self):
        # get a copy of all requested data-labels before additional data entries changes defaults
        data_label = self.data_label_value
        ext_data_label = self.ext_data_label_value

        super().__call__()

        if not self.auto_extract:
            return

        try:
            plg = self.app.get_tray_item_from_name('photometric-extraction')
            ext = plg._extract_in_new_instance(dataset=data_label,
                                               auto_update=False,
                                               add_data=False)
            # we'll add the data manually instead of through add_results_from_plugin
            # but still want to preserve the plugin metadata
            ext.meta['plugin'] = plg._plugin_name
        except Exception:
            ext = None
            msg = SnackbarMessage(
                "Automatic spectrum extraction failed. See the 3D spectral extraction"
                " plugin to perform a custom extraction",
                color='error', sender=self, timeout=10000)
        else:
            msg = SnackbarMessage(
                "The extracted 1D spectrum was generated automatically."
                " See the 3D spectral extraction plugin for details or to"
                " perform a custom extraction.",
                color='warning', sender=self, timeout=10000)
        self.app.hub.broadcast(msg)

        if ext is not None:
            self.add_to_data_collection(ext, ext_data_label, viewer_select=self.ext_viewer)
