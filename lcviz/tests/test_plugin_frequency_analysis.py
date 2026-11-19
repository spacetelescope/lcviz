import pytest

from numpy.testing import assert_allclose

from lightkurve.periodogram import LombScarglePeriodogram, BoxLeastSquaresPeriodogram


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_docs_snippets(helper_name, light_curve_like_kepler_quarter, request):
    jd = request.getfixturevalue(helper_name)
    lc = light_curve_like_kepler_quarter

    jd.load(lc, format='Light Curve')
    # jd.show()

    freq = jd.plugins['Frequency Analysis']
    freq.open_in_tray()
    freq.method = 'Lomb-Scargle'
    freq.xunit = 'period'
    periodogram = freq.periodogram
    print(periodogram)


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_plugin_frequency_analysis(helper_name, light_curve_like_kepler_quarter, request):
    helper = request.getfixturevalue(helper_name)
    helper.load(light_curve_like_kepler_quarter, format='Light Curve')

    freq = helper.plugins['Frequency Analysis']
    freq.open_in_tray()
    freq._obj.plugin_opened = True

    assert freq.method == 'Lomb-Scargle'
    assert freq._obj.err == ''
    assert isinstance(freq.periodogram, LombScarglePeriodogram)

    freq.method = 'Box Least Squares'
    assert freq._obj.err == ''
    assert isinstance(freq.periodogram, BoxLeastSquaresPeriodogram)

    assert freq.xunit == 'frequency'
    assert freq._obj.plot.figure.axes[0].label == 'frequency (1 / d)'

    freq.xunit = 'period'
    assert freq._obj.plot.figure.axes[0].label == 'period (d)'
    line_x = freq._obj.plot.layers['periodogram'].layer['x']
    assert_allclose((line_x.min(), line_x.max()), (0.3508333334885538, 31.309906458683404))

    freq.auto_range = False
    assert_allclose((freq.minimum, freq.maximum), (1, 10))
    while freq._obj.spinner:
        pass
    line_x = freq._obj.plot.layers['periodogram'].layer['x']
    assert_allclose((line_x.min(), line_x.max()), (1, 10.00141))

    freq.xunit = 'frequency'
    assert_allclose((freq.minimum, freq.maximum), (0.1, 1))
    while freq._obj.spinner:
        pass
    line_x = freq._obj.plot.layers['periodogram'].layer['x']
    assert_allclose((line_x.min(), line_x.max()), (0.0999859, 1))


def test_inactive_updates_are_deferred(helper, light_curve_like_kepler_quarter):
    helper.load(light_curve_like_kepler_quarter, format='Light Curve')

    freq = helper.plugins['Frequency Analysis']
    freq_obj = freq._obj
    assert freq_obj.is_active is False

    freq.method = 'Box Least Squares'
    assert 'periodogram' not in freq_obj.__dict__

    # API access still computes from the latest inputs while the UI is closed.
    assert isinstance(freq.periodogram, BoxLeastSquaresPeriodogram)
    assert 'periodogram' in freq_obj.__dict__

    freq.method = 'Lomb-Scargle'
    assert 'periodogram' not in freq_obj.__dict__

    freq_obj.plugin_opened = True
    assert isinstance(freq.periodogram, LombScarglePeriodogram)
