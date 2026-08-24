"""Backend conftest.py — loads test fixtures for pytest 9.x compatibility."""

pytest_plugins = [
    "tests.fixtures.pytest_config",
    "tests.fixtures.hypothesis",
    "tests.fixtures.database",
    "tests.fixtures.seed",
    "tests.fixtures.client",
    "tests.fixtures.builders",
    "tests.fixtures.factories",
]
