.. _lcviz-loader-tpf:

*********************
Target Pixel File
*********************

Import a ``lightkurve`` target pixel file (TPF) object into jdaviz.

Overview
========

The TPF importer accepts a :class:`lightkurve.KeplerTargetPixelFile` or
:class:`lightkurve.TessTargetPixelFile` object and loads the pixel data into
the data collection. Optionally, an aperture photometry light curve can be
auto-extracted on load.

Usage
=====

.. code-block:: python

    import jdaviz as jd
    from lightkurve import search_targetpixelfile

    tpf = search_targetpixelfile("KIC 001429092",
                                 mission="Kepler",
                                 cadence="long",
                                 quarter=10).download()
    jd.load(tpf, format="TPF")
    jd.show()

.. seealso::

    :class:`~lcviz.loaders.importers.tpf.tpf.TPFImporter`
        API documentation for the TPF importer.

    :ref:`lcviz-photometric-extraction`
        The Photometric Extraction plugin for aperture photometry on loaded TPF data.
