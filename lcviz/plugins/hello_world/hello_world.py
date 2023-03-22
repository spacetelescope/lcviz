from traitlets import Bool, List, observe

from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import PluginTemplateMixin, DatasetSelectMixin
from jdaviz.core.user_api import PluginUserApi
from jdaviz.utils import PRIHDR_KEY, COMMENTCARD_KEY

__all__ = ['HelloWorldPlugin']


@tray_registry('HelloWorldPlugin', label="HelloWorldPlugin")
class HelloWorldPlugin(PluginTemplateMixin, DatasetSelectMixin):
    """ A Test plugin """
    template_file = __file__, "hello_world.vue"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
