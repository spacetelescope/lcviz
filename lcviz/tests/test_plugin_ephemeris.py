import pytest


def test_docs_snippets(helper, light_curve_like_kepler_quarter):
    lcviz, lc = helper, light_curve_like_kepler_quarter

    lcviz.load_data(lc)
    # lcviz.show()

    ephem = lcviz.plugins['Ephemeris']
    ephem.period = 4.88780258
    ephem.t0 = 2.43
    ephem.rename_component('default', 'my component name')


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

    pv = ephem._obj.phase_viewer
    # original limits are set to 0->1 (technically 1-phase_wrap -> phase_wrap)
    assert (pv.state.x_min, pv.state.x_max) == (0.0, 1.0)
    ephem.wrap_at = 0.5
    assert (pv.state.x_min, pv.state.x_max) == (-0.5, 0.5)

    ephem.add_component('custom component')
    assert not ephem._obj.phase_viewer_exists
    ephem.create_phase_viewer()
    assert len(helper.app.get_viewer_ids()) == 3
    assert len(ephem.ephemerides) == 2
    assert 'custom component' in ephem.ephemerides

    with pytest.raises(ValueError):
        # brackets interfere with cloned viewer label logic
        ephem.rename_component('custom component', 'custom component[blah]')
    with pytest.raises(ValueError):
        # colons interfere with viewer ephemeris logic
        ephem.rename_component('custom component', 'custom component:blah')

    ephem.rename_component('custom component', 'renamed custom component')
    assert len(ephem.ephemerides) == 2
    assert 'renamed custom component' in ephem.ephemerides
    assert len(helper.app.get_viewer_ids()) == 3

    assert ephem.component == 'renamed custom component'
    assert ephem.period == 3.14
    assert ephem.ephemeris['period'] == 3.14
    # modify the ephemeris of the NON-selected ephemeris component
    ephem.update_ephemeris(ephem_component='default', period=2)
    assert ephem.period == 3.14
    assert ephem.ephemerides['default']['period'] == 2

    ephem.remove_component('renamed custom component')
    assert len(ephem.ephemerides) == 1
    assert len(helper.app.get_viewer_ids()) == 2
    assert ephem.component == 'default'
    assert ephem.period == 2

    assert ephem.method.selected == 'Lomb-Scargle'
    ephem.method = 'Box Least Squares'
    assert ephem._obj.method_err == ''
    ephem._obj.vue_adopt_period_at_max_power()
    assert ephem.period != 2

    # test that non-zero dpdt does not crash
    ephem.dpdt = 0.005
