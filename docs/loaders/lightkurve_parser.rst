.. _lcviz-loader-lightkurve-parser:

*****************
lightkurve.read()
*****************

Parse files directly using ``lightkurve.read`` as a jdaviz file format parser.

Overview
========

The ``lightkurve.read`` parser allows loading any file format supported by
:func:`lightkurve.read` (Kepler, K2, TESS FITS files, etc.) through jdaviz's
file-based loaders (file path, URL, file drop).

Usage
=====

.. code-block:: python

    import jdaviz as jd

    # Load a FITS light curve file directly
    jd.load("mytpf.fits", format="lightkurve.read")
    jd.show()

.. seealso::

    :class:`~lcviz.loaders.parsers.lightkurve.LightkurveParser`
        API documentation for the lightkurve parser.

    :func:`lightkurve.read`
        lightkurve documentation on supported file formats.
