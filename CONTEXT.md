# release-package

A GitHub Action that turns an NSIS package, a plugin's source or data (headers, graphics, language files), into a release, replacing wiki uploads as the way NSIS extensions are distributed.

## Language

**Package**:
What a repository releases: a Plugin, or a data-only package (headers, graphics, language files) built with `toolchain: none`, which ships `Include/`, `Examples/`, `Docs/` and `Contrib/` as they are. Its name is the `name` input.
_Avoid_: extension, add-on

**Plugin**:
One DLL that NSIS scripts call as `Name::Function`, kept in its own repository. Its name is the DLL basename.
_Avoid_: extension, add-on

**Target**:
One of the NSIS 3 architecture and charset combinations a Plugin is built for: `x86-ansi`, `x86-unicode`, `amd64-unicode`, `arm64-unicode`. It names the folder under `Plugins/`.
_Avoid_: arch, platform, flavour

**Toolchain**:
The compiler family that builds a Plugin: `msvc`, `mingw` or `zig` (`zig cc`, on any runner) for C/C++, `fpc` (Free Pascal) for Pascal, `rust` (Cargo with MSVC targets) for Rust.
_Avoid_: compiler, stack

**Release Toolchain**:
The one Toolchain whose DLLs a release ships, chosen by the Plugin author.

**Plugin API**:
NSIS's `pluginapi.c` and headers, or `nsis.pas` for Pascal, which give a Plugin access to the NSIS stack and variables. For `msvc`, `mingw`, `zig` and `fpc` it is compiled into the Plugin from the NSIS source of a given version; a Rust Plugin is supplied none and brings its own.
_Avoid_: SDK, ExDLL, pluginapi.lib

**Sources and Project**:
The two ways a Plugin points at its code. `msvc`, `mingw` and `zig` take **sources**, globs matching every file to compile. `fpc` and `rust` take a **project**, the single file their Toolchain reads to find the rest: a `.dpr`, `.lpr` or `.pas`, or a `Cargo.toml`. A Toolchain takes exactly one of them.
_Avoid_: entry, manifest (except for Cargo's own). "Input" means an `action.yml` input, not the value of one.

**Release Archive**:
The zip attached to a release, `<Name>-<version>.zip`. It contains the built `Plugins/<target>/<Name>.dll` (none for a data-only Package), plus `Contrib/` for one, whichever of `Docs/`, `Examples/` and `Include/` the repository has, its top-level LICENSE and README if there are any, laid out so it unzips into NSISDIR.
_Avoid_: bundle, distribution

**Package Installer**:
The Windows installer attached to a release, `<Name>-<version>-setup.exe`. It copies the Release Archive's NSISDIR folders into an existing NSIS installation; the LICENSE is not copied, it is shown on the license page. A top-level LICENSE wins, and several (`LICENSE-MIT`, `LICENSE-APACHE`) are joined into one page; without one, the shallowest one under `Docs/` is shown. With `strict: false` a Package may have no LICENSE, and then there is no license page.
_Avoid_: setup
