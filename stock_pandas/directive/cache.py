from typing import (
    Dict,
    Optional
)
from .types import Directive


# A simple cache
class DirectiveCache:
    _store: Dict[str, Directive]

    def __init__(self) -> None:
        self._store = {}

    def set(
        self,
        key: str,
        value: Directive
    ) -> Directive:
        self._store[key] = value
        return value

    def get(
        self,
        key: str
    ) -> Optional[Directive]:
        return self._store.get(key)
