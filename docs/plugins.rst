*********************
Data Analysis Plugins
*********************

.. _metadata-viewer:

Metadata Viewer
===============

This plugin allows viewing of any metadata associated with the selected data.

If the data is loaded from multi-extension FITS that contains a primary header,
you will also see a :guilabel:`Show primary header` toggle, when enabled, would
display just the primary header metadata.

.. _plot-options:

Plot Options
============

This plugin gives access to per-viewer and per-layer plotting options.


.. _subset-tools:

Subset Tools
============

This plugin allows viewing and modifying defined subsets.


.. _markers:

Markers
=======

This plugin allows for interactively creating markers in any viewer and logging information about
the location of that marker along with the applicable data and viewer labels into a table.

With the plugin open in the tray, mouse over any viewer and press the "m" key to log the information
displayed in the app toolbar into the table.  The markers remain at that fixed pixel-position in
the viewer they were created (regardless of changes to the underlying data or linking) and are only
visible when the plugin is opened.


.. _flatten:

Flatten
=======

This plugin allows for flattening the light curve by removing trends.  By default, the resulting flattened light curve is
"unnormalized" by multiplying the flattened light curve by the median of the trend, but this
can be disabled through the plugin settings.

This plugin uses the following lightkurve implementations:

* :meth:`lightkurve.LightCurve.flatten`


.. _frequency_analysis:

Frequency Analysis
==================

This plugin exposes the periodogram (in period or frequency space) for an input light curve.

This plugin uses the following lightkurve implementations:

* :meth:`lightkurve.periodogram.LombScarglePeriodogram.from_lightcurve`
* :meth:`lightkurve.periodogram.BoxLeastSquaresPeriodogram.from_lightcurve`


.. _ephemeris:

Ephemeris
============

The ephemeris plugin allows for setting, finding, and refining the ephemeris or ephemerides used
for phase-folding.


.. _export-plot:

Export Plot
===========

This plugin allows exporting the plot in a given viewer to various image formats.
