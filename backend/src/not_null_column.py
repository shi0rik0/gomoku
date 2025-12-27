from functools import wraps
from typing import TYPE_CHECKING, Any, Literal, Optional, Union, overload

from sqlalchemy import Column
from sqlalchemy.sql.schema import SchemaConst

if TYPE_CHECKING:
    from sqlalchemy.sql.schema import Column as _Column
    from sqlalchemy.types import TypeEngine


@overload
def NotNullColumn(
    name: str,
    type_: "TypeEngine[Any]",
    *args: Any,
    autoincrement: Union[bool, Literal["auto", "ignore_fk"]] = "auto",
    default: Any = ...,
    index: Optional[bool] = ...,
    unique: Optional[bool] = ...,
    info: Optional[dict] = ...,
    nullable: bool = False,
    onupdate: Any = ...,
    primary_key: bool = ...,
    server_default: Any = ...,
    comment: Optional[str] = ...,
    **kwargs: Any,
) -> "_Column[Any]": ...


@overload
def NotNullColumn(
    *args,
    **kwargs,
): ...


# 实际实现
@wraps(Column)
def NotNullColumn(*args: Any, **kwargs: Any) -> Any:
    """
    默认 nullable=False 的 Column，保留完整类型提示
    """
    if "nullable" not in kwargs:
        kwargs["nullable"] = False
    return Column(*args, **kwargs)
