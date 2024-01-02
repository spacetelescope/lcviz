from numpy.testing import assert_allclose


def test_docs_snippets(helper, light_curve_like_kepler_quarter):
    lcviz, lc = helper, light_curve_like_kepler_quarter

    lcviz.load_data(lc)
    # lcviz.show()

    flux_origin = lcviz.plugins['Flux Origin']
    print(flux_origin.flux_origin.choices)
    # NOTE: choices for docs example are: ['sap_flux', 'sap_bkg', 'pdcsap_flux']
    flux_origin.flux_origin = 'flux_alt'


def test_plugin_flux_origin(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)

    fo = helper.plugins['Flux Origin']
    assert len(fo.flux_origin.choices) == 2
    assert fo.flux_origin.selected == 'flux:orig'

    lc = helper.get_data()
    assert lc.meta.get('FLUX_ORIGIN') == 'flux:orig'
    assert_allclose(lc['flux'], fo._obj.dataset.selected_dc_item['flux:orig'])

    fo.flux_origin = 'flux_alt'
    lc = helper.get_data()
    assert lc.meta.get('FLUX_ORIGIN') == 'flux_alt'
    assert_allclose(lc['flux'], fo._obj.dataset.selected_dc_item['flux_alt'])
