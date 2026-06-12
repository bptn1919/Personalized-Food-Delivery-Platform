from django.forms import FileField, ModelForm

from attachment.services import AttachmentService
from utils.admin.widgets import FileUrlWidget


class AttachmentAdminForm(ModelForm):
    image = FileField(required=False, label="Image")

    def __init__(self, *args, **kwargs):
        self.attachment_service = AttachmentService()
        super().__init__(*args, **kwargs)

        url = None
        file_name = None

        if (
            self.instance
            and self.instance.attachment
            and self.instance.attachment.public_url
        ):
            url = self.instance.attachment.public_url
            file_name = self.instance.attachment.original_name

        self.fields["image"].widget = FileUrlWidget(url=url, file_name=file_name)
