.. _lcviz-loader-lightkurve-resolver:

********************
Lightkurve Resolver
********************

Query the Kepler, K2, and TESS archive via ``lightkurve`` and load results directly into lcviz.

Overview
========

The Lightkurve Resolver performs a cone search around a target name or sky coordinates
using :func:`lightkurve.search_lightcurve` or :func:`lightkurve.search_targetpixelfile`.
Results are presented as a table; selected entries are downloaded and loaded as
Light Curve or Target Pixel File data.

Like the jdaviz Astroquery and Virtual Observatory resolvers, this resolver also
accepts a loaded source catalog or a subset of its rows. Lightkurve searches one
target at a time, so catalog queries run once per selected row and combine the
results into a single table.

Parameters
==========

**Input**
    ``Source``, ``Viewer`` (when available), or ``Catalog`` (when a source catalog
    has been loaded).

**Source/Coordinates**
    A source name (resolved via SIMBAD) or sky coordinates in degrees.
    When a viewer is selected the coordinates can be read from the viewer centre.

**Coordinate Frame**
    Astronomical coordinate frame for the provided coordinates (e.g. ``icrs``).

**Catalog / Subset**
    The loaded source catalog to query, optionally restricted to a selected
    subset. The default subset is ``Entire Catalog``.

**Coordinates from / Source Name Column**
    Use the catalog's assigned RA/Dec columns (``catalog_col_type = "sky_coords"``),
    or resolve entries in a source-name column
    (``catalog_col_type = "source_name"`` and ``catalog_name_col``).
    Source-name resolution uses Sesame/CDS and adds one request per selected row.

**Radius**
    Angular search radius around the target (default: 10 arcsec).

**Radius Unit**
    Unit for the search radius. Supported values include ``arcsec``, ``arcmin``, and ``deg``.

**Mission**
    Space mission to search: ``Kepler``, ``K2``, or ``TESS``.

**Data Type**
    Whether to search for ``Light Curve`` or ``Target Pixel File`` products.

**Max Results**
    Maximum total number of archive results to return (default: 100), across all
    selected sources. Catalog querying stops once this limit is reached.

**Query Progress**
    ``query_progress`` reports the current catalog source while querying and is
    cleared when the query finishes. Individual search failures are reported
    without discarding successful results from other sources.

UI Access
=========

.. guidestar-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action": "show-sidebar", "value": "loaders", "delay": 1500, "caption": "Open the data loader"}, {"action": "select-dropdown", "value": "Source:Lightkurve", "delay": 1000, "caption": "Set source to Lightkurve"}, {"action": "highlight", "target": "#source-select", "delay": 1500}]

Usage
=====

.. code-block:: python

    import lcviz
    viz = lcviz.LCviz()

    # Access the lightkurve resolver
    ldr = viz.loaders["lightkurve"]

    # Configure and query
    ldr.source = "HAT-P-11"
    ldr.mission.selected = "Kepler"
    ldr.data_type.selected = "Light Curve"
    ldr.radius = 10
    ldr.radius_unit.selected = "arcsec"
    ldr.max_results = 50
    ldr.query_archive()

    # Load a result from the returned table
    ldr.load()
    viz.show()

To query an already loaded source catalog:

.. code-block:: python

    ldr.search_input = "Catalog"
    ldr.catalog = "my catalog"  # label in the data collection
    ldr.catalog_subset = "Entire Catalog"  # or a subset label
    ldr.catalog_col_type = "sky_coords"
    ldr.query_archive()

    # Alternatively, resolve a column of source names:
    ldr.catalog_col_type = "source_name"
    ldr.catalog_name_col = "source_id"
    ldr.query_archive()

.. seealso::

    :class:`~lcviz.loaders.resolvers.lightkurve.lightkurve.LightkurveResolver`
        API documentation for the Lightkurve resolver.

    :func:`lightkurve.search_lightcurve`
        lightkurve documentation on light curve archive searches.

    :func:`lightkurve.search_targetpixelfile`
        lightkurve documentation on target pixel file archive searches.

    :ref:`lcviz-loader-tpf`
        Loading Target Pixel File data into lcviz.
