from collections import OrderedDict
from typing import Any, Generic, List, Type, TypeVar

from django.core.paginator import Paginator
from ninja import Schema
from ninja.pagination import PaginationBase
from ninja_extra.pagination import paginate
from pydantic import BaseModel


T = TypeVar("T")


class PaginatedResponseSchema(BaseModel, Generic[T]):
    content: List[T]
    current_page: int
    page_size: int
    total_rows: int
    total_pages: int


class Pagination(PaginationBase):
    items_attribute: str = "content"
    page_query_param = "page"
    page_size_query_param = "page_size"

    class Input(Schema):
        page_size: int = 50
        page: int = 1

    def paginate_queryset(self, queryset: Any, pagination: Input, **params: Any):
        paginator = Paginator(queryset, pagination.page_size)

        total_pages = paginator.num_pages

        if int(total_pages) < pagination.page:
            page_number = pagination.page
            content = []
        else:
            current_page = paginator.page(pagination.page)
            page_number = current_page.number
            content = list(current_page)

        total = paginator.count

        return OrderedDict(
            [
                ("content", content),
                ("total_rows", total),
                ("total_pages", total_pages),
                ("current_page", page_number),
                ("page_size", pagination.page_size),
            ]
        )

    @classmethod
    def get_response_schema(cls, response_schema: Type[Schema]):
        return PaginatedResponseSchema[response_schema]  # type: ignore


paginate = paginate(Pagination)
