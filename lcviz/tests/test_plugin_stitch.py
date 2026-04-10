import pytest


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_docs_snippets(helper_name, light_curve_like_kepler_quarter, request):
    helper = request.getfixturevalue(helper_name)
    lcviz, lc = helper, light_curve_like_kepler_quarter
    lc1 = lc
    lc2 = lc.copy()

    lcviz.load(lc1, data_label='lc1')
    lcviz.load(lc2, data_label='lc2')
    # lcviz.show()

    stitch = lcviz.plugins['Stitch']
    stitch.open_in_tray()
    stitch.dataset.select_all()
    stitched_lc = stitch.stitch()
    print(stitched_lc)


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_plugin_stitch(helper_name, light_curve_like_kepler_quarter, request):
    helper = request.getfixturevalue(helper_name)
    helper.load(light_curve_like_kepler_quarter, data_label='lc1')

    assert "Stitch" not in helper.plugins.keys()

    helper.load(light_curve_like_kepler_quarter.copy(), data_label='lc2')
    helper._app.add_data_to_viewer('flux-vs-time', 'lc2')
    assert "Stitch" in helper.plugins.keys()

    stitch = helper.plugins['Stitch']
    stitch.dataset.select_all()
    stitch.remove_input_datasets = True
    stitched_lc = stitch.stitch()

    assert len(stitched_lc) == 2 * len(light_curve_like_kepler_quarter)
    assert len(helper._app.data_collection) == 1
