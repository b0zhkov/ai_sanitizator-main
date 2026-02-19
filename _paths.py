"""
This file is responsible for adding all necessary directories to sys.path,
instead of adding them to each file that needs to import from another directory.
"""
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

_DIRS = [
    _PROJECT_ROOT,
    os.path.join(_PROJECT_ROOT, 'text-analysis'),
    os.path.join(_PROJECT_ROOT, 'text-rewriting'),
    os.path.join(_PROJECT_ROOT, 'text_sanitization'),
]

for _d in _DIRS:
    if _d not in sys.path:
        sys.path.insert(0, _d)
