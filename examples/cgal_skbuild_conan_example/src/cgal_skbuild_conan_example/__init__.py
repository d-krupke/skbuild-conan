"""
This package just show cases how to use CGAL with PyBind11 with the help of skbuild_conan.
"""

# ._cgal_bindings will only exist after compilation.
from ._cgal_bindings import FieldNumber, Point, Polygon, PolygonWithHoles

__all__ = ["FieldNumber", "Point", "Polygon", "PolygonWithHoles"]
