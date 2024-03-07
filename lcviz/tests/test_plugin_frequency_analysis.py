from numpy.testing import assert_allclose

from lightkurve.periodogram import LombScarglePeriodogram, BoxLeastSquaresPeriodogram


def test_docs_snippets(helper, light_curve_like_kepler_quarter):
    lcviz, lc = helper, light_curve_like_kepler_quarter

    lcviz.load_data(lc)
    # lcviz.show()

    freq = lcviz.plugins['Frequency Analysis']
    freq.open_in_tray()
    freq.method = 'Lomb-Scargle'
    freq.xunit = 'period'
    periodogram = freq.periodogram
    print(periodogram)


def test_plugin_frequency_analysis(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)

    freq = helper.plugins['Frequency Analysis']
    freq.open_in_tray()

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
