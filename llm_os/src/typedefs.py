import typing as tp
from abc import ABC, abstractmethod

import typing_extensions as tpe
from openai import OpenAI

JSON: tpe.TypeAlias = dict[str, tp.Any]


class TypedDict(tpe.TypedDict): ...


T = tp.TypeVar("T", bound=TypedDict)


class Component(ABC, tp.Generic[T]):
    @abstractmethod
    def run(self, **kwargs: tpe.Unpack[T]) -> tp.Any:  # type:ignore
        ...


class TranscriberKwargs(TypedDict):
    stream: tp.Generator[bytes, None, None]
    client: OpenAI


class TerminalKwargs(TypedDict):
    content: str


class SpeakerKwargs(TerminalKwargs):
    client: OpenAI


ChatbotKwargs = SpeakerKwargs
