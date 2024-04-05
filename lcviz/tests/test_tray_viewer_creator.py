import pytest


@pytest.mark.remote_data
def test_tray_viewer_creator(helper, light_curve_like_kepler_quarter):
    # additional coverage in test_plugin_ephemeris
    helper.load_data(light_curve_like_kepler_quarter)
    vc = helper._tray_tools['g-viewer-creator']

    assert len(helper.viewers) == 1
    assert len(vc.viewer_types) == 2  # time and default phase
    vc.vue_create_viewer('flux-vs-time')
    assert len(helper.viewers) == 2

    # TODO: replace with test fixture
    from lightkurve import search_targetpixelfile
    tpf = search_targetpixelfile("KIC 001429092",
                                 mission="Kepler",
                                 cadence="long",
                                 quarter=10).download()
    helper.load_data(tpf)
    assert len(helper.viewers) == 3  # image viewer added by default

    assert len(vc.viewer_types) == 3  # time, default phase, cube
    vc.vue_create_viewer('image')
    assert len(helper.viewers) == 4
