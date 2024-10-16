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

    async def test_update_existing_key(self, db: AsyncInMemoryDB) -> None:
        """Test updating an existing key in the database."""

        await db.set("key1", "initial_value")
        await db.update("key1", "updated_value")
        async with db._lock:
            assert db._data["key1"] == "updated_value"

    async def test_update_nonexistent_key(self, db: AsyncInMemoryDB) -> None:
        """Test that updating a non-existent key raises a KeyError."""

        with pytest.raises(KeyError, match="Key key1 not found in the database"):
            await db.update("key1", "new_value")

    async def test_delete_existing_key(self, db: AsyncInMemoryDB) -> None:
        """Test deleting an existing key."""

        await db.set("key1", "value1")
        await db.delete("key1")
        async with db._lock:
            assert "key1" not in db._data

    async def test_delete_nonexistent_key(self, db: AsyncInMemoryDB) -> None:
        """Test that deleting a non-existent key raises a KeyError."""

        with pytest.raises(KeyError, match="Key key1 not found in the database"):
            await db.delete("key1")
