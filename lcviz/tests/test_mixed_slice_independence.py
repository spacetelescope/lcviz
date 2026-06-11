"""
Tests that the slice tool in lcviz light-curve viewers and the slice tool in
jdaviz spectral viewers remain independent when both data types are loaded into
the same deconfigged app.
"""
import numpy as np
import pytest
import astropy.units as u
from astropy.wcs import WCS
from specutils import Spectrum


def _make_spectrum3d(shape=(4, 3, 3)):
    """Create a minimal 3-D Spectrum for testing."""
    nz, ny, nx = shape
    flux = np.arange(np.prod(shape)).reshape(shape) * u.Jy
    wcs_dict = {
        "CTYPE1": "RA---TAN", "CTYPE2": "DEC--TAN", "CTYPE3": "WAVE-LOG",
        "CRVAL1": 205, "CRVAL2": 27, "CRVAL3": 4.622e-7,
        "CDELT1": -0.0001, "CDELT2": 0.0001, "CDELT3": 8e-11,
        "CRPIX1": 0, "CRPIX2": 0, "CRPIX3": 0,
        "PIXAR_SR": 10.,
    }
    w = WCS(wcs_dict)
    return Spectrum(flux=flux, wcs=w, meta=wcs_dict)


def _load_both(jd, light_curve_like_kepler_quarter):
    """Load a spectrum cube and a light curve into a deconfigged app."""
    spec3d = _make_spectrum3d()
    ldr = jd.loaders['object']
    ldr.object = spec3d
    ldr.format = '3D Spectrum'
    ldr.load()

    jd.load(light_curve_like_kepler_quarter, format='Light Curve')


def test_lc_slice_does_not_affect_spectral_slice(
        deconfigged_helper, light_curve_like_kepler_quarter):
    """Moving the slice indicator in a light-curve viewer must not change the
    spectral slice value."""
    jd = deconfigged_helper
    _load_both(jd, light_curve_like_kepler_quarter)

    time_plg = jd.plugins['Time Selector']
    spectral_plg = jd.plugins['Spectral Slice']

    initial_spectral_value = spectral_plg.value

    # Simulate the select-slice tool by broadcasting a SliceSelectSliceMessage
    # from a time-scatter viewer (the same path the interactive tool takes).
    from jdaviz.core.events import SliceSelectSliceMessage
    from lcviz.viewers import TimeScatterView

    time_viewers = [v for v in jd._app._viewer_store.values()
                    if isinstance(v, TimeScatterView)]
    assert len(time_viewers) >= 1, "Expected at least one time viewer"
    time_viewer = time_viewers[0]

    # Pick a new time value different from the current one
    slice_values = time_plg._obj.valid_indicator_values_sorted
    new_time_value = float(slice_values[len(slice_values) // 4])
    assert new_time_value != time_plg.value

    # Create a minimal sender stub that looks like the SelectSlice tool
    class _Sender:
        viewer = time_viewer

    msg = SliceSelectSliceMessage(value=new_time_value, sender=_Sender())
    jd._app.hub.broadcast(msg)

    # Time Selector should have updated
    assert abs(time_plg.value - new_time_value) < abs(
        slice_values[1] - slice_values[0])

    # Spectral Slice must be unchanged
    assert spectral_plg.value == initial_spectral_value


def test_spectral_slice_does_not_affect_lc_indicator(
        deconfigged_helper, light_curve_like_kepler_quarter):
    """Moving the slice indicator in the spectrum viewer must not change the
    time-selector value."""
    jd = deconfigged_helper
    _load_both(jd, light_curve_like_kepler_quarter)

    time_plg = jd.plugins['Time Selector']
    spectral_plg = jd.plugins['Spectral Slice']

    initial_time_value = time_plg.value

    # Simulate the select-slice tool from the spectrum (profile) viewer.
    from jdaviz.core.events import SliceSelectSliceMessage
    from jdaviz.configs.specviz.plugins.viewers import Spectrum1DViewer

    spectrum_viewers = [v for v in jd._app._viewer_store.values()
                        if type(v) is Spectrum1DViewer]
    assert len(spectrum_viewers) >= 1, "Expected at least one spectrum viewer"
    spectrum_viewer = spectrum_viewers[0]

    # Pick a spectral slice value different from the current one
    slice_values = spectral_plg._obj.valid_selection_values_sorted
    new_spectral_value = float(slice_values[0])
    assert new_spectral_value != spectral_plg.value

    class _Sender:
        viewer = spectrum_viewer

    msg = SliceSelectSliceMessage(value=new_spectral_value, sender=_Sender())
    jd._app.hub.broadcast(msg)

    # Spectral Slice should have updated
    assert spectral_plg.value == pytest.approx(new_spectral_value, abs=1e-20)

    # Time Selector must be unchanged
    assert time_plg.value == initial_time_value
