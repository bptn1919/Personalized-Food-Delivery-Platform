from typing import Annotated, Any, List, Optional, Union

from ninja import Field, Schema

from utils.enums import SortTypeEnum


IOptionalStr = Annotated[Optional[str], Field(None)]
IContainsField = Annotated[IOptionalStr, Field(None, q="__icontains")]


def FilterField(
    default: Any = None, q: Union[str, List[str], None] = None, *args, **kwargs
):
    return Field(default, q=q, *args, **kwargs)  # type: ignore


class OrderBySchema(Schema):
    order_by: str
    sort_type: SortTypeEnum = SortTypeEnum.DESC

    def get_order_by_expression(self):
        return (
            self.order_by if self.sort_type == SortTypeEnum.ASC else f"-{self.order_by}"
        )


__all__ = ["IOptionalStr", "IContainsField", "FilterField", "OrderBySchema"]
