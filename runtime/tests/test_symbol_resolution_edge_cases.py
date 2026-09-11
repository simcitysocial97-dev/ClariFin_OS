import tempfile
from pathlib import Path

from runtime.foundation.verification.symbol_resolver import SymbolExtractor


def test_symbol_extraction_with_syntax_error():
    """Symbol extractor must gracefully handle files with syntax errors."""

    code = """
def valid_function():
    pass

def broken_function(
    # Missing closing paren - syntax error
    pass
"""

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        test_file = Path(f.name)

    try:
        extractor = SymbolExtractor()
        symbols = extractor.extract_from_file(test_file)

        assert isinstance(symbols, list)
    finally:
        test_file.unlink()


def test_symbol_extraction_with_deep_nesting():
    """Symbol extractor must handle deeply nested functions."""

    code = """
def level_1():
    def level_2():
        def level_3():
            def level_4():
                def level_5():
                    def level_6():
                        def level_7():
                            def level_8():
                                def level_9():
                                    def level_10():
                                        pass
"""

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        test_file = Path(f.name)

    try:
        extractor = SymbolExtractor()
        symbols = extractor.extract_from_file(test_file)

        function_names = [s.name for s in symbols]
        assert "level_1" in function_names
    finally:
        test_file.unlink()


def test_symbol_extraction_with_decorators():
    """Symbol extractor must handle decorated functions."""

    code = """
@decorator_one
@decorator_two
def decorated_function():
    pass

class MyClass:
    @property
    def my_property(self):
        pass

    @staticmethod
    def static_method():
        pass

    @classmethod
    def class_method(cls):
        pass
"""

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        test_file = Path(f.name)

    try:
        extractor = SymbolExtractor()
        symbols = extractor.extract_from_file(test_file)

        function_names = [s.name for s in symbols]

        assert "decorated_function" in function_names
        assert "MyClass" in function_names
        assert "my_property" in function_names
        assert "static_method" in function_names
        assert "class_method" in function_names
    finally:
        test_file.unlink()


def test_symbol_extraction_with_async_functions():
    """Symbol extractor must handle async def."""

    code = """
async def async_function():
    pass

class AsyncClass:
    async def async_method(self):
        pass
"""

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        test_file = Path(f.name)

    try:
        extractor = SymbolExtractor()
        symbols = extractor.extract_from_file(test_file)

        function_names = [s.name for s in symbols]

        assert "async_function" in function_names
        assert "async_method" in function_names
    finally:
        test_file.unlink()


def test_symbol_extraction_with_duplicate_names():
    """Symbol extractor must handle functions with same name in different scopes."""

    code = """
def duplicate():
    pass

class ClassA:
    def duplicate(self):
        pass

class ClassB:
    def duplicate(self):
        pass
"""

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        test_file = Path(f.name)

    try:
        extractor = SymbolExtractor()
        symbols = extractor.extract_from_file(test_file)

        duplicates = [s for s in symbols if s.name == "duplicate"]
        assert len(duplicates) == 3

        top_level = [s for s in duplicates if s.parent_class is None]
        in_class_a = [s for s in duplicates if s.parent_class == "ClassA"]
        in_class_b = [s for s in duplicates if s.parent_class == "ClassB"]

        assert len(top_level) == 1
        assert len(in_class_a) == 1
        assert len(in_class_b) == 1
    finally:
        test_file.unlink()


def test_symbol_extraction_with_lambdas():
    """Symbol extractor behavior with lambda functions."""

    code = """
regular_function = lambda x: x + 1

class MyClass:
    method = lambda self, x: x * 2
"""

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(code)
        test_file = Path(f.name)

    try:
        extractor = SymbolExtractor()
        symbols = extractor.extract_from_file(test_file)

        assert isinstance(symbols, list)
    finally:
        test_file.unlink()
