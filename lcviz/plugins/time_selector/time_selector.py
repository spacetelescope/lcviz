from jdaviz.configs.cubeviz.plugins import Slice
from jdaviz.core.registries import tray_registry

from lcviz.viewers import CubeView

__all__ = ['TimeSelector']


@tray_registry('time-selector', label="Time Selector")
class TimeSelector(Slice):
    """
    See the :ref:`Time Selector Plugin Documentation <time-selector>` for more details.

    Only the following attributes and methods are available through the
    :ref:`public plugin API <plugin-apis>`:

    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.show`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.open_in_tray`
    * :meth:`~jdaviz.core.template_mixin.PluginTemplateMixin.close_in_tray`
    * ``value``  Time of the indicator.  When setting this directly, it will
      update automatically to the value corresponding to the nearest slice, if ``snap_to_slice`` is
      enabled and a cube is loaded.
    * ``show_indicator``
      Whether to show indicator in spectral viewer when slice tool is inactive.
    * ``show_value``
      Whether to show slice value in label to right of indicator.
    * ``snap_to_slice``
      Whether the indicator (and ``value``) should snap to the value of the nearest slice in the
      cube (if one exists).
    """
    _cube_viewer_cls = CubeView
    _cube_viewer_default_label = 'image'

    def __init__(self, *args, **kwargs):
        """

        """
        super().__init__(*args, **kwargs)
        self.docs_link = f"https://lcviz.readthedocs.io/en/{self.vdocs}/plugins.html#time-selector"
        self.docs_description = "Select time to sync across all viewers (as an indicator in all time/phase viewers or to select the active slice in any image/cube viewers).  The slice can also be changed interactively in any time viewer by activating the slice tool."  # noqa
        self.value_label = 'Time'
        self.value_unit = 'd'
        self.allow_disable_snapping = True

    @property
    def slice_axis(self):
        # global display unit "axis" corresponding to the slice axis
        return 'time'

    @property
    def valid_slice_att_names(self):
        return ["time", "dt"]

    @property
    def user_api(self):
        api = super().user_api
        # can be removed after deprecated upstream attributes for wavelength/wavelength_value
        # are removed in the lowest supported version of jdaviz
        api._expose = [e for e in api._expose if e not in ('slice', 'wavelength',
                                                           'wavelength_value', 'show_wavelength')]
        return api
