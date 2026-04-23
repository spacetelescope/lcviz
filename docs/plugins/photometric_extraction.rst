.. _lcviz-photometric-extraction:

************************
Photometric Extraction
************************

Extract a light curve from target pixel file (TPF) data via aperture photometry.

Overview
========

This plugin is only available if TPF data is loaded into the app.

UI Access
=========

.. wireframe-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action": "show-sidebar", "value": "plugins", "delay": 1500, "caption": "Open the plugin toolbar"}, {"action": "open-panel", "value": "Photometric Extraction", "delay": 1000, "caption": "Open the Photometric Extraction plugin"}]

User API
========

.. admonition:: User API Example
    :class: dropdown

    See the :class:`~lcviz.plugins.photometric_extraction.photometric_extraction.PhotometricExtraction` user API documentation for more details.

    .. code-block:: python

      import jdaviz as jd
      from lightkurve import search_targetpixelfile
      tpf = search_targetpixelfile("KIC 001429092",
                                   mission="Kepler",
                                   cadence="long",
                                   quarter=10).download()
      jd.load(tpf, format="TPF")
      jd.show()

      ext = jd.plugins['Photometric Extraction']
      ext.open_in_tray()

.. seealso::

    This plugin uses the following ``lightkurve`` implementations:

    * :meth:`lightkurve.KeplerTargetPixelFile.extract_aperture_photometry`
