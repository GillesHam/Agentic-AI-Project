"""Shared loader for the mock datasets (stands in for SCADA/EDI/ERP/news APIs).

Supports optional in-memory OVERRIDES so a UI can run alternative scenarios (e.g. a
different disruption or thinner inventory) without editing the JSON files on disk.
"""

import copy
import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")

# name -> dataset dict. If a name is present here, load() returns it instead of the file.
_OVERRIDES = {}


def set_overrides(mapping):
    global _OVERRIDES
    _OVERRIDES = mapping or {}


def clear_overrides():
    global _OVERRIDES
    _OVERRIDES = {}


def read_file(name):
    """Always read the on-disk fixture, ignoring any overrides."""
    path = os.path.join(_DATA_DIR, f"{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load(name):
    if name in _OVERRIDES:
        return copy.deepcopy(_OVERRIDES[name])
    return read_file(name)
