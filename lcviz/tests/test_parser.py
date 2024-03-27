import pytest
import numpy as np
from glue.core.roi import XRangeROI, YRangeROI
from astropy.time import Time
from astropy.utils.data import download_file
from lightkurve import LightCurve, KeplerTargetPixelFile, search_targetpixelfile
from lightkurve.io import kepler
import astropy.units as u

from lcviz.utils import TimeCoordinates


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

    assert isinstance(data.coords, TimeCoordinates)
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

    assert isinstance(data.coords, TimeCoordinates)
    assert isinstance(flux, u.Quantity)
    assert flux.unit.is_equivalent(u.electron / u.s)


@pytest.mark.remote_data
def test_kepler_tpf_via_lightkurve(helper):
    tpf = search_targetpixelfile("KIC 001429092",
                                 mission="Kepler",
                                 cadence="long",
                                 quarter=10).download()
    helper.load_data(tpf)
    assert helper.get_data().shape == (4447, 4, 6)  # (time, x, y)
    assert helper.app.data_collection[0].get_object(cls=KeplerTargetPixelFile).shape == (4447, 4, 6)


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

    assert isinstance(data.coords, TimeCoordinates)
    assert isinstance(flux, u.Quantity)
    assert flux.unit.is_equivalent(u.electron / u.s)


def test_apply_xrangerois(helper, light_curve_like_kepler_quarter):
    lc = light_curve_like_kepler_quarter
    helper.load_data(lc)
    viewer = helper.default_time_viewer._obj
    subset_plugin = helper.plugins['Subset Tools']

    # the min/max of temporal regions can be defined in two ways:
    time_ranges = [
        [6, 8],  # in same units as the x axis, OR
        Time(['2011-07-19', '2011-07-23'])  # directly with a Time object
    ]

    for time_range in time_ranges:
        subset_plugin._obj.subset_selected = "Create New"
        viewer.apply_roi(XRangeROI(*time_range))

    subsets = helper.app.get_subsets()

    subset_1_bounds_jd = subsets['Subset 1'][0]['region'].jd
    subset_2_bounds_jd = subsets['Subset 2'][0]['region'].jd

    np.testing.assert_allclose(subset_1_bounds_jd, [2455745., 2455747.])
    np.testing.assert_allclose(subset_2_bounds_jd, [2455761.50076602, 2455765.50076602])


def test_apply_yrangerois(helper, light_curve_like_kepler_quarter):
    lc = light_curve_like_kepler_quarter
    helper.load_data(lc)
    viewer = helper.default_time_viewer._obj
    subset_plugin = helper.plugins['Subset Tools']

    subset_plugin._obj.subset_selected = "Create New"
    viewer.apply_roi(YRangeROI(1, 1.05))

    subsets = helper.app.get_subsets()

    # TODO: subsets['Subset 1'][0]['region'] is still returning a Time object

    subset_state = subsets['Subset 1'][0]['subset_state']

    np.testing.assert_allclose([subset_state.lo, subset_state.hi], [1, 1.05])
