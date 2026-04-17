import numpy as np

from jdaviz.configs.default.plugins import Markers

__all__ = []

# Append lcviz time-series columns to whatever headers the base config provides.
# In deconfigged mode the base already includes value, value:unit, viewer, pixel_x/y, etc.
Markers._extra_headers = ['time', 'time:unit', 'phase', 'ephemeris', 'pixel']
Markers._extra_default_values = {
    'time': np.nan,
    'time:unit': '',
    'phase': np.nan,
    'ephemeris': '',
    'pixel': (np.nan, np.nan),
}

Markers._docs_link_fmt = (
    'https://lcviz.readthedocs.io/en/{vdocs}/plugins.html#markers'
)
