from astropy.table import Table


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
