from functools import cached_property

import h5py

from jdaviz.core.loaders.parsers import BaseParser
from jdaviz.core.registries import loader_parser_registry


__all__ = ['HDF5Parser']


@loader_parser_registry('hdf5')
class HDF5Parser(BaseParser):

    def _check_is_valid(self):
        if self._app.config not in ('lcviz', 'deconfigged'):
            return f'hdf5 format is not supported in {self._app.config}.'
        self.output
        return ''

    @cached_property
    def output(self):
        return h5py.File(self.input, 'r')

    def _cleanup(self):
        if 'output' in self.__dict__:
            self.output.close()
            self._clear_cache('output')
