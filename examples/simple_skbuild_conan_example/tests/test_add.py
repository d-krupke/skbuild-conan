from simple_skbuild_conan_example import add


def test_add():
    assert add(1, 2) == "1+2=3"
    assert add(1, 3) == "1+3=4"
