import os
import h5py
import numpy as np
from functools import cached_property
from traitlets import Any, Bool, List, Unicode, observe
from astropy.io import fits
from astropy import units as u
from astropy.table import Table
from astropy.time import Time
from lightkurve import LightCurve

from glue_jupyter.common.toolbar_vuetify import read_icon

from jdaviz.core.tools import ICON_DIR
from jdaviz.core.registries import loader_importer_registry
from jdaviz.core.loaders.importers import BaseImporterToDataCollection
from jdaviz.core.template_mixin import SelectFileExtensionComponent
from jdaviz.core.user_api import ImporterUserApi
from jdaviz.utils import create_data_hash
from lcviz.utils import _data_with_reftime


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
    if not isinstance(hdu, fits.hdu.table.BinTableHDU):
        return False
    if 'TIME' not in hdu.columns.names:
        return False
    # TESS DVT format
    if ('LC_INIT' in hdu.columns.names and
            'LC_INIT_ERR' in hdu.columns.names and
            'TUNIT1' in hdu.header):
        return True
    # Generic lightkurve FITS format
    if 'FLUX' in hdu.columns.names:
        return True
    return False


def hdulist_to_lightcurve(pri_header, hdu):
    if 'LC_INIT' in hdu.columns.names:
        # TESS DVT format
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
    else:
        # Generic lightkurve FITS format (TIME + FLUX columns)
        data = Table(hdu.data)
        for col in ('PHASE', 'CADENCENO'):
            if col in data.columns:
                data.remove_column(col)
        flux_err = data['FLUX_ERR'] if 'FLUX_ERR' in data.columns else None
        lc = LightCurve(data=data,
                        time=data['TIME'],
                        flux=data['FLUX'],
                        flux_err=flux_err)
        lc.meta = dict(pri_header)
        lc.meta = lc.meta | dict(hdu.header)

    return lc


def has_ephem(lc):
    return ('TPERIOD' in lc.meta and
            'TEPOCH' in lc.meta and
            'TUNIT1' in lc.meta)


def _decode_hdf5_metadata(value):
    if isinstance(value, bytes):
        return value.decode('utf-8')
    if isinstance(value, np.ndarray):
        return _decode_hdf5_metadata(value.tolist())
    if isinstance(value, list):
        return [_decode_hdf5_metadata(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def hdf5_to_lightcurve(data, model=None):
    """Combine the visits in a Rocky Worlds light curve into one time series."""
    if _decode_hdf5_metadata(data.attrs.get('HLSPID', '')) != 'Rocky-Worlds':
        raise ValueError('HDF5 light curves must use the Rocky-Worlds schema.')
    for name in ('time', 'visit', 'rawFlux', 'rawFluxErr'):
        if name not in data or not isinstance(data[name], h5py.Dataset):
            raise ValueError(f'Rocky-Worlds light curve is missing dataset {name!r}.')

    times = data['time'][:]
    visits = data['visit']
    if times.ndim != 1 or not times.size or not np.all(np.isfinite(times)):
        raise ValueError('Rocky-Worlds time must be a nonempty, finite 1D array.')
    if visits.ndim != 1 or not visits.size:
        raise ValueError('Rocky-Worlds visit must be a nonempty 1D array.')
    if _decode_hdf5_metadata(data['time'].attrs.get('units', '')) != 'BJD_TDB':
        raise ValueError('Rocky-Worlds time units must be BJD_TDB.')

    columns = {}
    shape = (visits.size, times.size)
    for name, dataset in data.items():
        if 'flux' not in name.lower() or name.lower().endswith('model') \
                or not isinstance(dataset, h5py.Dataset):
            continue
        if dataset.shape != shape or dataset.dtype.kind not in 'fiu':
            raise ValueError(f'Flux dataset {name!r} must be a numeric array of shape {shape}.')
        unit = _decode_hdf5_metadata(dataset.attrs.get('units', ''))
        unit = u.dimensionless_unscaled if unit == 'None (normalized)' else u.Unit(unit)
        column_name = name[:-3] + '_err' if name.endswith('Err') else name
        if column_name in columns:
            raise ValueError(f'Duplicate flux column {column_name!r}.')
        columns[column_name] = dataset[:].reshape(-1) * unit

    if model is not None:
        dataset = data[model]
        if not isinstance(dataset, h5py.Dataset) or dataset.shape != shape \
                or dataset.dtype.kind not in 'fiu':
            raise ValueError(f'Model dataset {model!r} must be a numeric array of shape {shape}.')
        unit = _decode_hdf5_metadata(dataset.attrs.get('units', ''))
        unit = u.dimensionless_unscaled if unit == 'None (normalized)' else u.Unit(unit)
        columns = {model: dataset[:].reshape(-1) * unit}

    # NetCDF outer alignment can pad visits with rows missing every selected column.
    present = np.any([np.isfinite(column.value) for column in columns.values()], axis=0)
    if not np.any(present):
        if model is not None:
            raise ValueError(f'Model dataset {model!r} contains no finite values.')
        raise ValueError('Rocky-Worlds light curve contains no finite fluxes or uncertainties.')
    time = np.tile(times, visits.size)[present]
    order = np.argsort(time, kind='stable')
    columns = {name: column[present][order] for name, column in columns.items()}
    meta = {name: _decode_hdf5_metadata(value) for name, value in data.attrs.items()
            if not name.startswith('_')}
    meta['OBJECT'] = meta.get('HLSPTARG') or meta.get('STAR') or 'Light curve'
    meta['FLUX_ORIGIN'] = model or 'rawFlux'
    if model is not None:
        meta['EXTNAME'] = model
    return LightCurve(time=Time(time[order], format='jd', scale='tdb'),
                      flux=columns[model or 'rawFlux'], flux_err=columns.get('rawFlux_err'),
                      data=columns, meta=meta)


@loader_importer_registry('Light Curve')
class LightCurveImporter(BaseImporterToDataCollection):
    template_file = __file__, "./lightcurve.vue"

    create_ephemeris_available = Bool(False).tag(sync=True)
    create_ephemeris = Bool(True).tag(sync=True)

    # File extension options
    input_has_extensions = Bool(False).tag(sync=True)
    extension_items = List().tag(sync=True)
    extension_selected = Any().tag(sync=True)
    extension_multiselect = Bool(True).tag(sync=True)

    icon_radialtocheck = Unicode(read_icon(os.path.join(ICON_DIR, 'radialtocheck.svg'), 'svg+xml')).tag(sync=True)  # noqa
    icon_checktoradial = Unicode(read_icon(os.path.join(ICON_DIR, 'checktoradial.svg'), 'svg+xml')).tag(sync=True)  # noqa

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_valid:
            return

        if isinstance(self.input, fits.HDUList):
            self.input_has_extensions = True
            pri_header = self.input[0].header
            # Build ext_options as a list of dicts (required by SelectFileExtensionComponent)
            ext_options = [{'label': f"{i}: [{hdu.name},{getattr(hdu, 'ver', 1)}]",
                            'name': hdu.name,
                            'ver': getattr(hdu, 'ver', 1),
                            'name_ver': f"{hdu.name},{getattr(hdu, 'ver', 1)}",
                            'index': i,
                            'data_hash': create_data_hash(
                                hdulist_to_lightcurve(pri_header, hdu)
                            ) if hdu_is_valid(hdu) else None,
                            'obj': hdu} for i, hdu in enumerate(self.input)]

            def _hdu_filter(item):
                hdu = item.get('obj')
                return hdu_is_valid(hdu)

            # TODO: allow multiselect and select_all by default,
            # update __call__ logic below to loop and add each independently including ephemerides,
            # modify default data_label logic to inject data_label within loop (and inform user)
            self.extension = SelectFileExtensionComponent(self,
                                                          items='extension_items',
                                                          selected='extension_selected',
                                                          multiselect='extension_multiselect',
                                                          manual_options=ext_options,
                                                          filters=[_hdu_filter])
            self.data_hashes = self.extension.data_hashes
            self.hash_map_to_label = dict(zip(self.extension.data_hashes,
                                              self.extension.labels))
            self.extension.select_all()
            # NOTE: data_label_default handled by changes to extension_selected
        elif isinstance(self.input, h5py.File):
            models = sorted(name for name in self.input if name.lower().endswith('model')
                            and isinstance(self.input[name], h5py.Dataset))
            self.data_label_default = self._hdf5_lightcurve.meta['OBJECT']
            if models:
                self.input_has_extensions = True
                self.extension_multiselect = False
                lightcurves = [('Light curve', self._hdf5_lightcurve)]
                lightcurves += [(name, hdf5_to_lightcurve(self.input, model=name))
                                for name in models]
                ext_options = [{'label': name, 'name': name, 'index': index,
                                'data_hash': create_data_hash(lc), 'obj': lc}
                               for index, (name, lc) in enumerate(lightcurves)]
                self.extension = SelectFileExtensionComponent(
                    self, items='extension_items', selected='extension_selected',
                    multiselect='extension_multiselect', manual_options=ext_options)
                self.data_hashes = self.extension.data_hashes
                self.hash_map_to_label = dict(zip(self.extension.data_hashes,
                                                  self.extension.labels))
                self.extension.selected = 'Light curve'
                self._clear_cache('output')
                self._extension_selected_changed()
        else:
            meta = self.input.meta
            if meta.get('QUARTER', None) is None:
                self.data_label_default = meta.get('OBJECT', 'Light curve')
            else:
                self.data_label_default = f"{meta.get('OBJECT', 'Light curve')} [Q{meta.get('QUARTER')}]"  # noqa

    @property
    def user_api(self):
        expose = ['create_ephemeris']
        if self.input_has_extensions:
            expose += ['extension']
        return ImporterUserApi(self, expose)

    def _check_is_valid(self):
        if self._app.config not in ('lcviz', 'deconfigged'):
            return f'Light Curve importer is not supported in {self._app.config}.'
        if isinstance(self.input, LightCurve):
            return ''
        if isinstance(self.input, h5py.File):
            self._hdf5_lightcurve
            return ''
        if isinstance(self.input, fits.HDUList):
            for hdu in self.input:
                if hdu_is_valid(hdu):
                    return ''
        return ('Input must be a LightCurve, a HDUList with a valid light curve extension, '
                'or a Rocky-Worlds HDF5 light curve.')

    @observe('extension_selected')
    def _extension_selected_changed(self, event={}):
        if not hasattr(self, 'extension'):
            return

        self._clear_cache('output')

        self.data_label_is_prefix = self.extension_multiselect
        self.data_label_suffices = (
            [f" [{name}]" for name in self.extension.selected_name]
            if self.data_label_is_prefix else [])

        if isinstance(self.input, h5py.File):
            obj_name = self._hdf5_lightcurve.meta['OBJECT']
            name = self.extension.selected_name
            self.data_label_default = (
                obj_name if self.extension_multiselect or name in ('Light curve', None)
                else f'{obj_name} [{name}]')
            return

        if self.extension_multiselect:
            self.data_label_default = self.input[0].header.get('OBJECT') or 'Light curve'
            self.create_ephemeris_available = any([has_ephem(lc) for lc in self.output])
        else:
            obj_name = self.input[0].header.get('OBJECT') or 'Light curve'
            self.data_label_default = f"{obj_name} [{self.extension.selected_item['name']}]"  # noqa
            self.create_ephemeris_available = has_ephem(self.output)

    @staticmethod
    def _get_supported_viewers():
        return [{'label': 'flux-vs-time', 'reference': 'lcviz-time-viewer'}]

    @cached_property
    def _hdf5_lightcurve(self):
        return hdf5_to_lightcurve(self.input)

    @cached_property
    def output(self):
        if isinstance(self.input, LightCurve):
            lc = self.input
        elif isinstance(self.input, h5py.File):
            lc = self.extension.selected_obj if hasattr(self, 'extension') \
                else self._hdf5_lightcurve
        else:
            # HDUList case
            pri_header = self.input[0].header
            if self.extension_multiselect:
                lc = [hdulist_to_lightcurve(pri_header, hdu) for hdu in self.extension.selected_obj]
            else:
                lc = hdulist_to_lightcurve(pri_header, self.extension.selected_obj)

        lcs = lc if isinstance(lc, list) else [lc]
        for single_lc in lcs:
            flux_origin = single_lc.meta.get('FLUX_ORIGIN', None)  # i.e. PDCSAP or SAP
            if flux_origin == 'flux' or (flux_origin is None and 'flux' in getattr(single_lc, 'columns', [])):  # noqa
                # then make a copy of this column so it won't be lost when changing with the
                # flux_column plugin
                single_lc['flux:orig'] = single_lc['flux']
                if 'flux_err' in single_lc.columns:
                    single_lc['flux:orig_err'] = single_lc['flux_err']
                single_lc.meta['FLUX_ORIGIN'] = 'flux:orig'

        return lc

    def add_to_data_collection(self, data, *args, **kwargs):
        lc_cls = data.__class__
        kwargs.setdefault('cls', lc_cls)
        if isinstance(self.input, h5py.File):
            kwargs.setdefault('data_hash', create_data_hash(data))
        data = _data_with_reftime(self.app, data)
        super().add_to_data_collection(data, *args, **kwargs)

    def __call__(self):
        if self.input_has_extensions and self.extension_multiselect:
            data_label = self.data_label_value
            lcs = self.output
            with self._app._jdaviz_helper.batch_load():
                for lc, ext in zip(lcs, self.extension.selected_name):
                    self.add_to_data_collection(lc, f"{data_label} [{ext}]")
        else:
            super().__call__()
            lcs = [self.output]

        if self.create_ephemeris_available and self.create_ephemeris \
                and 'Ephemeris' in self._app._jdaviz_helper.plugins:
            for lc, ext in zip(lcs, self.extension.selected_name):
                if not has_ephem(lc):
                    continue
                ephem = self._app._jdaviz_helper.plugins['Ephemeris']
                ephem_component = self._app.return_unique_name(ext, ephem.component.choices)

                time_offset = int(lc.meta.get('TUNIT1').split('- ')[1].split(',')[0])
                period = lc.meta.get('TPERIOD', 1.0)
                t0 = lc.meta.get('TEPOCH', None) + time_offset - ephem._obj.reference_time

                ephem.add_component(ephem_component, set_as_selected=False)
                ephem.update_ephemeris(ephem_component, t0=t0, period=period, wrap_at=0.5)
                ephem.create_phase_viewer(ephem_component)
