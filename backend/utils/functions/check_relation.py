from typing import List

from django.db.models import Model
from django.db.models.fields.related import ForeignObjectRel


def has_related_objects(instance: Model, exclude: List[str] = []) -> bool:
    for relation in instance._meta.get_fields():
        if not isinstance(relation, ForeignObjectRel):
            continue

        accessor_name = relation.get_accessor_name()
        if not isinstance(accessor_name, str):
            continue

        if accessor_name in exclude:
            continue

        if relation.one_to_one:
            related_object = getattr(instance, accessor_name, None)
            if related_object is not None:
                return True

        elif relation.one_to_many or relation.many_to_many:
            related_manager = getattr(instance, accessor_name, None)
            if related_manager and related_manager.exists():
                return True

    return False
