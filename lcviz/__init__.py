# Licensed under a 3-clause BSD style license - see LICENSE.rst

try:
    from .version import version as __version__
except ImportError:
    __version__ = ''

from . import utils  # noqa
from .utils import enable_hot_reloading  # noqa: F401
from . import state  # noqa

# Expose subpackage API at package level.
from .plugins import *  # noqa
from .parsers import *  # noqa
from .tools import *  # noqa
from .viewers import *  # noqa
from .helper import *  # noqa

from .loaders import *  # noqa
from .viewer_creators import *  # noqa

from jdaviz import gca

jdaviz_app = gca()
# inject loaders/plugins into the jdaviz deconfigged app
jdaviz_app.app.update_tray_items_from_registry()
jdaviz_app.app.update_loaders_from_registry()
jdaviz_app.app.update_new_viewers_from_registry()

# redirect top-level calls to the deconfigged jdaviz app
_expose = ['show', 'load', 'batch_load',
           'toggle_api_hints',
           'plugins',
           'loaders',
           'viewers']
_incl = ['App', 'enable_hot_reloading', '__version__']
_temporary_incl = ['LCviz']
__all__ = _expose + _incl + _temporary_incl


def __dir__():
    return sorted(__all__)
