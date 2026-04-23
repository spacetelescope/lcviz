.. _lcviz-viewer-tpf:

**********
TPF Viewer
**********

Display a Target Pixel File (TPF) as a 2-D image that is linked to the
time axis of any loaded light curves.

Overview
========

The TPF viewer renders
each cadence of a :class:`~lightkurve.KeplerTargetPixelFile` or
:class:`~lightkurve.TessTargetPixelFile` as a 2-D pixel image.  The displayed
cadence is controlled by the shared time slice indicator that is kept in sync
with the Flux vs Time viewer.

A TPF viewer is created automatically when a TPF is loaded.  Additional
TPF viewers can be added via the *TPF* entry in the Viewer Creator
controls, which is only shown when TPF data is present in the app.

UI Access
=========

.. wireframe-demo:: _static/jdaviz-wireframe.html
   :js: jdaviz-wireframe-actions.js
   :css: jdaviz-wireframe.css
   :repeat: false
   :steps-json: [{"action": "show-sidebar", "value": "loaders", "delay": 1500, "caption": "Open the data loader"}, {"action": "select-tab", "value": "Viewer", "delay": 1500, "caption": "Select the Viewer tab"}, {"action": "select-dropdown", "value": "Viewer Type:TPF", "delay": 1500, "caption": "Set viewer type to TPF"}]

API Access
==========

.. code-block:: python

    import jdaviz as jd
    from lightkurve import search_targetpixelfile

    tpf = search_targetpixelfile("KIC 001429092",
                                 mission="Kepler",
                                 cadence="long",
                                 quarter=10).download()
    jd.load(tpf, format="TPF")
    jd.show()

    # Access the TPF viewer
    iv = jd.viewers['TPF']

    # Create an additional TPF viewer via the viewer creator
    vc = jd.new_viewers['TPF']
    new_viewer = vc()

.. seealso::

    :class:`~lcviz.viewers.CubeView`
        API documentation for the TPF viewer.

    :ref:`lcviz-photometric-extraction`
        The Photometric Extraction plugin for extracting light curves from a TPF.
