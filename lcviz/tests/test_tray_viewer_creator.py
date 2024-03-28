def test_tray_viewer_creator(helper, light_curve_like_kepler_quarter):
    # additional coverage in test_plugin_ephemeris
    helper.load_data(light_curve_like_kepler_quarter)
    vc = helper._tray_tools['g-viewer-creator']

    assert len(helper.viewers) == 1
    assert len(vc.viewer_types) == 2  # time and default phase
    vc.vue_create_viewer('flux-vs-time')
    assert len(helper.viewers) == 2
