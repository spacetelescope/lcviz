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
    assert 'flux-vs-phase:default' in helper.app.get_viewer_ids()

    ephem.t0 = 5
    ephem._obj.vue_period_double()
    assert ephem.period == 3.14 * 2
    ephem._obj.vue_period_halve()
    assert ephem.period == 3.14

    pv = ephem._obj.default_phase_viewer
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


def test_cloned_phase_viewer(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)
    ephem = helper.plugins['Ephemeris']

    assert len(ephem._obj._get_phase_viewers()) == 0
    pv1 = ephem.create_phase_viewer()
    assert len(ephem._obj._get_phase_viewers()) == 1
    pv2 = pv1._obj.clone_viewer()
    assert len(ephem._obj._get_phase_viewers()) == 2
    assert len(helper.viewers) == 3
    assert pv1._obj.reference_id == 'flux-vs-phase:default'
    assert pv1._obj._ephemeris_component == 'default'
    assert pv2._obj.reference_id == 'flux-vs-phase:default[1]'
    assert pv2._obj._ephemeris_component == 'default'

    # renaming ephemeris should update both labels
    ephem.rename_component('default', 'renamed')
    assert pv1._obj.reference_id == 'flux-vs-phase:renamed'
    assert pv1._obj._ephemeris_component == 'renamed'
    assert pv2._obj.reference_id == 'flux-vs-phase:renamed[1]'
    assert pv2._obj._ephemeris_component == 'renamed'
    assert len(ephem._obj._get_phase_viewers()) == 2

    ephem.remove_component('renamed')
    assert len(helper.viewers) == 1  # just flux-vs-phase


def test_create_phase_viewer(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)
    ephem = helper.plugins['Ephemeris']
    vc = helper._tray_tools['g-viewer-creator']

    assert len(vc.viewer_types) == 2  # time viewer, phase viewer for default
    _ = ephem.create_phase_viewer()
    assert len(ephem._obj._get_phase_viewers()) == 1

    vc.vue_create_viewer('flux-vs-phase:default')
    assert len(ephem._obj._get_phase_viewers()) == 2
    for pv in ephem._obj._get_phase_viewers():
        assert pv._ephemeris_component == 'default'

    ephem.rename_component('default', 'renamed')
    assert len(vc.viewer_types) == 2
    vc.vue_create_viewer('flux-vs-phase:renamed')
    assert len(ephem._obj._get_phase_viewers()) == 3

    for pv in ephem._obj._get_phase_viewers():
        assert pv._ephemeris_component == 'renamed'

    ephem.add_component('new')
    assert len(vc.viewer_types) == 3


def compare_against_literature_ephemeris(helper, ephem):
    # compare against best/recent parameters:
    period_yee_2018 = 4.88780244
    assert abs(1 - period_yee_2018 / ephem.period) < 1e-3

    # epoch_kokori_2022 = 2455109.335119
    # ref_time = helper.app.data_collection[0].coords.reference_time.jd
    # expected_t0 = (epoch_kokori_2022 - ref_time) % period_yee_2018
    expected_t0 = 0.8932070000283261
    assert abs(1 - expected_t0 / ephem.t0) < 1e-3


def test_ephemeris_queries(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)
    ephem = helper.plugins['Ephemeris']

    ephem.query_for_ephemeris()
    planet = ephem.query_result.choices[0]
    assert planet == 'HAT-P-11 b'

    ephem.query_result = planet
    ephem.create_ephemeris_from_query()

    compare_against_literature_ephemeris(helper, ephem)


def test_ephemeris_query_no_name(helper, light_curve_like_kepler_quarter):
    # test that the query successfully falls back on the RA/Dec:
    light_curve_like_kepler_quarter.meta['OBJECT'] = ''

    helper.load_data(light_curve_like_kepler_quarter)
    ephem = helper.plugins['Ephemeris']

    ephem.query_for_ephemeris()
    planet = ephem.query_result.choices[0]
    assert planet == 'HAT-P-11 b'

    ephem.query_result = planet
    ephem.create_ephemeris_from_query()

    compare_against_literature_ephemeris(helper, ephem)
