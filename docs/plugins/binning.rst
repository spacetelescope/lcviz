.. _lcviz-binning:

*******
Binning
*******

Bin a light curve in time or phase-space.

Overview
========

This plugin combines light-curve samples into bins to reduce the number of points
and make trends easier to see. Select the input light curve with **Data**, then
choose whether to bin in time or phase using **Ephemeris** (only available if at least
one ephemeris has been created).

Time binning: No ephemeris
-------------------------

With **Ephemeris** set to **No ephemeris** (the default), samples are grouped by
their observation times. **N Bins** sets the bin width by dividing the full input
time span by the requested number of bins.

The live preview shows the time-binned light curve in the time viewer and its
phase-folded appearance in existing phase viewers.

Phase binning: Selecting an ephemeris
------------------------------------

Select an ephemeris defined in the :ref:`Ephemeris plugin <lcviz-ephemeris>` to
fold the input light curve before binning. This is useful for
showing the average shape of a repeating signal rather than its cycle-to-cycle
variations.

In this mode, **N Bins** divides the input's phase span rather than its time span.
The live preview appears only in phase viewers using the selected ephemeris, and
the output viewer selector offers those matching phase viewers.

The output is a phase-binned light curve tied to the selected ephemeris, not a
time-binned record of the original observations. Its representative times are
derived from the binned phases using that ephemeris; they do not preserve the
individual observation times from all contributing cycles.


UI Access
=========

.. guidestar-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action": "show-sidebar", "value": "plugins", "delay": 1500, "caption": "Open the plugin toolbar"}, {"action": "open-panel", "value": "Binning", "delay": 1000, "caption": "Open the Binning plugin"}]

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.binning.binning.Binning` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      import lcviz
      from lightkurve import search_lightcurve
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      jd.load(lc, format="Light Curve")
      jd.show()

      binning = jd.plugins['Binning']
      binning.n_bins = 150
      binned_lc = binning.bin(add_data=True)
      print(binned_lc)

.. seealso::

    This plugin uses the following ``lightkurve`` implementations:

    * :meth:`lightkurve.LightCurve.bin`
    * :meth:`lightkurve.FoldedLightCurve.bin`
