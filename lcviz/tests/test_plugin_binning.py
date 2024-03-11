import pytest

from lcviz.marks import LivePreviewBinning


def _get_marks_from_viewer(viewer, cls=(LivePreviewBinning)):
    return [m for m in viewer.figure.marks if isinstance(m, cls) and m.visible]


def test_docs_snippets(helper, light_curve_like_kepler_quarter):
    lcviz, lc = helper, light_curve_like_kepler_quarter

    lcviz.load_data(lc)
    # lcviz.show()

    binning = lcviz.plugins['Binning']
    binning.n_bins = 150
    binned_lc = binning.bin(add_data=True)
    print(binned_lc)


def test_plugin_binning(helper, light_curve_like_kepler_quarter):
    helper.load_data(light_curve_like_kepler_quarter)
    tv = helper.default_time_viewer._obj

    b = helper.plugins['Binning']
    b._obj.plugin_opened = True
    ephem = helper.plugins['Ephemeris']
    ephem.period = 1.2345
    pv = ephem.create_phase_viewer()._obj

    with b.as_active():
        assert b.ephemeris == 'No ephemeris'
        assert len(_get_marks_from_viewer(tv)) == 1
        assert len(_get_marks_from_viewer(pv)) == 1
        assert b._obj.ephemeris_dict == {}

        # update ephemeris will force re-phasing
        ephem.period = 1.111

        b.bin(add_data=True)

        b.ephemeris = 'default'
        assert len(_get_marks_from_viewer(tv)) == 0
        assert len(_get_marks_from_viewer(pv)) == 1
        assert len(b._obj.ephemeris_dict.keys()) > 0

        # update ephemeris will force re-binning
        ephem.period = 1.222

        b.bin(add_data=True)

        # setting to invalid n_bins will raise error
        b.n_bins = 0
        assert b._obj.bin_enabled is False
        with pytest.raises(ValueError):
            b.bin(add_data=False)

        # the enabled state of the button should work with or without live previews enabled
        b.show_live_preview = False
        assert len(_get_marks_from_viewer(tv)) == 0
        assert len(_get_marks_from_viewer(pv)) == 0
        assert b._obj.bin_enabled is False
        b.n_bins = 1
        assert b._obj.bin_enabled is True
        b.n_bins = ''
        assert b._obj.bin_enabled is False
