from functools import cached_property
from lightkurve import read as lkread

from jdaviz.core.loaders.parsers import BaseParser
from jdaviz.core.registries import loader_parser_registry


__all__ = ['LightkurveParser']


@loader_parser_registry('lightkurve.read')
class LightkurveParser(BaseParser):

    @property
    def is_valid(self):
        if self.app.config not in ('deconfigged', 'lcviz'):
            # NOTE: temporary during deconfig process
            return False
        try:
            self.output
        except Exception:
            return False
        return True

    @cached_property
    def output(self):
        return lkread(self.input)
