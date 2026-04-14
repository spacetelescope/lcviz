# Licensed under a 3-clause BSD style license - see LICENSE.rst

try:
    from .version import version as __version__
except ImportError:
    __version__ = ''

from . import utils  # noqa
from .utils import enable_hot_reloading  # noqa: F401
from . import state  # noqa
from . import marks  # noqa: apply SliceIndicatorMarks patches early

# Expose subpackage API at package level.
from .plugins import *  # noqa
from .tools import *  # noqa
from .viewers import *  # noqa
from .helper import *  # noqa

from .loaders import *  # noqa
from .viewer_creators import *  # noqa

import jdaviz
from jdaviz import gca
from .helper import _apply_lcviz_patches

# Register lcviz patches with jdaviz's hook system so every App instance —
# including pre-existing ones and any created in the future — gets temporal-data support.
jdaviz._register_new_app_hook(lambda app: _apply_lcviz_patches(app._app))

jdaviz_app = gca()

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
