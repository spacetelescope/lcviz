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
