"""Shared loader for the mock datasets (stands in for SCADA/EDI/ERP/news APIs)."""

import json
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")


def load(name):
    path = os.path.join(_DATA_DIR, f"{name}.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
