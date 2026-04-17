import pytest


@pytest.mark.remote_data
def test_tray_viewer_creator(helper, light_curve_like_kepler_quarter):
    # additional coverage in test_plugin_ephemeris
    helper.load(light_curve_like_kepler_quarter)
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
    helper.load(tpf)
    assert len(helper.viewers) == 3  # image viewer added by default

    assert len(vc.viewer_types) == 3  # time, default phase, cube
    vc.vue_create_viewer('image')
    assert len(helper.viewers) == 4


@pytest.mark.remote_data
def test_tpf_viewer_creator(deconfigged_helper):
    from lightkurve import search_targetpixelfile
    from lcviz.viewer_creators.tpf.tpf import TPFViewerCreator
    from lcviz.viewers import CubeView

    jd = deconfigged_helper

    # before loading any data, TPF creator is not relevant
    nv_labels = [item['label'] for item in jd._app.state.new_viewer_items]
    assert 'TPF' in nv_labels
    image_item = next(i for i in jd._app.state.new_viewer_items if i['label'] == 'TPF')
    assert not image_item['is_relevant']

    # load a TPF
    tpf = search_targetpixelfile("KIC 001429092",
                                 mission="Kepler",
                                 cadence="long",
                                 quarter=10).download()
    jd.load(tpf, format='TPF')

    # TPF viewer creator should now be relevant
    image_item = next(i for i in jd._app.state.new_viewer_items if i['label'] == 'TPF')
    assert image_item['is_relevant']

    # the TPF creator should appear in new_viewers
    assert 'TPF' in jd.new_viewers

    # create an image viewer via the creator
    n_viewers_before = len(jd.viewers)
    vc_widget()
    assert len(jd.viewers) == n_viewers_before + 1
