.. |lcviz_logo| image:: ./logos/lcviz_icon.svg
    :height: 42px


******************
|lcviz_logo| lcviz
******************

``lcviz`` is a light curve visualization and analysis tool within the Jupyter environment (lab or 
notebook), built on top of `Jdaviz <https://jdaviz.readthedocs.io>`_ and `lightkurve <https://docs.lightkurve.org>`_::

    from lcviz import LCviz
    from lightkurve import search_lightcurve

    lc = search_lightcurve("HAT-P-11", mission="Kepler",
                           cadence="long", quarter=10).download()

    lcviz = LCviz()
    lcviz.load_data(lc)
    lcviz.show()

It aims to provide tools for the analysis of periodic and semi-periodic variability from
stationary sources (exoplanets, eclipsing binaries, ellipsoidal variables, pulsating stars,
rotating stars, etc) in high-cadence photometric data sets, specifically - but not limited to - Kepler, K2, and TESS.

Although ``lcviz`` implements convenient UI access to functionality from the ``lightkurve`` python
package, it does not aim to be a complete ``lightkurve`` UI, nor is it limited to only features
supported by ``lightkurve``.

Reference/API
=============

.. toctree::
   :maxdepth: 2

   installation.rst
   plugins.rst
   reference/api.rst
