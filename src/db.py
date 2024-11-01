"""Concurrency-safe DB implementation for async code."""

import asyncio
from typing import Any, Protocol


class AsyncDB(Protocol):
    """Protocol for non-blocking database implementations."""

    async def get(self, key: str) -> Any: ...

    async def set(self, key: str, value: Any) -> None: ...

    async def delete(self, key: str) -> None: ...


class AsyncInMemoryDB(AsyncDB):
    """Concurrency-safe in-memory database implementation for async code."""

    def __init__(self) -> None:
        """Initialize the in-memory database."""
        self._data: dict[str, Any] = {}

        # Use asyncio.Lock for async compatible concurrency safety
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any:
        async with self._lock:
            return self._data.get(key, None)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._data[key] = value

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._data.pop(key, None)
