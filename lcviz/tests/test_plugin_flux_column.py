from numpy.testing import assert_allclose


def test_docs_snippets(helper, light_curve_like_kepler_quarter):
    lcviz, lc = helper, light_curve_like_kepler_quarter

    lcviz.load_data(lc)
    # lcviz.show()

    flux_col = lcviz.plugins['Flux Column']
    print(flux_col.flux_column.choices)
    # NOTE: choices for docs example are: ['sap_flux', 'sap_bkg', 'pdcsap_flux']
    flux_col.flux_column = 'flux_alt'


def test_plugin_flux_column(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)

    fo = helper.plugins['Flux Column']
    assert len(fo.flux_column.choices) == 2
    assert fo.flux_column.selected == 'flux:orig'

    lc = helper.get_data()
    assert lc.meta.get('FLUX_ORIGIN') == 'flux:orig'
    assert_allclose(lc['flux'], fo._obj.dataset.selected_dc_item['flux:orig'])

    fo.flux_column = 'flux_alt'
    lc = helper.get_data()
    assert lc.meta.get('FLUX_ORIGIN') == 'flux_alt'
    assert_allclose(lc['flux'], fo._obj.dataset.selected_dc_item['flux_alt'])
