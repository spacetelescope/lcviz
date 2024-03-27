import pytest


def test_reset_limits(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)
    tv = helper.default_time_viewer._obj

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
def test_clone(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)

    def_viewer = helper.viewers['flux-vs-time']
    assert helper._get_clone_viewer_reference(def_viewer._obj.reference) == 'flux-vs-time[1]'

    new_viewer = def_viewer._obj.clone_viewer()
    assert helper._get_clone_viewer_reference(new_viewer._obj.reference) == 'flux-vs-time[2]'

    # TODO: replace with test fixture
    from lightkurve import search_targetpixelfile
    tpf = search_targetpixelfile("KIC 001429092",
                                 mission="Kepler",
                                 cadence="long",
                                 quarter=10).download()
    helper.load_data(tpf)
    im_viewer = helper.viewers['image']
    assert helper._get_clone_viewer_reference(im_viewer._obj.reference) == 'image[1]'
    im_viewer._obj.clone_viewer()
