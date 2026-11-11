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
            data['astroModel'] = np.where(np.isfinite(arrays['rawFluxErr'][:, ::-1]),
                                          0.99, np.nan)
            data['astroModel'].attrs['units'] = np.bytes_('None (normalized)')
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
    assert data.label == 'GJ 3929 b [Light curve]'
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


@pytest.mark.parametrize('nvisits', [1, 2])
def test_hdf5_model_conversion(rocky_worlds_file, nvisits):
    path = rocky_worlds_file(nvisits)
    with h5py.File(path, 'r+') as data:
        data['astroModel'][0, -1] = np.nan
        lc = hdf5_to_lightcurve(data, model='astroModel')
    assert len(lc) == 4 * nvisits - 1
    np.testing.assert_array_equal(lc.time.jd, 2459000 + np.arange(1, 4 * nvisits))
    np.testing.assert_allclose(lc.flux.value, 0.99)
    assert lc.flux.unit == u.dimensionless_unscaled
    assert lc.time.scale == 'tdb'
    assert np.all(np.isnan(lc.flux_err.value))
    assert set(lc.colnames) == {'time', 'flux', 'flux_err', 'astroModel'}
    assert lc.meta['FLUX_ORIGIN'] == 'astroModel'
    assert lc.meta['EXTNAME'] == 'astroModel'


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
@pytest.mark.parametrize('nvisits', [1, 2])
def test_hdf5_model_extensions(rocky_worlds_file, helper_name, nvisits, request):
    helper = request.getfixturevalue(helper_name)
    path = rocky_worlds_file(nvisits)
    with h5py.File(path, 'r+') as data:
        data['fullModel'] = data['astroModel'][:] * 1.01
        data['fullModel'].attrs['units'] = np.bytes_('None (normalized)')
        data['noiseModel'] = data['astroModel'][:] * 1.02
        data['noiseModel'].attrs['units'] = np.bytes_('None (normalized)')

    loader = helper.loaders['file']
    loader.filepath = str(path)
    loader.format = 'Light Curve'
    importer = loader.importer
    assert importer.extension.choices == ['Light curve', 'astroModel', 'fullModel', 'noiseModel']
    assert importer.extension.selected == ['Light curve']
    assert importer.extension.multiselect
    assert importer._obj.data_label_is_prefix
    assert importer._obj.data_label_suffices == [' [Light curve]']
    assert importer.data_label.value == 'GJ 3929 b'
    assert [lc.meta['FLUX_ORIGIN'] for lc in importer._obj.output] == ['rawFlux']
    hashes = importer._obj.data_hashes
    assert len(hashes) == 4
    assert len(set(hashes)) == 4
    assert all(hashes)

    importer.extension.multiselect = False
    assert not importer._obj.data_label_is_prefix
    assert importer._obj.data_label_suffices == []
    importer.extension = 'astroModel'
    assert importer.data_label.value == 'GJ 3929 b [astroModel]'
    assert importer._obj.output.meta['FLUX_ORIGIN'] == 'astroModel'
    importer.extension = 'fullModel'
    assert importer._obj.output.meta['FLUX_ORIGIN'] == 'fullModel'
    importer.extension.multiselect = True
    importer.extension = ['Light curve', 'astroModel', 'fullModel']
    assert importer.data_label.value == 'GJ 3929 b'
    importer.data_label = 'Custom prefix'
    assert importer._obj.data_label_is_prefix
    assert importer._obj.data_label_suffices == [' [Light curve]', ' [astroModel]', ' [fullModel]']
    assert importer._obj.data_label_overwrite_by_index == [False, False, False]
    loader.load()

    dc = helper._app.data_collection
    assert dc.labels == ['Custom prefix [Light curve]', 'Custom prefix [astroModel]',
                         'Custom prefix [fullModel]']
    for data, origin in zip(dc, ['rawFlux', 'astroModel', 'fullModel']):
        assert data.shape == (4 * nvisits,)
        assert data.meta['FLUX_ORIGIN'] == origin
        assert data.meta['_data_hash'] in hashes
        assert 'centroid_x' not in {cid.label for cid in data.components}
    np.testing.assert_allclose(dc[1]['flux'], 0.99)
    np.testing.assert_allclose(dc[2]['flux'], 0.9999)
    importer._obj.reset_and_check_existing_data_in_dc()
    assert len(importer._obj.existing_data_in_dc) == 3
    importer._obj._on_label_changed()
    assert importer._obj.data_label_overwrite_by_index == [True, True, True]
    assert importer._obj.data_label_overwrite
    importer.extension = ['Light curve', 'noiseModel']
    assert importer._obj.data_label_suffices == [' [Light curve]', ' [noiseModel]']
    assert importer._obj.data_label_overwrite_by_index == [True, False]
    importer.extension.multiselect = False
    assert not importer._obj.data_label_is_prefix
    assert importer._obj.data_label_suffices == []
    assert isinstance(importer._obj.output, LightCurve)
    importer.extension = 'noiseModel'
    assert importer._obj.output.meta['FLUX_ORIGIN'] == 'noiseModel'


def test_hdf5_single_model_loading(rocky_worlds_file, deconfigged_helper):
    loader = deconfigged_helper.loaders['file']
    loader.filepath = str(rocky_worlds_file())
    loader.format = 'Light Curve'
    loader.importer.extension = 'astroModel'
    loader.load()
    dc = deconfigged_helper._app.data_collection
    assert dc.labels == ['GJ 3929 b [astroModel]']
    np.testing.assert_allclose(dc[0]['flux'], 0.99)
    assert deconfigged_helper.plugins['Flux Column'].flux_column.choices == ['astroModel']


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_hdf5_load_multiple_extensions(rocky_worlds_file, helper_name, request):
    helper = request.getfixturevalue(helper_name)
    helper.load(str(rocky_worlds_file()), format='Light Curve',
                extension=['Light curve', 'astroModel'], data_label='Custom')

    dc = helper._app.data_collection
    assert dc.labels == ['Custom [Light curve]', 'Custom [astroModel]']
    assert [data.meta['FLUX_ORIGIN'] for data in dc] == ['rawFlux', 'astroModel']
    np.testing.assert_allclose(dc[0]['flux'], [1, np.nan, 1.02, 1.03])
    np.testing.assert_allclose(dc[1]['flux'], 0.99)


@pytest.mark.parametrize('extension', ['astroModel', ['astroModel']])
def test_hdf5_load_single_extension(rocky_worlds_file, deconfigged_helper, extension):
    deconfigged_helper.load(str(rocky_worlds_file()), format='Light Curve',
                            extension=extension)
    dc = deconfigged_helper._app.data_collection
    assert dc.labels == ['GJ 3929 b [astroModel]']
    assert dc[0].meta['FLUX_ORIGIN'] == 'astroModel'
    np.testing.assert_allclose(dc[0]['flux'], 0.99)


def test_hdf5_without_models(rocky_worlds_file, deconfigged_helper):
    path = rocky_worlds_file()
    with h5py.File(path, 'r+') as data:
        del data['astroModel']
    loader = deconfigged_helper.loaders['file']
    loader.filepath = str(path)
    loader.format = 'Light Curve'
    assert not loader.importer._obj.input_has_extensions
    assert not hasattr(loader.importer, 'extension')
    loader.load()
    assert deconfigged_helper._app.data_collection.labels == ['GJ 3929 b']


def test_hdf5_model_names(rocky_worlds_file, deconfigged_helper):
    path = rocky_worlds_file()
    with h5py.File(path, 'r+') as data:
        data.move('astroModel', 'fluxMODEL')
        lc = hdf5_to_lightcurve(data)
        assert 'fluxMODEL' not in lc.colnames
    loader = deconfigged_helper.loaders['file']
    loader.filepath = str(path)
    loader.format = 'Light Curve'
    assert loader.importer.extension.choices == ['Light curve', 'fluxMODEL']
    loader.importer.extension = 'fluxMODEL'
    loader.load()
    np.testing.assert_allclose(deconfigged_helper._app.data_collection[0]['flux'], 0.99)
