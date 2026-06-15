import pytest


@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_reset_limits(helper_name, light_curve_like_kepler_quarter, request):
    helper = request.getfixturevalue(helper_name)
    helper.load(light_curve_like_kepler_quarter, format='Light Curve')
    tv = helper.viewers['flux-vs-time']._obj.glue_viewer

    orig_xlims = (tv.state.x_min, tv.state.x_max)
    orig_ylims = (tv.state.y_min, tv.state.y_max)
    # set xmin and ymin to midpoints
    new_xmin = (tv.state.x_min + tv.state.x_max) / 2
    new_ymin = (tv.state.y_min + tv.state.y_max) / 2
    tv.state.x_min = new_xmin
    tv.state.y_min = new_ymin

    tv.state._reset_x_limits()
    assert tv.state.x_min == orig_xlims[0]
    assert tv.state.y_min == new_ymin

    tv.state._reset_y_limits()
    assert tv.state.y_min == orig_ylims[0]


@pytest.mark.remote_data
@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_clone(helper_name, light_curve_like_kepler_quarter, request):
    helper = request.getfixturevalue(helper_name)
    helper.load(light_curve_like_kepler_quarter, format='Light Curve')

    def_viewer = helper.viewers['flux-vs-time']
    assert helper._get_clone_viewer_reference(def_viewer._obj.reference) == 'flux-vs-time[1]'

    new_viewer = def_viewer._obj.glue_viewer.clone_viewer()
    assert helper._get_clone_viewer_reference(new_viewer._obj.reference) == 'flux-vs-time[2]'

    # TODO: replace with test fixture
    from lightkurve import search_targetpixelfile
    tpf = search_targetpixelfile("KIC 001429092",
                                 mission="Kepler",
                                 cadence="long",
                                 quarter=10).download()
    helper.load(tpf)
    im_viewer = helper.viewers['TPF']
    assert helper._get_clone_viewer_reference(im_viewer._obj.reference) == 'TPF[1]'
    im_viewer._obj.glue_viewer.clone_viewer()
