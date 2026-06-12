from typing import Optional

from django.forms import ClearableFileInput
from django.utils.safestring import mark_safe


class FileUrlWidget(ClearableFileInput):
    def __init__(
        self,
        url: Optional[str] = None,
        file_name: Optional[str] = None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.url = url
        self.file_name = file_name

    def render(self, name, value, attrs=None, renderer=None):
        html = ""

        if self.url and not value:
            html += f"""
                <div style="display: flex; flex-direction: column;">
                    {super().render(name, value, attrs, renderer)}
                    <a href="{self.url}" target="_blank">View {self.file_name}</a>
                </div>
            """
        else:
            html += super().render(name, value, attrs, renderer)
        return mark_safe(html)
