import pytest


@pytest.mark.remote_data
def test_example_notebook():
    import astropy.units as u
    from astropy.time import Time
    from lightkurve import search_lightcurve

    import jdaviz as jd
    import lcviz  # noqa

    # Download the light curve from MAST:
    lc_q9 = search_lightcurve("HAT-P-11", mission="Kepler", cadence="long", quarter=9).download()

    # Load the light curve into jdaviz with lcviz:
    jd.load(lc_q9, data_label='Q9', format='Light Curve')
    # jd.show()

    # Download another Kepler quarter:
    lc_q10 = search_lightcurve("HAT-P-11", mission="Kepler", cadence="long", quarter=10).download()

    # load two quarters into LCviz:
    jd.load(lc_q10, data_label='Q10', format='Light Curve')

    # use the flatten plugin to flatten each quarter:
    flatten = jd.plugins['Flatten']

    for dataset in flatten.dataset.choices:
        flatten.dataset = dataset
        flatten.window_length = 50
        flatten.flatten()

    jd.viewers['flux-vs-time'].reset_limits()

    # get the origin of the time axis:
    reference_time = jd.datasets['Q9'].get_data().reference_time

    # literature ephemeris for hot Neptune planet HAT-P-11 b:
    morris2017_epoch = Time(2454605.89146, format='jd')
    morris2017_period = 4.88780258  # days

    # phase-fold the transit light curve in an ephemeris viewer:
    eph = jd.plugins['Ephemeris']
    eph.period = morris2017_period
    eph.t0 = (
        (morris2017_epoch - reference_time).to_value(u.d) % eph.period
    )

    # offset the wrapping phase so the transit (at phase 0) displays at center
    eph.wrap_at = 0.5
