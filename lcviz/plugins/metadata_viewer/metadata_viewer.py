from astropy.io.fits.card import Undefined

from jdaviz.configs.default.plugins import MetadataViewer

__all__ = []

# monkeypatch astropy.io.fits.card.Undefined to show an empty string
# instead of '<astropy.io.fits.card.Undefined object at 0x29f5b94d0>'
Undefined.__str__ = lambda x: ''

# Set lcviz-specific docs link without subclassing MetadataViewer.
MetadataViewer._docs_link_fmt = (
    'https://lcviz.readthedocs.io/en/{vdocs}/plugins.html#metadata-viewer'
)