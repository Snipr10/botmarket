from django import forms

from .widgets import ReadonlyTextWidget


class DynamicDataFieldsFormMixin:
    """Allows to create readonly fields dynamically.
    Just pass it a dict called data_fields:
    data_fields = {
        'field_name': data,
    }
    """

    def __init__(self, data_fields=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if data_fields is None:
            return

        for field_name, value in data_fields.items():
            self.fields[field_name] = forms.CharField(disabled=True, widget=ReadonlyTextWidget, initial=value)


class DataDisplayForm(DynamicDataFieldsFormMixin, forms.Form):
    pass
