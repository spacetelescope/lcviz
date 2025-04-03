import os
import numpy as np
from lightkurve import LightCurve

from jdaviz.core.events import SnackbarMessage
from jdaviz.core.registries import loader_importer_registry
from jdaviz.core.loaders.importers import BaseImporterToDataCollection


__all__ = ['LightCurveImporter']


@loader_importer_registry('Light Curve')
class LightCurveImporter(BaseImporterToDataCollection):
    template_file = __file__, "../to_dc_with_label.vue"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_valid:
            self.data_label_default = os.path.splitext(os.path.basename(self.input.filename))[0]

    @property
    def is_valid(self):
        if self.app.config not in ('deconfigged', 'lcviz'):
            # cubeviz allowed for cubeviz.specviz.load_data support
            # NOTE: temporary during deconfig process
            return False
        return isinstance(self.input, LightCurve)

    @property
    def default_viewer_label(self):
        return 'flux-vs-time'

    @property
    def default_viewer_reference(self):
        # returns the registry name of the default viewer
        # only used if `show_in_viewer=True` and no existing viewers can accept the data
        return 'lcviz-time-viewer'

    @property
    def output(self):
        return self.input


