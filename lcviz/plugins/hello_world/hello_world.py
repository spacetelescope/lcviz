from jdaviz.core.registries import tray_registry
from jdaviz.core.template_mixin import PluginTemplateMixin, DatasetSelectMixin

__all__ = ['HelloWorldPlugin']


@tray_registry('HelloWorldPlugin', label="HelloWorldPlugin")
class HelloWorldPlugin(PluginTemplateMixin, DatasetSelectMixin):
    """ A Test plugin """
    template_file = __file__, "hello_world.vue"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
