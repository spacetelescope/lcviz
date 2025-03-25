def test_docs_snippets(helper, light_curve_like_kepler_quarter):
    lcviz, lc = helper, light_curve_like_kepler_quarter
    lc1 = lc
    lc2 = lc.copy()

    lcviz.load_data(lc1, 'lc1')
    lcviz.load_data(lc2, 'lc2')
    lcviz.app.add_data_to_viewer('flux-vs-time', 'lc2')
    # lcviz.show()

    stitch = lcviz.plugins['Stitch']
    stitch.open_in_tray()
    stitch.dataset.select_all()
    stitched_lc = stitch.stitch()
    print(stitched_lc)


def test_plugin_stitch(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter, 'lc1')

    assert "Stitch" not in helper.plugins.keys()

    helper.load_data(light_curve_like_kepler_quarter.copy(), 'lc2')
    helper.app.add_data_to_viewer('flux-vs-time', 'lc2')
    assert "Stitch" in helper.plugins.keys()

    stitch = helper.plugins['Stitch']
    stitch.dataset.select_all()
    stitch.remove_input_datasets = True
    stitched_lc = stitch.stitch()

    assert len(stitched_lc) == 2 * len(light_curve_like_kepler_quarter)
    assert len(helper.app.data_collection) == 1
