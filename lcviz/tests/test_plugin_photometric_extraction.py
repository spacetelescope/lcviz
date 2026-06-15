import pytest


@pytest.mark.remote_data
@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_docs_snippets(helper_name, request):
    jd = request.getfixturevalue(helper_name)
    from lightkurve import search_targetpixelfile
    tpf = search_targetpixelfile("KIC 001429092",
                                 mission="Kepler",
                                 cadence="long",
                                 quarter=10).download()
    jd.load(tpf, format='TPF')
    # jd.show()

    ext = jd.plugins['Photometric Extraction']
    ext.open_in_tray()


@pytest.mark.remote_data
@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_loader_autoextract(helper_name, light_curve_like_kepler_quarter, request):
    helper = request.getfixturevalue(helper_name)
    from lightkurve import search_targetpixelfile
    tpf = search_targetpixelfile("KIC 001429092",
                                 mission="Kepler",
                                 cadence="long",
                                 quarter=10).download()
    lcviz = helper

    ldr = lcviz.loaders['object']
    ldr.object = tpf
    ldr.importer.auto_extract = True
    ldr.load()

    assert len(lcviz.viewers) == 2
    assert len(lcviz._app.data_collection) == 2


@pytest.mark.remote_data
@pytest.mark.parametrize('helper_name', ['helper', 'deconfigged_helper'])
def test_plugin_photometric_extraction(helper_name, light_curve_like_kepler_quarter, request):
    helper = request.getfixturevalue(helper_name)
    from lightkurve import search_targetpixelfile
    tpf = search_targetpixelfile("KIC 001429092",
                                 mission="Kepler",
                                 cadence="long",
                                 quarter=10).download()
    lcviz = helper
    lcviz.load(tpf)

    assert len(lcviz.viewers) == 1  # only TPF viewer
    assert len(lcviz._app.data_collection) == 1  # only TPF data

    ext = lcviz.plugins['Photometric Extraction']
    ext.extract(add_data=True)

    assert len(lcviz._app.data_collection) == 2
