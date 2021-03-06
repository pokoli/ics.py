import functools
import warnings
from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterator, List, MutableMapping, NewType, Optional, TYPE_CHECKING, Tuple, Union, cast, overload
from urllib.parse import ParseResult

import attr

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from ics.event import Event, CalendarEntryAttrs
    # noinspection PyUnresolvedReferences
    from ics.todo import Todo
    # noinspection PyUnresolvedReferences
    from ics.timespan import Timespan
    # noinspection PyUnresolvedReferences
    from ics.grammar import ContentLine, Container

__all__ = [
    "ContainerItem", "ContainerList", "URL",

    "DatetimeLike", "OptionalDatetimeLike",
    "TimedeltaLike", "OptionalTimedeltaLike",

    "TimespanOrBegin",
    "EventOrTimespan",
    "EventOrTimespanOrInstant",
    "TodoOrTimespan",
    "TodoOrTimespanOrInstant",
    "CalendarEntryOrTimespan",
    "CalendarEntryOrTimespanOrInstant",

    "get_timespan_if_calendar_entry",

    "RuntimeAttrValidation",

    "EmptyDict", "ExtraParams", "EmptyParams", "ContextDict", "EmptyContext", "copy_extra_params",
]

ContainerItem = Union["ContentLine", "Container"]
ContainerList = List[ContainerItem]
URL = ParseResult

DatetimeLike = Union[Tuple, Dict, datetime, date]
OptionalDatetimeLike = Union[Tuple, Dict, datetime, date, None]
TimedeltaLike = Union[Tuple, Dict, timedelta]
OptionalTimedeltaLike = Union[Tuple, Dict, timedelta, None]

TimespanOrBegin = Union[datetime, date, "Timespan"]
EventOrTimespan = Union["Event", "Timespan"]
EventOrTimespanOrInstant = Union["Event", "Timespan", datetime]
TodoOrTimespan = Union["Todo", "Timespan"]
TodoOrTimespanOrInstant = Union["Todo", "Timespan", datetime]
CalendarEntryOrTimespan = Union["CalendarEntryAttrs", "Timespan"]
CalendarEntryOrTimespanOrInstant = Union["CalendarEntryAttrs", "Timespan", datetime]


@overload
def get_timespan_if_calendar_entry(value: CalendarEntryOrTimespan) -> "Timespan":
    ...


@overload
def get_timespan_if_calendar_entry(value: datetime) -> datetime:
    ...


@overload
def get_timespan_if_calendar_entry(value: None) -> None:
    ...


def get_timespan_if_calendar_entry(value):
    from ics.event import CalendarEntryAttrs  # noqa: F811 # pyflakes considers this a redef of the unused if TYPE_CHECKING import above

    if isinstance(value, CalendarEntryAttrs):
        return value._timespan
    else:
        return value


@attr.s
class RuntimeAttrValidation(object):
    """
    Mixin that automatically calls the converters and validators of `attr` attributes.
    The library itself only calls these in the generated `__init__` method, with
    this mixin they are also called when later (re-)assigning an attribute, which
    is handled by `__setattr__`. This makes setting attributes as versatile as specifying
    them as init parameters and also ensures that the guarantees of validators are
    preserved even after creation of the object, at a small runtime cost.
    """

    def __attrs_post_init__(self):
        self.__post_init__ = True

    def __setattr__(self, key, value):
        if getattr(self, "__post_init__", None):
            cls = self.__class__  # type: Any
            if not getattr(cls, "__attr_fields__", None):
                cls.__attr_fields__ = attr.fields_dict(cls)
            try:
                field = cls.__attr_fields__[key]
            except KeyError:
                pass
            else:  # when no KeyError was thrown
                if field.converter is not None:
                    value = field.converter(value)
                if field.validator is not None:
                    field.validator(self, field, value)
        super(RuntimeAttrValidation, self).__setattr__(key, value)


class EmptyDictType(MutableMapping[Any, None]):
    """An empty, immutable dict that returns `None` for any key. Useful as default value for function arguments."""

    def __getitem__(self, k: Any) -> None:
        return None

    def __setitem__(self, k: Any, v: None) -> None:
        warnings.warn("%s[%r] = %s ignored" % (self.__class__.__name__, k, v))
        return

    def __delitem__(self, v: Any) -> None:
        warnings.warn("del %s[%r] ignored" % (self.__class__.__name__, v))
        return

    def __len__(self) -> int:
        return 0

    def __iter__(self) -> Iterator[Any]:
        return iter([])


EmptyDict = EmptyDictType()
ExtraParams = NewType("ExtraParams", Dict[str, List[str]])
EmptyParams = cast("ExtraParams", EmptyDict)
ContextDict = NewType("ContextDict", Dict[Any, Any])
EmptyContext = cast("ContextDict", EmptyDict)


def copy_extra_params(old: Optional[ExtraParams]) -> ExtraParams:
    new: ExtraParams = ExtraParams(dict())
    if not old:
        return new
    for key, value in old.items():
        if isinstance(value, str):
            new[key] = value
        elif isinstance(value, list):
            new[key] = list(value)
        else:
            raise ValueError("can't convert extra param %s with value of type %s: %s" % (key, type(value), value))
    return new


def attrs_custom_init(cls):
    assert attr.has(cls)
    attr_init = cls.__init__
    custom_init = cls.__attr_custom_init__

    @functools.wraps(attr_init)
    def new_init(self, *args, **kwargs):
        custom_init(self, attr_init, *args, **kwargs)

    cls.__init__ = new_init
    cls.__attr_custom_init__ = None
    del cls.__attr_custom_init__
    return cls

# @attrs_custom_init
# @attr.s
# class Test(object):
#     val1 = attr.ib()
#     val2 = attr.ib()
#
#     def __attr_custom_init__(self, attr_init, val1, val1_suffix, *args, **kwargs):
#         attr_init(self, val1 + val1_suffix, *args, **kwargs)
