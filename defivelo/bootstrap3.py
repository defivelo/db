from django.forms.widgets import ChoiceWidget

from bootstrap3.renderers import FieldRenderer, InlineFieldRenderer
from bootstrap3.utils import add_css_class


class DvFieldRendererMixin:
    def get_form_group_class(self):
        """
        Override to avoid applying `required_css_class` on Selects with no empty choice
        """
        form_group_class = self.form_group_class
        if self.field.errors:
            if self.error_css_class:
                form_group_class = add_css_class(form_group_class, self.error_css_class)
        else:
            if self.field.form.is_bound:
                form_group_class = add_css_class(
                    form_group_class, self.success_css_class
                )
        widget = self.field.field.widget
        if (
            self.field.field.required
            and self.required_css_class
            and not (
                # `widget` is a non-multiple select with no empty value
                widget
                and isinstance(widget, ChoiceWidget)
                and not widget.allow_multiple_selected
                and all(
                    val not in self.field.field.empty_values
                    for val, _ in self.field.field.choices
                )
            )
        ):
            form_group_class = add_css_class(form_group_class, self.required_css_class)
        if self.layout == "horizontal":
            form_group_class = add_css_class(
                form_group_class, self.get_size_class(prefix="form-group")
            )
        return form_group_class


class DvFieldRenderer(DvFieldRendererMixin, FieldRenderer):
    pass


class DvInlineFieldRenderer(DvFieldRendererMixin, InlineFieldRenderer):
    pass
