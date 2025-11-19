from lightkurve import KeplerTargetPixelFile, TessTargetPixelFile

from jdaviz.core.registries import loader_importer_registry
from jdaviz.core.loaders.importers import BaseImporterToDataCollection

from lcviz.viewers import TimeScatterView, PhaseScatterView


__all__ = ['TPFImporter']


@loader_importer_registry('TPF')
class TPFImporter(BaseImporterToDataCollection):
    template_file = __file__, "tpf.vue"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_valid:
            self.data_label_default = f"{self.input.meta.get('OBJECT', 'Light curve')} [TPF]"

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

    @property
    def output(self):
        return self.input
