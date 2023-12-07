# Licensed under a 3-clause BSD style license - see LICENSE.rst

import os
from astropy.tests.runner import TestRunner

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

# Create the test function for self test
test = TestRunner.make_test_runner_in(os.path.dirname(__file__))
