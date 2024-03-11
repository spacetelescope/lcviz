*********************
Data Analysis Plugins
*********************

.. _metadata-viewer:

Metadata Viewer
===============

This plugin allows viewing of any metadata associated with the selected data.


.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.metadata_viewer.metadata_viewer.MetadataViewer` user API documentation for more details.

    .. code-block:: python

      from lcviz import LCviz
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      lcviz = LCviz()
      lcviz.load_data(lc)
      lcviz.show()

      metadata = lcviz.plugins['Metadata']
      print(f"dataset choices: {metadata.dataset.choices}")
      metadata.dataset = metadata.dataset.choices[0]
      print(metadata.metadata)
      

.. seealso::

    :ref:`Jdaviz Metadata Viewer <jdaviz:imviz_metadata-viewer>`
        Jdaviz documentation on the Metadata Viewer plugin.

.. _flux-column:

Flux Column
===========

This plugin allows choosing which column in the underlying data should be used as the flux column
(origin) throughout the app (when plotting and in any data analysis plugins).


.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.flux_column.flux_column.FluxColumn` user API documentation for more details.

    .. code-block:: python

      from lcviz import LCviz
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      lcviz = LCviz()
      lcviz.load_data(lc)
      lcviz.show()

      flux_col = lcviz.plugins['Flux Column']
      print(flux_col.flux_column.choices)
      flux_col.flux_column = 'sap_flux'


.. seealso::

    This plugin reproduces the behavior also available in ``lightkurve`` as:

    * :meth:`lightkurve.LightCurve.select_flux`


.. _plot-options:

Plot Options
============

This plugin gives access to per-viewer and per-layer plotting options.


.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.plot_options.plot_options.PlotOptions` user API documentation for more details.

    .. code-block:: python

      from lcviz import LCviz
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      lcviz = LCviz()
      lcviz.load_data(lc)
      lcviz.show()

      po = lcviz.plugins['Plot Options']
      print(f"viewer choices: {po.viewer.choices}")
      po.viewer = po.viewer.choices[0]
      print(f"layer choices: {po.layer.choices}")
      po.layer = po.layer.choices[0]

      po.marker_size = 4
      po.marker_color = 'blue'


.. seealso::

    :ref:`Jdaviz Plot Options <jdaviz:imviz-plot-options>`
        Jdaviz documentation on the Plot Options plugin.

.. _subset-tools:

Subset Tools
============

This plugin allows viewing and modifying defined subsets.

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.subset_plugin.subset_plugin.SubsetPlugin` user API documentation for more details.

    .. code-block:: python

      from lcviz import LCviz
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      lcviz = LCviz()
      lcviz.load_data(lc)
      lcviz.show()

      subset_tools = lcviz.plugins['Subset Tools']
      subset_tools.open_in_tray()


.. seealso::

    :ref:`Jdaviz Subset Tools <jdaviz:imviz-subset-plugin>`
        Jdaviz documentation on the Subset Tools plugin.

.. _markers:

Markers
=======

This plugin allows for interactively creating markers in any viewer and logging information about
the location of that marker along with the applicable data and viewer labels into a table.

With the plugin open in the tray, mouse over any viewer and press the "m" key to log the information
displayed in the app toolbar into the table.  The markers remain at that fixed pixel-position in
the viewer they were created (regardless of changes to the underlying data or linking) and are only
visible when the plugin is opened.


.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.markers.markers.Markers` user API documentation for more details.

    .. code-block:: python

      from lcviz import LCviz
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      lcviz = LCviz()
      lcviz.load_data(lc)
      lcviz.show()

      markers = lcviz.plugins['Markers']
      markers.open_in_tray()
      # interactively mark by mousing over the viewer and pressing "M"
      table = markers.export_table()
      print(table)
      markers.clear_table()


.. seealso::

    :ref:`Jdaviz Markers <jdaviz:markers-plugin>`
        Jdaviz documentation on the Markers plugin.


.. _flatten:

Flatten
=======

This plugin allows for flattening the light curve by removing trends.  By default, the resulting flattened light curve is
"unnormalized" by multiplying the flattened light curve by the median of the trend, but this
can be disabled through the plugin settings.

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.flatten.flatten.Flatten` user API documentation for more details.

    .. code-block:: python

      from lcviz import LCviz
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download()
      lcviz = LCviz()
      lcviz.load_data(lc)
      lcviz.show()

      flatten = lcviz.plugins['Flatten']
      flatten.open_in_tray()
      flatten.polyorder = 4
      flattened_lc = flatten.flatten(add_data=True)
      print(flattened_lc)


.. seealso::

    This plugin uses the following ``lightkurve`` implementations:

    * :meth:`lightkurve.LightCurve.flatten`


.. _frequency_analysis:

Frequency Analysis
==================

This plugin exposes the periodogram (in period or frequency space) for an input light curve.


.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.frequency_analysis.frequency_analysis.FrequencyAnalysis` user API documentation for more details.

    .. code-block:: python

      from lcviz import LCviz
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      lcviz = LCviz()
      lcviz.load_data(lc)
      lcviz.show()
      
      freq = lcviz.plugins['Frequency Analysis']
      freq.open_in_tray()
      freq.method = 'Lomb-Scargle'
      freq.xunit = 'period'
      periodogram = freq.periodogram
      print(periodogram)


.. seealso::

    This plugin uses the following ``lightkurve`` implementations:

    * :meth:`lightkurve.periodogram.LombScarglePeriodogram.from_lightcurve`
    * :meth:`lightkurve.periodogram.BoxLeastSquaresPeriodogram.from_lightcurve`


.. _ephemeris:

Ephemeris
==========

The ephemeris plugin allows for setting, finding, and refining the ephemeris or ephemerides used
for phase-folding.


.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.ephemeris.ephemeris.Ephemeris` user API documentation for more details.

    .. code-block:: python

      from lcviz import LCviz
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      lcviz = LCviz()
      lcviz.load_data(lc)
      lcviz.show()

      ephem = lcviz.plugins['Ephemeris']
      ephem.period = 4.88780258
      ephem.t0 = 2.43
      ephem.rename_component('default', 'my component name')


.. _binning:

Binning
=======

This plugin supports binning a light curve in time or phase-space.


.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.binning.binning.Binning` user API documentation for more details.

    .. code-block:: python

      from lcviz import LCviz
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      lcviz = LCviz()
      lcviz.load_data(lc)
      lcviz.show()

      binning = lcviz.plugins['Binning']
      binning.n_bins = 150
      binned_lc = binning.bin(add_data=True)
      print(binned_lc)


.. seealso::

  This plugin uses the following ``lightkurve`` implementations:

  * :meth:`lightkurve.LightCurve.bin`


.. _export:

Export
======

This plugin allows exporting the plot in a given viewer to various image formats.


.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.export.export.Export` user API documentation for more details.

    .. code-block:: python

      from lcviz import LCviz
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      lcviz = LCviz()
      lcviz.load_data(lc)
      lcviz.show()

      export = lcviz.plugins['Export']
      export.export('test.png')


.. seealso::

    :ref:`Jdaviz Export Plot <jdaviz:imviz-export-plot>`
        Jdaviz documentation on the Export plugin.
