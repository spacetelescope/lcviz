.. _lcviz-loader-light-curve:

***********
Light Curve
***********

Import a ``lightkurve.LightCurve`` object or a FITS light curve file into jdaviz.

Overview
========

The Light Curve importer accepts a :class:`lightkurve.LightCurve` object (or any
FITS file readable as one) and loads it into the data collection, creating a
time-scatter viewer automatically.

UI Access
=========

.. wireframe-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action": "show-sidebar", "value": "loaders", "delay": 1500, "caption": "Open the data loader"}, {"action": "select-dropdown", "value": "Format:Light Curve", "delay": 1000, "caption": "Set format to Light Curve"}, {"action": "highlight", "target": "#format-select", "delay": 1500}]

Usage
=====

.. code-block:: python

    import jdaviz as jd
    from lightkurve import search_lightcurve

    lc = search_lightcurve("HAT-P-11", mission="Kepler",
                           cadence="long", quarter=10).download()
    jd.load(lc, format="Light Curve")
    jd.show()

.. seealso::

    :class:`~lcviz.loaders.importers.lightcurve.lightcurve.LightCurveImporter`
        API documentation for the Light Curve importer.
