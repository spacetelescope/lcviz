from lcviz.marks import LivePreviewBinning


def _get_marks_from_viewer(viewer, cls=(LivePreviewBinning)):
    return [m for m in viewer.figure.marks if isinstance(m, cls) and m.visible]


def test_plugin_binning(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)
    tv = helper.app.get_viewer(helper._default_time_viewer_reference_name)

    b = helper.plugins['Binning']
    b._obj.plugin_opened = True
    ephem = helper.plugins['Ephemeris']
    ephem.period = 1.2345
    pv = ephem.create_phase_viewer()

    assert b.ephemeris == 'No ephemeris'
    assert len(_get_marks_from_viewer(tv)) == 1
    assert len(_get_marks_from_viewer(pv)) == 0

    b.bin(add_data=True)

    b.ephemeris = 'default'
    assert len(_get_marks_from_viewer(tv)) == 0
    assert len(_get_marks_from_viewer(pv)) == 1

    b.bin(add_data=True)
