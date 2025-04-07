import os
import numpy as np
from functools import cached_property
from traitlets import Bool, List, Unicode, observe
from astropy.io import fits
from astropy.table import Table
from lightkurve import LightCurve

from jdaviz.core.events import SnackbarMessage
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
    return isinstance(hdu, fits.hdu.table.BinTableHDU) and \
           'TIME' in hdu.columns.names and \
           'LC_INIT' in hdu.columns.names and \
           'LC_INIT_ERR' in hdu.columns.names and \
           'TUNIT1' in hdu.header


@loader_importer_registry('Light Curve')
class LightCurveImporter(BaseImporterToDataCollection):
    template_file = __file__, "./lightcurve.vue"

    # HDUList-specific options
    input_hdulist = Bool(False).tag(sync=True)
    extension_items = List().tag(sync=True)
    extension_selected = Unicode().tag(sync=True)

    # TODO: fix upstream handling of extension index (store in dict instead of splitting on assumed :)
    # and consider allowing passing filter for hdu_is_valid and call update_items instead of passing manual_options?

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_valid:
            return

        self.input_hdulist = isinstance(self.input, fits.HDUList)
        if self.input_hdulist:
            extension_options = [f"{i}: {hdu.name}"
                                 for i, hdu in enumerate(self.input)
                                 if hdu_is_valid(hdu)]
            # TODO: allow multiselect and select_all by default, 
            # update __call__ logic below to loop and add each independently including ephemerides,
            # modify default data_label logic to inject data_label within loop (and inform user)
            self.extension = SelectFileExtensionComponent(self,
                                                          items='extension_items',
                                                          selected='extension_selected',
                                                          manual_options=extension_options)
            self._extension_selected_changed()
            # NOTE: data_label_default handled by changes to extension_selected
        else:
            self.data_label_default = self.input.meta.get('OBJECT', 'Light curve')

    @property
    def user_api(self):
        expose = []
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
        self.data_label_default = f"{self.input[0].header.get('OBJECT', 'Light curve')} [{self.extension.selected.split(': ')[1]}]"
        self._clear_cache('output')

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

        # HDUList
        hdulist = self.input
        hdu = hdulist[self.extension.selected_index]
        data = Table(hdu.data)
        # don't load some columns with names that may
        # conflict with components generated later by lcviz
        for col in ('PHASE', 'CADENCENO'):
            if col in data.columns:
                data.remove_column(col)
        # Remove rows that have NaN data
        data = data[~np.isnan(data['LC_INIT'])]
        header = hdu.header
        time_offset = int(header['TUNIT1'].split('- ')[1].split(',')[0])
        data['TIME'] += time_offset
        lc = LightCurve(data=data,
                        time=data['TIME'],
                        flux=data['LC_INIT'],
                        flux_err=data['LC_INIT_ERR'])
        lc.meta = dict(hdulist[0].header)
        lc.meta = lc.meta | dict(hdu.header)
        lc.meta['MISSION'] = 'TESS DVT'
        lc.meta['FLUX_ORIGIN'] = "LC_INIT"
        lc.meta['EXTNAME'] = header['EXTNAME']

        return lc

    def __call__(self):
        super().__call__()

        # after data is loaded, check if any ephemeris can be adopted into the ephemeris plugin
        if 'TPERIOD' in self.output.meta and 'TEPOCH' in self.output.meta and 'TUNIT1' in self.output.meta and 'Ephemeris' in self.app._jdaviz_helper.plugins:
            time_offset = int(self.output.meta.get('TUNIT1').split('- ')[1].split(',')[0])
            period = self.output.meta.get('TPERIOD', 1.0)
            t0 = self.output.meta.get('TEPOCH', None) + time_offset - self.app.data_collection[0].coords.reference_time.jd  # noqa

            ephem = self.app._jdaviz_helper.plugins['Ephemeris']
            ephem_component = self.extension.selected.split(': ')[1]
            ephem.add_component(ephem_component, set_as_selected=False)
            ephem.update_ephemeris(ephem_component, t0=t0, period=period, wrap_at=0.5)
            ephem.create_phase_viewer(ephem_component)




