.. _lcviz-plugins:

*********************
Data Analysis Plugins
*********************

lcviz provides data analysis plugins for light curve visualization and analysis.
These plugins are injected into jdaviz at runtime and are available alongside
all built-in jdaviz plugins.

.. toctree::
   :maxdepth: 1

   metadata_viewer
   flux_column
   plot_options
   subset_tools
   markers
   time_selector
   photometric_extraction
   stitch
   flatten
   frequency_analysis
   ephemeris
   binning
   export

.. grid:: 1

   .. grid-item-card:: Also includes jdaviz plugins
      :link: https://jdaviz.readthedocs.io/en/latest/plugins/index.html

      lcviz loads all jdaviz built-in analysis plugins in addition to the
      lcviz-specific plugins listed above. See the jdaviz documentation for
      details on plugins such as Model Fitting, Line Analysis, and more.
