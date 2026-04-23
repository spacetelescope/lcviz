.. _lcviz-frequency-analysis:

******************
Frequency Analysis
******************

Compute periodograms in period or frequency space for a light curve.

Overview
========

This plugin exposes the periodogram (in period or frequency space) for an input light curve.

UI Access
=========

.. wireframe-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action": "show-sidebar", "value": "plugins", "delay": 1500, "caption": "Open the plugin toolbar"}, {"action": "open-panel", "value": "Frequency Analysis", "delay": 1000, "caption": "Open the Frequency Analysis plugin"}]

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.frequency_analysis.frequency_analysis.FrequencyAnalysis` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_lightcurve
      lc = search_lightcurve("HAT-P-11", mission="Kepler",
                             cadence="long", quarter=10).download().flatten()
      jd.load(lc, format="Light Curve")
      jd.show()

      freq = jd.plugins['Frequency Analysis']
      freq.open_in_tray()
      freq.method = 'Lomb-Scargle'
      freq.xunit = 'period'
      periodogram = freq.periodogram
      print(periodogram)

.. seealso::

    This plugin uses the following ``lightkurve`` implementations:

    * :meth:`lightkurve.periodogram.LombScarglePeriodogram.from_lightcurve`
    * :meth:`lightkurve.periodogram.BoxLeastSquaresPeriodogram.from_lightcurve`
