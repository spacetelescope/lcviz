.. _lcviz-loader-light-curve:

***********
Light Curve
***********

Import a ``lightkurve.LightCurve`` object, a FITS light curve file, or a
Rocky Worlds HDF5 light curve file into jdaviz.

Overview
========

The Light Curve importer accepts a :class:`lightkurve.LightCurve` object (or any
FITS file readable as one) and loads it into the data collection, creating a
time-scatter viewer automatically.

Rocky Worlds HDF5
================

Rocky Worlds light curve products (``HLSPID=Rocky-Worlds``) are also supported.
All visits are combined into a single data entry, sorted by time. Times are
interpreted as full BJD in the TDB scale. Rows missing every flux and uncertainty
are omitted, including padding introduced by alignment between visits; other
missing flux values are preserved.

All flux columns are retained, with ``rawFlux`` selected initially and
``rawFluxErr`` imported as ``rawFlux_err``. The Flux Column plugin can switch to
``cleanedFlux`` or other supplied flux columns. Uncertainty names ending in
``Err`` are converted to ``_err`` to associate them with their flux column;
uncertainties are not inferred for columns without supplied errors.
Model datasets with names ending in ``Model`` (case-insensitive), such as
``astroModel``, ``noiseModel``, and ``fullModel``, are exposed as Extension
options alongside ``Light curve``. By default, only the light curve is imported.
Each selected model is imported as a separate light curve with the model values
as its flux, combining all visits and omitting missing model values. Models are
not stored as columns in the observed light curve, and diagnostic arrays are
not imported. Root metadata are preserved.

Enable extension multiselect to import the light curve and/or several models.
The Data Label becomes a prefix: entries are labeled
``<Data Label> [<Extension>]``.
The loader previews the resolved labels and marks entries that will overwrite
existing data.

.. code-block:: python

    import jdaviz as jd
    import lcviz

    jd.load("hlsp_rocky-worlds_example_lc.h5", format="Light Curve")

To select models programmatically:

.. code-block:: python

    ldr = jd.loaders["file"]
    ldr.filepath = "hlsp_rocky-worlds_example_lc.h5"
    ldr.format = "Light Curve"
    ldr.importer.extension.multiselect = True
    ldr.importer.extension = ["Light curve", "fullModel"]
    ldr.importer.data_label = "GJ 3929 b"
    ldr.load()

UI Access
=========

.. guidestar-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action": "show-sidebar", "value": "loaders", "delay": 1500, "caption": "Open the data loader"}, {"action": "select-dropdown", "value": "Format:Light Curve", "delay": 1000, "caption": "Set format to Light Curve"}, {"action": "highlight", "target": "#format-select", "delay": 1500}]

Usage
=====

.. code-block:: python

    import jdaviz as jd
    import lcviz
    from lightkurve import search_lightcurve

    lc = search_lightcurve("HAT-P-11", mission="Kepler",
                           cadence="long", quarter=10).download()
    jd.load(lc, format="Light Curve")
    jd.show()

.. seealso::

    :class:`~lcviz.loaders.importers.lightcurve.lightcurve.LightCurveImporter`
        API documentation for the Light Curve importer.
