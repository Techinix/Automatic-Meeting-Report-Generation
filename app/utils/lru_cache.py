"""
LRU Cache implementation.
"""

from collections import OrderedDict
from typing import Any, Dict, Optional, TypeVar, Union, overload

_T = TypeVar("_T")


class LRUCache(OrderedDict[str, Dict[str, Any]]):
    """Least Recently Used (LRU) cache."""

    def __init__(self, capacity: int):
        super().__init__()
        self._capacity = capacity

    @overload
    def get(self, key: str) -> Optional[Dict[str, Any]]: ...

    @overload
    def get(
        self, key: str, default: Union[Dict[str, Any], _T]
    ) -> Union[Dict[str, Any], _T]: ...

    def get(self, key: str, default: Any = None) -> Any:
        """Get an item and mark it as recently used."""
        if key not in self:
            return default
        self.move_to_end(key)
        return self[key]

    def put(self, key: str, value: Dict[str, Any]) -> None:
        self[key] = value
        self.move_to_end(key)
        if len(self) > self._capacity:
            self.popitem(last=False)
