"""Test suite for the db module."""

import asyncio
from typing import Any

import pytest

from src.db import AsyncInMemoryDB


class TestAsyncInMemoryDB:
    """Test suite for the AsyncInMemoryDB class."""

    @pytest.fixture
    async def db(self) -> AsyncInMemoryDB:
        """Fixture to provide a fresh instance of AsyncInMemoryDB for each test."""
        return AsyncInMemoryDB()

    async def test_set(self, db: AsyncInMemoryDB) -> None:
        """Test setting a value in the database."""
        await db.set("key1", "value1")
        async with db._lock:  # Access _data for verification
            assert "key1" in db._data
            assert db._data["key1"] == "value1"

    async def test_get_existing_key(self, db: AsyncInMemoryDB) -> None:
        """Test getting a value for an existing key in the database."""
        async with db._lock:
            db._data["key1"] = "value1"  # Directly set a value to simulate existing key
        result = await db.get("key1")
        assert result == "value1"

    async def test_get_nonexistent_key(self, db: AsyncInMemoryDB) -> None:
        """Test getting a value for a non-existent key returns None."""
        result = await db.get("nonexistent")
        assert result is None

    async def test_delete_existing_key(self, db: AsyncInMemoryDB) -> None:
        """Test deleting an existing key."""
        await db.set("key1", "value1")
        await db.delete("key1")
        async with db._lock:
            assert "key1" not in db._data

    async def test_delete_nonexistent_key(self, db: AsyncInMemoryDB) -> None:
        """Test that deleting a non-existent key doesn't raise any KeyError."""
        await db.delete("key1")

    async def test_concurrent_access(self, db: AsyncInMemoryDB) -> None:
        """Test that the database is safe for concurrent access."""

        async def read_write_task(key: str, value: Any) -> None:
            await db.set(key, value)
            read_value = await db.get(key)
            assert read_value == value, f"Expected {value}, but got {read_value}"

        async def delete_task(key: str) -> None:
            await db.delete(key)
            result = await db.get(key)
            assert result is None, f"Expected None, but got {result}"

        async def run_concurrent_tasks() -> None:
            async with asyncio.TaskGroup() as tg:
                # Concurrent writes
                tg.create_task(read_write_task("key1", "value1"))
                tg.create_task(read_write_task("key2", "value2"))

                # Concurrent updates
                tg.create_task(read_write_task("key3", "initial"))

                # Concurrent deletes
                tg.create_task(read_write_task("key4", "to_be_deleted"))
                tg.create_task(delete_task("key4"))

        # First, test concurrent access
        await run_concurrent_tasks()

        # Validate that no data persists after deletion
        assert await db.get("key4") is None, "Expected key4 to be deleted"
