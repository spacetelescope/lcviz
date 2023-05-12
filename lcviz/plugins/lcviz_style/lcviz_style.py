from ipyvuetify import VuetifyTemplate

__all__ = ['StyleWidget']


class StyleWidget(VuetifyTemplate):
    template_file = __file__, "lcviz_style.vue"
