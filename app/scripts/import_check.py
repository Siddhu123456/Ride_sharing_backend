"""Simple import-only check: walk the 'app' package and try to import every submodule.
Returns non-zero exit code on the first failure and prints failures.
"""
import pkgutil
import importlib
import sys

mods = list(pkgutil.walk_packages(['app'], prefix='app.'))
print('Scanned', len(mods), 'modules')
failures = []
for finder, name, ispkg in mods:
    try:
        importlib.import_module(name)
    except Exception as e:
        failures.append((name, e))

if failures:
    print('\nIMPORT FAILURES:')
    for m, e in failures:
        print(f"- {m}: {type(e).__name__}: {e}")
    sys.exit(1)

print('All imports succeeded')
