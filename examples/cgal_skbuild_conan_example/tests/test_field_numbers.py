from cgal_skbuild_conan_example import FieldNumber, Point, Polygon, PolygonWithHoles


def test_field_number():
    x1 = FieldNumber(1)
    x2 = FieldNumber(2)
    assert x1 + x2 == FieldNumber(3)
