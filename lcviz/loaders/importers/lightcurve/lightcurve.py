import os
import numpy as np
from functools import cached_property
from traitlets import Any, Bool, List, Unicode, observe
from astropy.io import fits
from astropy.table import Table
from lightkurve import LightCurve

from glue_jupyter.common.toolbar_vuetify import read_icon

from jdaviz.core.tools import ICON_DIR
from jdaviz.core.registries import loader_importer_registry
from jdaviz.core.loaders.importers import BaseImporterToDataCollection
from jdaviz.core.template_mixin import SelectFileExtensionComponent
from jdaviz.core.user_api import ImporterUserApi


__all__ = ['LightCurveImporter']


def hdu_is_valid(hdu):
    """
    Check if the HDU is a valid light curve HDU.

    Parameters
    ----------
    hdu : `astropy.io.fits.hdu.base.HDUBase`
        The HDU to check.

    Returns
    -------
    bool
        True if the HDU is a valid light curve HDU, False otherwise.
    """
    return (isinstance(hdu, fits.hdu.table.BinTableHDU) and
            'TIME' in hdu.columns.names and
            'LC_INIT' in hdu.columns.names and
            'LC_INIT_ERR' in hdu.columns.names and
            'TUNIT1' in hdu.header)

def hdulist_to_lightcurve(pri_header, hdu):
    data = Table(hdu.data)
    # don't load some columns with names that may
    # conflict with components generated later by lcviz
    for col in ('PHASE', 'CADENCENO'):
        if col in data.columns:
            data.remove_column(col)
    # Remove rows that have NaN data
    data = data[~np.isnan(data['LC_INIT'])]
    time_offset = int(hdu.header['TUNIT1'].split('- ')[1].split(',')[0])
    data['TIME'] += time_offset
    lc = LightCurve(data=data,
                    time=data['TIME'],
                    flux=data['LC_INIT'],
                    flux_err=data['LC_INIT_ERR'])
    lc.meta = dict(pri_header)
    lc.meta = lc.meta | dict(hdu.header)
    lc.meta['MISSION'] = 'TESS DVT'
    lc.meta['FLUX_ORIGIN'] = "LC_INIT"
    lc.meta['EXTNAME'] = hdu.header['EXTNAME']

    return lc

def has_ephem(lc):
    return ('TPERIOD' in lc.meta and
            'TEPOCH' in lc.meta and
            'TUNIT1' in lc.meta)


@loader_importer_registry('Light Curve')
class LightCurveImporter(BaseImporterToDataCollection):
    template_file = __file__, "./lightcurve.vue"

    create_ephemeris_available = Bool(False).tag(sync=True)
    create_ephemeris = Bool(True).tag(sync=True)

    # HDUList-specific options
    input_hdulist = Bool(False).tag(sync=True)
    extension_items = List().tag(sync=True)
    extension_selected = Any().tag(sync=True)
    extension_multiselect = Bool(True).tag(sync=True)

    icon_radialtocheck = Unicode(read_icon(os.path.join(ICON_DIR, 'radialtocheck.svg'), 'svg+xml')).tag(sync=True)  # noqa
    icon_checktoradial = Unicode(read_icon(os.path.join(ICON_DIR, 'checktoradial.svg'), 'svg+xml')).tag(sync=True)  # noqa

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_valid:
            return

        self.input_hdulist = isinstance(self.input, fits.HDUList)
        if self.input_hdulist:
            # TODO: allow multiselect and select_all by default,
            # update __call__ logic below to loop and add each independently including ephemerides,
            # modify default data_label logic to inject data_label within loop (and inform user)
            self.extension = SelectFileExtensionComponent(self,
                                                          items='extension_items',
                                                          selected='extension_selected',
                                                          multiselect='extension_multiselect',
                                                          manual_options=self.input,
                                                          filters=[hdu_is_valid])
            self.extension.select_all()
            # NOTE: data_label_default handled by changes to extension_selected
        else:
            self.data_label_default = self.input.meta.get('OBJECT', 'Light curve')

    @property
    def user_api(self):
        expose = ['create_ephemeris']
        if isinstance(self.input, fits.HDUList):
            expose += ['extension']
        return ImporterUserApi(self, expose)

    @property
    def is_valid(self):
        if self.app.config not in ('deconfigged', 'lcviz'):
            # NOTE: temporary during deconfig process
            return False
        return (isinstance(self.input, LightCurve) or
                (isinstance(self.input, fits.HDUList)
                 and len([hdu for hdu in self.input if hdu_is_valid(hdu)])))  # noqa

    @observe('extension_selected')
    def _extension_selected_changed(self, event={}):
        if not hasattr(self, 'extension') or not self.input_hdulist:
            return

        self._clear_cache('output')

        if self.extension_multiselect:
            self.data_label_default = self.input[0].header.get('OBJECT', 'Light curve')
            self.create_ephemeris_available = any([has_ephem(lc) for lc in self.output])
        else:
            self.data_label_default = f"{self.input[0].header.get('OBJECT', 'Light curve')} [{self.extension.selected_item['name']}]"  # noqa
            self.create_ephemeris_available = has_ephem(self.output)

    @property
    def default_viewer_label(self):
        return 'flux-vs-time'

    @property
    def default_viewer_reference(self):
        # returns the registry name of the default viewer
        # only used if `show_in_viewer=True` and no existing viewers can accept the data
        return 'lcviz-time-viewer'

    @cached_property
    def output(self):
        if isinstance(self.input, LightCurve):
            return self.input

        pri_header = self.input[0].header
        if self.extension_multiselect:
            return [hdulist_to_lightcurve(pri_header, hdu) for hdu in self.extension.selected_hdu]
        return hdulist_to_lightcurve(pri_header, self.extension.selected_hdu)

    def __call__(self):
        if self.extension_multiselect:
            data_label = self.data_label_value
            lcs = self.output
            with self.app._jdaviz_helper.batch_load():
                for lc, ext in zip(lcs, self.extension.selected_name):
                    self.add_to_data_collection(lc, f"{data_label} [{ext}]", show_in_viewer=True)
        else:
            super().__call__()
            lcs = [self.output]

        if self.create_ephemeris_available and self.create_ephemeris \
                and 'Ephemeris' in self.app._jdaviz_helper.plugins:
            for lc, ext in zip(lcs, self.extension.selected_name):
                if not has_ephem(lc):
                    continue
                time_offset = int(lc.meta.get('TUNIT1').split('- ')[1].split(',')[0])
                period = lc.meta.get('TPERIOD', 1.0)
                t0 = lc.meta.get('TEPOCH', None) + time_offset - self.app.data_collection[0].coords.reference_time.jd  # noqa

                ephem = self.app._jdaviz_helper.plugins['Ephemeris']
                ephem.add_component(ext, set_as_selected=False)
                ephem.update_ephemeris(ext, t0=t0, period=period, wrap_at=0.5)
                ephem.create_phase_viewer(ext)
