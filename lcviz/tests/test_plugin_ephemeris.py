

def test_plugin_ephemeris(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)
    ephem = helper.plugins['Ephemeris']

    assert len(helper.app.get_viewer_ids()) == 1
    assert not ephem._obj.phase_viewer_exists

    # setting any value in the ephemeris should create a new viewer
    ephem.period = 3.14
    assert len(helper.app.get_viewer_ids()) == 2
    assert ephem._obj.phase_viewer_exists
    assert ephem._obj.phase_viewer_id in helper.app.get_viewer_ids()

    ephem.t0 = 5
    ephem._obj.vue_period_double()
    assert ephem.period == 3.14 * 2
    ephem._obj.vue_period_halve()
    assert ephem.period == 3.14
