from numpy.testing import assert_allclose


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
