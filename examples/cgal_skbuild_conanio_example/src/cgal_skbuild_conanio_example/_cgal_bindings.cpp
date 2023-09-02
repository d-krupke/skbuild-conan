
// pybind11
#include <pybind11/operators.h> // to define operator overloading
#include <pybind11/pybind11.h>  // basic pybind11 functionality
#include <pybind11/stl.h>       // automatic conversion of vectors
// cgal
#include <CGAL/Boolean_set_operations_2.h>
#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/Point_2.h>
#include <CGAL/Polygon_2.h>
#include <CGAL/Polygon_with_holes_2.h>
// fmt
#include <fmt/core.h>

// Getting this name right is important! It has to equal the name in the
// CMakeLists.txt.
PYBIND11_MODULE(_cgal_bindings, m) {
  namespace py = pybind11;
  m.doc() = "Example of PyBind11 and CGAL."; // optional module docstring

  // Define CGAL types
  using Kernel = CGAL::Epeck; // Exact Predicates Exact Constructions Kernel
  using Point = CGAL::Point_2<Kernel>;
  using Polygon2WithHoles = CGAL::Polygon_with_holes_2<Kernel>;
  using Polygon2 = CGAL::Polygon_2<Kernel>;

  // Exact numbers
  py::class_<Kernel::FT>(m, "FieldNumber",
                         "A container for exact numbers in CGAL.")
      .def(py::init<long>())
      .def(py::init<double>())
      .def(py::self / Kernel::FT())
      .def(py::self + Kernel::FT())
      .def(py::self * Kernel::FT())
      .def(py::self == Kernel::FT())
      .def("__float__", &CGAL::to_double<Kernel::FT>)
      .def("__str__", [](const Kernel::FT &x) {
        return std::to_string(CGAL::to_double(x));
      });

  // Points
  py::class_<Point>(m, "Point", "A point in CGAL.")
      .def(py::init<Kernel::FT, Kernel::FT>())
      .def("x", [](const Point &p) { return p.x(); })
      .def("y", [](const Point &p) { return p.y(); })
      .def(py::self == Point())
      .def("__str__", [](const Point &p) {
        return fmt::format("({}, {})", CGAL::to_double(p.x()),
                           CGAL::to_double(p.y()));
      });

  // Polygons
  py::class_<Polygon2>(m, "Polygon", "A simple polygon in CGAL.")
      .def(py::init<>())
      .def(py::init([](const std::vector<Point> &vertices) {
        return std::make_unique<Polygon2>(vertices.begin(), vertices.end());
      }))
      .def("boundary",
           [](const Polygon2 &poly) {
             std::vector<Point> points;
             std::copy(poly.begin(), poly.end(), std::back_inserter(points));
             return points;
           })
      .def("is_simple", &Polygon2::is_simple)
      .def("area", [](const Polygon2 &poly) { return poly.area(); });

  py::class_<Polygon2WithHoles>(m, "PolygonWithHoles",
                                "A polygon with holes in CGAL.")
      .def(py::init(
          [](const Polygon2 &outer, const std::vector<Polygon2> &holes) {
            return new Polygon2WithHoles(outer, holes.begin(), holes.end());
          }))
      .def("outer_boundary",
           [](const Polygon2WithHoles &poly) { return poly.outer_boundary(); })
      .def("holes", [](const Polygon2WithHoles &poly) {
        std::vector<Polygon2> holes;
        std::copy(poly.holes_begin(), poly.holes_end(),
                  std::back_inserter(holes));
        return holes;
      });
}
