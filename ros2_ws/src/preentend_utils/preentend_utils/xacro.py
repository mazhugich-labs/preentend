"""Helpers for processing xacro descriptions."""

import xacro


def process_xacro(path, mappings=None):
    """Expand a xacro file into an XML description string."""
    return xacro.process_file(str(path), mappings=mappings or {}).toxml()
