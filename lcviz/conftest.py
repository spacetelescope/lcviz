import numpy as np
import pytest
from astropy import units as u
from lightkurve import LightCurve

from lcviz import __version__, LCviz


@pytest.fixture
def helper():
    return LCviz()


@pytest.fixture
def light_curve_like_kepler_quarter(seed=42):
    """
    Generate a normalized (near unity) light curve with
    Gaussian noise. Times correspond very roughly to the
    Kepler 30-min cadences in Quarter 10. A random masking
    is applied to a small fraction of the fluxes.
    """
    np.random.seed(seed)
    exp_per_day = (30 * u.min).to_value(u.day)

    # approx start and stop JD for Kepler Quarter 10:
    time = np.arange(2455739, 2455833, exp_per_day)
    scale = 0.01
    flux = np.random.normal(
        1, scale=scale, size=len(time)
    ) * u.dimensionless_unscaled
    flux_err = scale * np.ones_like(flux)

    quality = np.zeros(len(time), dtype=np.int32)

    lc = LightCurve(
        time=time, flux=flux, flux_err=flux_err, quality=quality
    )
    lc['flux_alt'] = flux + 1
    lc['flux_alt_err'] = flux_err
    lc.meta.update(
        {
            'MISSION': 'KEPLER',
            'QUARTER': 10,
            'OBJECT': 'HAT-P-11',
            'RA': 297.7101763,
            'DEC': 48.0818635,
        }
    )

    return lc


try:
    from pytest_astropy_header.display import PYTEST_HEADER_MODULES, TESTED_VERSIONS
except ImportError:
    PYTEST_HEADER_MODULES = {}
    TESTED_VERSIONS = {}


def pytest_configure(config):
    PYTEST_HEADER_MODULES['astropy'] = 'astropy'
    PYTEST_HEADER_MODULES['glue-core'] = 'glue'
    PYTEST_HEADER_MODULES['glue-astronomy'] = 'glue_astronomy'
    PYTEST_HEADER_MODULES['gwcs'] = 'gwcs'
    PYTEST_HEADER_MODULES['lightkurve'] = 'lightkurve'

    TESTED_VERSIONS['lcviz'] = __version__
