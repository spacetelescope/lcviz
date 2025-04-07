import os
import numpy as np
from lightkurve import KeplerTargetPixelFile, TessTargetPixelFile

from jdaviz.core.events import SnackbarMessage
from jdaviz.core.registries import loader_importer_registry
from jdaviz.core.loaders.importers import BaseImporterToDataCollection

from lcviz.viewers import TimeScatterView, PhaseScatterView


__all__ = ['TPFImporter']


@loader_importer_registry('TPF')
class TPFImporter(BaseImporterToDataCollection):
    template_file = __file__, "../to_dc_with_label.vue"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_valid:
            self.data_label_default = f"{self.input.meta.get('OBJECT', 'Light curve')} [TPF]"

    @property
    def is_valid(self):
        if self.app.config not in ('deconfigged', 'lcviz'):
            # cubeviz allowed for cubeviz.specviz.load_data support
            # NOTE: temporary during deconfig process
            return False
        return isinstance(self.input, (KeplerTargetPixelFile, TessTargetPixelFile))

    @property
    def default_viewer_label(self):
        return 'image'

    @property
    def ignore_viewers_with_cls(self):
        # time viewers do support manually loading TPF data, but we do not want to
        # load automatically and instead default to creating and loading into
        # an image viewer
        return (TimeScatterView, PhaseScatterView)

    @property
    def default_viewer_reference(self):
        # returns the registry name of the default viewer
        # only used if `show_in_viewer=True` and no existing viewers can accept the data
        return 'lcviz-cube-viewer'

    @property
    def output(self):
        return self.input


