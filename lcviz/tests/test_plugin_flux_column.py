import pytest

from lightkurve import LightCurve
from numpy.testing import assert_allclose


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_docs_snippets(helper_name, light_curve_like_kepler_quarter, request):
    jd = request.getfixturevalue(helper_name)
    lc = light_curve_like_kepler_quarter

    jd.load(lc, format='Light Curve')
    # jd.show()

    flux_col = jd.plugins['Flux Column']
    print(flux_col.flux_column.choices)
    # NOTE: choices for docs example are: ['sap_flux', 'sap_bkg', 'pdcsap_flux']
    flux_col.flux_column = 'flux_alt'


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_plugin_flux_column(helper_name, light_curve_like_kepler_quarter, request):
    helper = request.getfixturevalue(helper_name)
    helper.load(light_curve_like_kepler_quarter, format='Light Curve')

    fo = helper.plugins['Flux Column']
    assert len(fo.flux_column.choices) == 2
    assert fo.flux_column.selected == 'flux:orig'

    lc = helper.get_data(cls=LightCurve)
    assert lc.meta.get('FLUX_ORIGIN') == 'flux:orig'
    assert_allclose(lc['flux'], fo._obj.dataset.selected_dc_item['flux:orig'])

    fo.flux_column = 'flux_alt'
    lc = helper.get_data(cls=LightCurve)
    assert lc.meta.get('FLUX_ORIGIN') == 'flux_alt'
    assert_allclose(lc['flux'], fo._obj.dataset.selected_dc_item['flux_alt'])
