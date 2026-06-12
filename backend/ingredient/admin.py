from django.contrib import admin

from attachment.models import AttachmentType
from utils.admin.attachment_form import AttachmentAdminForm

from .models import Ingredient, IngredientAlias, IngredientSuggestion


class IngredientAdminForm(AttachmentAdminForm):
    class Meta:
        model = Ingredient
        fields = "__all__"
        exclude = ["attachment", "owner", "updater"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        image = self.cleaned_data.get("image")

        if image:
            attachment = self.attachment_service.post_file(
                user=instance.owner,
                file=image,
                type=AttachmentType.FOOD,
            )
            instance.attachment = attachment

        if commit:
            instance.save()

        return instance


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    form = IngredientAdminForm
    search_fields = ["name"]
    list_display = ["name", "category"]
    list_filter = ["category"]


@admin.register(IngredientAlias)
class IngredientAliasAdmin(admin.ModelAdmin):
    search_fields = ["alias", "ingredient__name"]
    list_display = ["alias", "ingredient", "is_active", "created_at"]
    list_filter = ["is_active"]


@admin.register(IngredientSuggestion)
class IngredientSuggestionAdmin(admin.ModelAdmin):
    search_fields = ["suggested_name", "created_by__email"]
    list_display = ["suggested_name", "suggested_category", "status", "created_by", "created_at"]
    list_filter = ["status", "suggested_category"]
