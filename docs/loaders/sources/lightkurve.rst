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

Parameters
==========

**Source/Coordinates**
    A source name (resolved via SIMBAD) or sky coordinates in degrees.
    When a viewer is selected the coordinates can be read from the viewer centre.

**Coordinate Frame**
    Astronomical coordinate frame for the provided coordinates (e.g. ``icrs``).

**Radius**
    Angular search radius around the target (default: 10 arcsec).

**Radius Unit**
    Unit for the search radius. Supported values include ``arcsec``, ``arcmin``, and ``deg``.

**Mission**
    Space mission to search: ``Kepler``, ``K2``, or ``TESS``.

**Data Type**
    Whether to search for ``Light Curve`` or ``Target Pixel File`` products.

**Max Results**
    Maximum number of archive results to return (default: 100).

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

.. seealso::

    :class:`~lcviz.loaders.resolvers.lightkurve.lightkurve.LightkurveResolver`
        API documentation for the Lightkurve resolver.

    :func:`lightkurve.search_lightcurve`
        lightkurve documentation on light curve archive searches.

    :func:`lightkurve.search_targetpixelfile`
        lightkurve documentation on target pixel file archive searches.

    :ref:`lcviz-loader-tpf`
        Loading Target Pixel File data into lcviz.
