from astropy.io.fits.card import Undefined
from traitlets import observe

from jdaviz.configs.default.plugins import MetadataViewer
from jdaviz.core.registries import tray_registry

__all__ = ['MetadataViewer']


# monkeypatch astropy.io.fits.card.Undefined to show an empty string
# instead of '<astropy.io.fits.card.Undefined object at 0x29f5b94d0>'
Undefined.__str__ = lambda x: ''


@tray_registry('lcviz-metadata-viewer', label="Metadata")
class MetadataViewer(MetadataViewer):
    """
    See the :ref:`Metadata Viewer Plugin Documentation <metadata-viewer>` for more details.

    Only the following attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    * ``dataset`` (:class:`~jdaviz.core.template_mixin.DatasetSelect`):
      Dataset to expose the metadata.
    * :attr:`show_primary` : bool
      Whether to show MEF primary header metadata instead.
    * :attr:`metadata`:
      Read-only metadata. If the data is loaded from a multi-extension FITS file,
      this can be the extension header or the primary header, depending on
      ``show_primary`` setting.

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @observe('vdocs')
    def _update_docs_link(self, *args):
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#metadata-viewer"  # noqa