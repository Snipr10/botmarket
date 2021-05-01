from django.forms import widgets
from django.template.defaultfilters import register


class ReadonlyTextWidget(widgets.TextInput):
    template_name = 'admin/widgets/readonly_text.html'


@register.filter(name='instance_of_tuple')
def instance_of_tuple(value):
    """
    Return isinstance value of tuple
    :param value:
    :return: bool
    """
    if isinstance(value, tuple):
        return True
    return False
