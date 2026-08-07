# Docker-based example tests

Builds and tests the examples inside a set of Linux containers with different
compilers.

```sh
./tests/docker/run.sh              # default image set
./tests/docker/run.sh --list       # show known images
./tests/docker/run.sh gcc10        # a single image
./tests/docker/run.sh --all        # every known image
./tests/docker/run.sh --with-cgal  # include the slow CGAL example
```

Output ends in a summary:

```
IMAGE          RESULT DETECTED cppstd
gcc10          PASS   gnu14
gcc13          PASS   gnu17
ubuntu2204     PASS   gnu17
almalinux9     PASS   gnu17
```

## Why this exists

The failure mode behind [#16](https://github.com/d-krupke/skbuild-conan/issues/16)
is a compiler whose **default** C++ standard is older than a dependency
requires. `conan profile detect` records that default, and CGAL then refuses to
build because the profile says `14`.

This cannot be reproduced on `ubuntu-latest`, which ships a GCC defaulting to
`gnu17`. A regression that dropped the `compiler.cppstd` pin from the examples
would pass every check in `.github/workflows/`. GCC 10 and older default to
`gnu14` and reproduce it exactly, which is why `gcc:10` is in the default set.

## What each run asserts

Building successfully is deliberately **not** the only check — on a modern
compiler an unpinned build still succeeds, which would report a false pass.
Each example must also:

1. log `Conan toolchain: C++ Standard 17`, proving the pinned standard was the
   one actually applied, and
2. produce **no** `has been modified` warning. Conan emits that via
   `variable_watch` when a `CMakeLists.txt` overrides the standard the toolchain
   set, which means dependencies and bindings disagree.

Each run also prints the profile the image detects on its own, so the table of
compiler defaults documents itself rather than relying on a hand-maintained
list that will silently rot.

## Caching

Each image gets its own named docker volume for `CONAN_HOME`
(`skbuild-conan-cache-<label>`), so boost and CGAL are built once and reused.
Use `--no-cache` to ignore them, and remove them with:

```sh
docker volume ls -q -f name=skbuild-conan-cache- | xargs -r docker volume rm
```

The repository is mounted read-only and copied to `/work` inside the container,
so build artefacts never touch your checkout and nothing ends up owned by root.

## Limitations

- **Linux only, by design.** Windows containers need a Windows host, so this
  harness covers neither MSVC nor macOS. Linux is the platform we support first;
  this is where that coverage lives.
- `--with-cgal` uses `cgal_skbuild_conanio_example`, not
  `cgal_skbuild_conan_example`. The latter sets
  `conan_env={"CONAN_HOME": "./conan/cache"}`, which points the cache inside the
  example directory and therefore bypasses the shared volume — it would rebuild
  CGAL from scratch on every run.
- Alpine/musl is intentionally absent: conancenter ships glibc binaries, so it
  is not a supported target.
- The first run of an image is slow (toolchain install plus a cold conan
  cache). Later runs reuse both.
