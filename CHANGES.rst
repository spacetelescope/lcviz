0.4.3 (unreleased)
------------------

* bumps lightkurve to 2.5.0 to include upstream bug fixes. [#132]

* Improve scatter viewer and mouseover performance. [#137, #139]


0.4.2 (07.23.2024)
------------------

* Fix all docs links to point to correct version of read the docs. [#128]

* Update jdaviz requirement to 3.10.3 to include upstream bug fixes. [#130]

0.4.1 (07.15.2024)
------------------

* Max pin numpy to to exclude 2.0 until full compatibility can be supported. [#126]

* Fixes CDIPS support by handling columns filled with strings with empty units. [#122]

* Removes filepath from FILENAME entry in metadata. [#124]

0.4.0 (06-11-2024)
------------------

* Updates to use jdaviz 3.10, which now requires python 3.10+. [#105]

* Support loading, viewing, and slicing through TPF data cubes. [#82, #117, #118]

* Default data labels no longer include flux-origin, but do include quarter/campaign/sector. [#111]

* Basic stitch plugin to combine light curves into a single entry. [#107]

* Metadata plugin: show undefined entries as empty string instead of object repr. [#108]

* Raise error when parser can't identify file_obj [#106]

0.3.0 (04-05-2024)
--------------------

* Ability to create additional viewers. [#94]

* Updates to use jdaviz 3.9. [#68]

0.2.0 (02-26-2024)
------------------

* Clone viewer tool. [#74, #91]

* Flux column plugin to choose which column is treated as the flux column for each dataset. [#77]

* Flatten plugin no longer creates new data entries, but instead appends a new column to the input
  light curve and selects as the flux column (origin). [#77]

* Ephemeris plugin now supports passing floats to ``times_to_phases``. [#87]

* Ephemeris plugin's ``create_phase_viewer`` now returns the public user API instance of the viewer
  instead of the underlying object. [#87]

0.1.0 (12-14-2023)
------------------

* Initial release of lcviz with support to import time-series light curves via lightkurve and
  process them through binning, flattening, frequency analysis, and ephemeris plugins.
