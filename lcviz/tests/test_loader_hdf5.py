from types import SimpleNamespace

import h5py
import numpy as np
import pytest
from astropy import units as u
from lightkurve import LightCurve

from lcviz.loaders.importers.lightcurve.lightcurve import hdf5_to_lightcurve
from lcviz.loaders.parsers.hdf5 import HDF5Parser


@pytest.fixture
def rocky_worlds_file(tmp_path):
    def create(nvisits=1):
        path = tmp_path / 'rocky_worlds_lc.h5'
        size = 4 * nvisits
        arrays = {name: np.full((nvisits, size), np.nan)
                  for name in ('rawFlux', 'rawFluxErr', 'cleanedFlux', 'otherFlux')}
        for visit in range(nvisits):
            section = slice(4 * visit, 4 * visit + 4)
            arrays['rawFlux'][visit, section] = [1, np.nan, 1.02, 1.03]
            arrays['rawFluxErr'][visit, section] = 0.01
            arrays['cleanedFlux'][visit, section] = [np.nan, np.nan, 1.002, 1.003]
            arrays['otherFlux'][visit, section] = [1.1, np.nan, 1.12, 1.13]
        with h5py.File(path, 'w') as data:
            data.attrs['HLSPID'] = np.bytes_('Rocky-Worlds')
            data.attrs['HLSPTARG'] = np.bytes_('GJ 3929 b')
            data.attrs['TELESCOP'] = np.bytes_('JWST')
            data.attrs['NOTES'] = np.array([b'First note', b'Second note'])
            data.attrs['_NCProperties'] = np.bytes_('internal metadata')
            data['time'] = (2459000.0 + np.arange(size))[::-1]
            data['time'].attrs['units'] = np.bytes_('BJD_TDB')
            data['visit'] = np.arange(1, nvisits + 1)
            for name, array in arrays.items():
                data[name] = array[:, ::-1]
                data[name].attrs['units'] = np.bytes_('None (normalized)')
            data['astroModel'] = np.ones((nvisits, size))
            data['centroid_x'] = np.ones((nvisits, size))
            data['PIPELINE'] = np.array([b'eureka'] * nvisits)
        return path
    return create


@pytest.mark.parametrize('nvisits', [1, 2])
def test_hdf5_conversion(rocky_worlds_file, nvisits):
    with h5py.File(rocky_worlds_file(nvisits), 'r') as data:
        lc = hdf5_to_lightcurve(data)

    assert isinstance(lc, LightCurve)
    assert len(lc) == 4 * nvisits
    np.testing.assert_array_equal(lc.time.jd, 2459000 + np.arange(4 * nvisits))
    assert lc.time.scale == 'tdb'
    assert lc.flux.unit == u.dimensionless_unscaled
    np.testing.assert_allclose(lc.flux.value, np.tile([1, np.nan, 1.02, 1.03], nvisits))
    np.testing.assert_allclose(lc.flux_err.value, 0.01)
    np.testing.assert_allclose(
        lc['cleanedFlux'].value, np.tile([np.nan, np.nan, 1.002, 1.003], nvisits))
    assert set(lc.colnames) == {
        'time', 'flux', 'flux_err', 'rawFlux', 'rawFlux_err', 'cleanedFlux', 'otherFlux'}
    assert lc.meta['OBJECT'] == 'GJ 3929 b'
    assert lc.meta['TELESCOP'] == 'JWST'
    assert lc.meta['NOTES'] == ['First note', 'Second note']
    assert lc.meta['FLUX_ORIGIN'] == 'rawFlux'
    assert '_NCProperties' not in lc.meta


def test_hdf5_supplied_cleaned_uncertainties(rocky_worlds_file):
    path = rocky_worlds_file()
    with h5py.File(path, 'r+') as data:
        data['cleanedFluxErr'] = np.full((1, 4), 0.002)
        data['cleanedFluxErr'].attrs['units'] = np.bytes_('None (normalized)')
        lc = hdf5_to_lightcurve(data)
    np.testing.assert_allclose(lc['cleanedFlux_err'].value, 0.002)
    assert 'cleanedFluxErr' not in lc.colnames


def test_hdf5_overlapping_visits(rocky_worlds_file):
    path = rocky_worlds_file(2)
    with h5py.File(path, 'r+') as data:
        data['rawFlux'][1, -1] = 2
        data['rawFluxErr'][1, -1] = 0.02
        lc = hdf5_to_lightcurve(data)
    np.testing.assert_array_equal(lc.time.jd, 2459000 + np.array([0, 0, 1, 2, 3, 4, 5, 6, 7]))
    np.testing.assert_allclose(lc.flux[:2].value, [1, 2])
    np.testing.assert_allclose(lc.flux_err[:2].value, [0.01, 0.02])


@pytest.mark.parametrize('invalid, message', [
    ('schema', 'Rocky-Worlds schema'),
    ('missing', "missing dataset 'rawFluxErr'"),
    ('units', 'time units must be BJD_TDB'),
    ('time', 'finite 1D array'),
    ('shape', 'numeric array of shape'),
    ('empty', 'no finite fluxes or uncertainties'),
    ('duplicate', 'Duplicate flux column'),
])
def test_hdf5_invalid_schema(rocky_worlds_file, invalid, message):
    path = rocky_worlds_file()
    with h5py.File(path, 'r+') as data:
        if invalid == 'schema':
            data.attrs['HLSPID'] = 'another product'
        elif invalid == 'missing':
            del data['rawFluxErr']
        elif invalid == 'units':
            data['time'].attrs['units'] = 'MJD'
        elif invalid == 'time':
            data['time'][0] = np.nan
        elif invalid == 'shape':
            del data['rawFlux']
            data['rawFlux'] = np.ones((2, 4))
        elif invalid == 'empty':
            for name in ('rawFlux', 'rawFluxErr', 'cleanedFlux', 'otherFlux'):
                data[name][:] = np.nan
        elif invalid == 'duplicate':
            data['rawFlux_err'] = np.ones((1, 4))
        with pytest.raises(ValueError, match=message):
            hdf5_to_lightcurve(data)


def test_hdf5_parser_cleanup(rocky_worlds_file):
    parser = HDF5Parser(SimpleNamespace(config='deconfigged'), str(rocky_worlds_file()))
    assert parser.is_valid
    handle = parser.output
    assert handle.mode == 'r'
    parser._cleanup()
    assert not handle.id.valid
    assert 'output' not in parser.__dict__
    parser._cleanup()


def test_hdf5_parser_invalid_file(tmp_path):
    path = tmp_path / 'not_hdf5.h5'
    path.write_text('Not an HDF5 file')
    parser = HDF5Parser(SimpleNamespace(config='deconfigged'), str(path))
    assert not parser.is_valid
    parser._cleanup()


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
@pytest.mark.parametrize('nvisits', [1, 2])
def test_hdf5_file_loader(rocky_worlds_file, helper_name, nvisits, request):
    helper = request.getfixturevalue(helper_name)
    helper.load(str(rocky_worlds_file(nvisits)), format='Light Curve')
    assert len(helper._app.data_collection) == 1
    data = helper._app.data_collection[0]
    assert data.label == 'GJ 3929 b'
    assert data.shape == (4 * nvisits,)
    assert data.meta['FLUX_ORIGIN'] == 'rawFlux'
    assert not {'astroModel', 'centroid_x', 'PIPELINE'} & {cid.label for cid in data.components}

    plugin = helper.plugins['Flux Column']
    assert set(plugin.flux_column.choices) == {'rawFlux', 'cleanedFlux', 'otherFlux'}
    plugin.flux_column = 'cleanedFlux'
    np.testing.assert_allclose(data['flux'], data['cleanedFlux'])
    assert 'flux_err' not in {cid.label for cid in data.component_ids()}
    plugin.flux_column = 'rawFlux'
    np.testing.assert_allclose(data['flux'], data['rawFlux'])
    np.testing.assert_allclose(data['flux_err'], 0.01)


def test_hdf5_invalid_not_offered(rocky_worlds_file, deconfigged_helper):
    path = rocky_worlds_file()
    with h5py.File(path, 'r+') as data:
        del data['rawFluxErr']
    loader = deconfigged_helper.loaders['file']
    loader.filepath = str(path)
    assert 'Light Curve' not in loader.format.choices
