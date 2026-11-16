import pytest
from astropy import units as u
from astropy.table import Table
from glue.core.subset import RangeSubsetState


def test_lightkurve_source_input_without_viewers(deconfigged_helper):
    resolver = deconfigged_helper.loaders['lightkurve']._obj

    assert resolver.viewer.labels == []
    assert resolver.search_input.labels == ['Source']
    assert resolver.search_input.selected == 'Source'

    queried_coords = []
    resolver.source = '10.5 -20.25'
    resolver._query_single_coord = (
        lambda coord: queried_coords.append(coord) or Table({'result': [1]})
    )

    resolver.query_archive()

    assert len(queried_coords) == 1
    assert queried_coords[0].ra.deg == 10.5
    assert queried_coords[0].dec.deg == -20.25
    assert len(resolver._output) == 1


@pytest.mark.remote_data
def test_lightkurve_catalog_input(deconfigged_helper):
    # Kepler-10, Kepler-11, and HAT-P-11.
    catalog = Table({
        'ra': [285.67942, 297.11510, 297.71018] * u.deg,
        'dec': [50.24131, 41.90910, 48.08186] * u.deg,
    })
    deconfigged_helper.load(catalog, format='Source Catalog', data_label='Sources')
    dc = deconfigged_helper._app.data_collection
    data = dc[0]
    subset = dc.new_subset_group(
        label='selected sources',
        subset_state=RangeSubsetState(290, 300, data.id['ra'])
    )
    assert subset.subset_state.to_mask(data).tolist() == [False, True, True]

    resolver = deconfigged_helper.loaders['lightkurve']
    resolver.search_input = 'Catalog'
    resolver.catalog = 'Sources'
    resolver.mission = 'Kepler'
    resolver.max_results = 1000
    resolver.query_archive()

    output = resolver._obj._output
    assert output is not None
    assert set(output['source_index']) == {0, 1, 2}

    resolver.catalog_subset = subset.label
    resolver.query_archive()

    subset_output = resolver._obj._output
    assert subset_output is not None
    assert set(subset_output['source_index']) == {0, 1}
