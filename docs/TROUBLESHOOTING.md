# Troubleshooting Guide

### 1. Build fails unable to find `liboqs`
**Error:** `ld: library not found for -loqs`
**Fix:** Ensure you initialized submodules and built `liboqs` correctly. Check that the `liboqs/build/lib/liboqs.a` exists, or modify the `CMakeLists.txt` library search paths if you installed `liboqs` via a package manager.

### 2. `ModuleNotFoundError: No module named 'aegis_engine'`
**Fix:** The pybind11 extension was not built, or not found in the PYTHONPATH. Make sure you run `cmake .. && make` inside the `build/` directory, and run Python from the project root (where the `.so` or `.dylib` file is generated), or add `build/` to your path.

### 3. Docker Compose build hangs
**Fix:** Compiling `liboqs` can take several minutes on slower machines. Be patient. Ensure Docker has at least 4GB of RAM allocated.

### 4. Ruff Linting Errors in `liboqs_src`
**Fix:** Upstream code (`liboqs_src`) should not be linted by our local tools. Ensure your `pyproject.toml` contains `exclude = ["liboqs_src", ".venv"]`.
