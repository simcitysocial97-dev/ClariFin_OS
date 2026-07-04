import os
import sys

# Add the backend source directory to the Python path so that imports like
# `import src.logger` resolve correctly when running tests from the project root.
backend_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "backend", "src"))
if backend_src_path not in sys.path:
    sys.path.insert(0, backend_src_path)