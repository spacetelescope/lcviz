.. _lcviz-loaders:

**************
Importing Data
**************

lcviz provides data loaders for light curve and target pixel file data from the Kepler, K2,
and TESS missions, injected into jdaviz at runtime alongside all built-in jdaviz loaders.

.. toctree::
   :maxdepth: 1

   light_curve
   tpf
   lightkurve_parser

.. grid:: 1

   .. grid-item-card:: Also includes jdaviz loaders
      :link: https://jdaviz.readthedocs.io/en/latest/loaders/index.html

      lcviz registers its loaders into jdaviz's unified loader registry alongside all
      built-in jdaviz sources and formats. See the jdaviz documentation for details on
      loading from files, URLs, and other sources.
