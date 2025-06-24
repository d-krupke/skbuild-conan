#include <CGAL/Simple_cartesian.h>
#include <CGAL/point_generators_2.h>
#include <iostream>

int main() {
    typedef CGAL::Simple_cartesian<double> Kernel;
    typedef Kernel::Point_2 Point_2;

    Point_2 p(1.0, 2.0);
    std::cout << "Point: (" << p.x() << ", " << p.y() << ")" << std::endl;
    return 0;
}
