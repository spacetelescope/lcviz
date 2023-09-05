*******************
LCviz Documentation
*******************

``lcviz`` is a light curve visualization and analysis tool built on `Jdaviz <https://jdaviz.readthedocs.io>`_
and `lightkurve <https://docs.lightkurve.org>`_::

    from lcviz import LCviz
    from lightkurve import search_lightcurve

    lc = search_lightcurve("HAT-P-11", mission="Kepler",
                           cadence="long", quarter=10).download()

    lcviz = LCviz()
    lcviz.load_data(lc)
    lcviz.show()


Although ``lcviz`` does implement convenient UI access to ``lightkurve`` functionality, it does not
aim to be a complete ``lightkurve`` UI, nor is it limited to only features supported by ``lightkurve``.

Reference/API
=============

.. toctree::
   :maxdepth: 2

   installation.rst
   plugins.rst
   reference/api.rst
