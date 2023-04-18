import pytest
import numpy as np
from astropy.time import Time
from astropy.utils.data import download_file
from lightkurve import LightCurve
from lightkurve.io import kepler
from gwcs.wcs import WCS
import astropy.units as u


@pytest.mark.remote_data
def test_kepler_via_mast_local_file(helper):
    url = (
        'https://archive.stsci.edu/pub/kepler/'
        'lightcurves/0014/001429092/kplr001429092-2009166043257_llc.fits'
    )  # 188 KB

    path = download_file(url, cache=True, timeout=100)
    helper.load_data(path)

    data = helper.app.data_collection[0]
    flux_arr = data['flux']
    flux_unit = u.Unit(data.get_component('flux').units)
    flux = flux_arr * flux_unit

    assert isinstance(data.coords, WCS)
    assert isinstance(flux, u.Quantity)
    assert flux.unit.is_equivalent(u.electron / u.s)


@pytest.mark.remote_data
def test_kepler_via_mast_preparsed(helper):
    url = (
        'https://archive.stsci.edu/pub/kepler/'
        'lightcurves/0014/001429092/kplr001429092-2009166043257_llc.fits'
    )  # 188 KB

    light_curve = kepler.read_kepler_lightcurve(url)
    helper.load_data(light_curve)

    data = helper.app.data_collection[0]
    flux_arr = data['flux']
    flux_unit = u.Unit(data.get_component('flux').units)
    flux = flux_arr * flux_unit

    assert isinstance(data.coords, WCS)
    assert isinstance(flux, u.Quantity)
    assert flux.unit.is_equivalent(u.electron / u.s)


def test_synthetic_lc(helper):
    time = Time(np.linspace(2460050, 2460060), format='jd')
    flux = np.ones(len(time)) * u.electron / u.s
    flux_err = 0.1 * np.ones_like(flux)
    lc = LightCurve(time=time, flux=flux, flux_err=flux_err)
    helper.load_data(lc)

    data = helper.app.data_collection[0]
    flux_arr = data['flux']
    flux_unit = u.Unit(data.get_component('flux').units)
    flux = flux_arr * flux_unit

    assert isinstance(data.coords, WCS)
    assert isinstance(flux, u.Quantity)
    assert flux.unit.is_equivalent(u.electron / u.s)
