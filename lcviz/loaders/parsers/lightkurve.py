from functools import cached_property
from lightkurve import read as lkread

from jdaviz.core.loaders.parsers import BaseParser
from jdaviz.core.registries import loader_parser_registry


__all__ = ['LightkurveParser']


@loader_parser_registry('lightkurve.read')
class LightkurveParser(BaseParser):

    def _check_is_valid(self):
        if self._app.config not in ('lcviz', 'deconfigged'):
            return f'lightkurve.read format is not supported in {self._app.config}.'
        self.output
        return ''

    @cached_property
    def output(self):
        return lkread(self.input)
