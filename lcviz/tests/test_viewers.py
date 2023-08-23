
def test_reset_limits(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)
    tv = helper.app.get_viewer(helper._default_time_viewer_reference_name)

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
