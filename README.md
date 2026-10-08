# release-package

![License](https://img.shields.io/github/license/nsis-dev/release-package?color=blue&style=for-the-badge)
![Release](https://img.shields.io/github/v/release/nsis-dev/release-package?style=for-the-badge)
![CI](https://img.shields.io/github/actions/workflow/status/nsis-dev/release-package/ci.yml?style=for-the-badge)

> [!IMPORTANT]
> This GitHub Action is pre-1.0, expect breaking changes!

Release [NSIS](https://nsis.sourceforge.io/) packages from GitHub: plugins built from source, or headers, graphics and language files with nothing to build.

## Usage

Build on every push. When a release is published, attach these files to it:

- a Release Archive
- a Package Installer
- checksums, and build attestations on request

```yaml
on:
  push:
  pull_request:
  release:
    types: [published]

jobs:
  plugin:
    runs-on: windows-latest
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v7
      - uses: nsis-dev/release-package@v0
        with:
          name: Hello
          sources: Contrib/Hello/*.c
```

A repository with nothing to build (headers, graphics, language files) sets neither `sources` nor `project`, only `name`.

A plugin whose source is lost can set `toolchain: prebuilt` and commit `Plugins/<target>/<name>.dll` instead. This is an antipattern and the action warns about it: nobody can rebuild or verify those DLLs, and an attestation only proves the workflow copied them. Use it only to keep an otherwise abandoned plugin available.

A release of tag `v1.0.0` gets these assets:

| Asset                   | Contents                                                                                |
| ----------------------- | --------------------------------------------------------------------------------------- |
| `Hello-1.0.0.zip`       | `Plugins/<target>/Hello.dll`, your `Docs/`, `Examples/` and `Include/`, LICENSE, README |
| `Hello-1.0.0-setup.exe` | Installs those folders into NSISDIR, showing the LICENSE on its license page            |
| `SHA256SUMS`            | Checksums of the above                                                                  |

Other builds upload the zip and installer as the workflow artifact `<name>-<toolchain>`, versioned by the short commit SHA.
To attest build provenance, set `attestations: true` and add the `id-token: write` and `attestations: write` permissions.
Attestations are free on public repositories; a private one needs GitHub Team or Enterprise.
Check where a released file came from with `gh attestation verify Hello-1.0.0.zip --repo <owner>/<repo>`.

To also build with a second Toolchain as a check, use a matrix and release only one of them:

```yaml
jobs:
  plugin:
    strategy:
      matrix:
        include:
          - { toolchain: msvc, os: windows-latest, release: true }
          - { toolchain: mingw, os: ubuntu-latest, release: false }
    runs-on: ${{ matrix.os }}
    permissions:
      contents: write
    steps:
      - uses: actions/checkout@v7
      - uses: nsis-dev/release-package@v0
        with:
          name: Hello
          sources: Contrib/Hello/*.c
          toolchain: ${{ matrix.toolchain }}
          release: ${{ matrix.release }}
```

## Layout

A Package repository is laid out like NSISDIR, as specified in [SPEC.md](SPEC.md) for other tools to implement. The action checks this first and fails before building if it isn't:

| Path                | Rule                                                                                                                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Contrib/<name>/`   | **Required**, holds the source, not shipped. With `toolchain: none` it is optional and ships as-is, e.g. `Contrib/Graphics/` or `Contrib/Language files/`. With `prebuilt` it is optional and not shipped |
| `LICENSE`           | **Required** (a warning with `strict: false`) at the top level or in `Docs/<name>/`, any extension or suffix (`LICENSE-MIT`), or `LICENCE`, `COPYING`, `UNLICENSE`; several are joined on the installer's license page |
| `README`            | Suggested at the top level, any extension                                                                                                                                             |
| `Docs/<name>/`      | Optional, nothing else in `Docs/`, ships as-is                                                                                                                                        |
| `Examples/<name>/`  | Optional, nothing else in `Examples/`, ships as-is                                                                                                                                    |
| `Include/`          | Optional, ships as-is                                                                                                                                                                 |
| `Plugins/`, `*.dll` | Not committed, the action builds them. With `toolchain: prebuilt`, `Plugins/<target>/<name>.dll` is committed and each DLL's PE machine must match its target                        |

`Contrib`, `Docs`, `Examples`, `Include` and `Plugins` must be spelled that way.

## Inputs

| Name           | Default                              | Description                                                                                                                                                                                                                                                                                                                                                 |
| -------------- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`         |                                      | Package name; for a Plugin, the DLL basename scripts call as `Name::Func`.                                                                                                                                                                                                                                                                                  |
| `sources`      |                                      | `msvc`, `mingw` and `zig` only: C/C++ source globs (`.c`, `.cpp`, `.cxx`, `.cc`, `.rc`).                                                                                                                                                                                                                                                                    |
| `project`      |                                      | `fpc` and `rust` only: path of the Pascal project file (`.dpr`, `.lpr`, `.pas`) or the plugin's `Cargo.toml`.                                                                                                                                                                                                                                               |
| `targets`      | `x86-ansi,x86-unicode,amd64-unicode` | Any of `x86-ansi`, `x86-unicode`, `amd64-unicode`, `arm64-unicode`. `arm64-unicode` is opt-in.                                                                                                                                                                                                                                                              |
| `toolchain`    | from `sources`/`project`             | `msvc`, `fpc` or `rust` on a Windows runner, `mingw` on a Linux runner, `zig` on any runner, `none` to build nothing, `prebuilt` to ship the committed DLLs (an antipattern, see above). Left out, it is `none` without `sources` or `project`, `msvc` with `sources`, `rust` for a `Cargo.toml` project and `fpc` otherwise. `none` ships `Include/`, `Examples/`, `Docs/` and `Contrib/`: headers, graphics, language files. `prebuilt` ignores `targets` and ships every committed one. |
| `crt`          | `static`                             | C/C++ only: `static` links the C runtime in; `none` builds without it, entry point `DllMain`.                                                                                                                                                                                                                                                               |
| `strict`       | `true`                               | Fail on every layout violation. `false` is for legacy packages: a missing LICENSE is only a warning, and the installer has no license page.                                                                                                                                                                                                                 |
| `release`      | `true`                               | Attach the files to the release that triggered the run.                                                                                                                                                                                                                                                                                                     |
| `attestations` | `false`                              | Attest build provenance, needs the `id-token` and `attestations` write permissions. Free on public repositories; a private one needs GitHub Team or Enterprise.                                                                                                                                                                                             |

Each Toolchain takes exactly one of `sources` and `project`; the action fails before building if the other one is set.
List inputs are comma or newline separated, so paths may contain spaces.

There are deliberately no inputs for defines, libraries, include directories or raw flags:

- Every directory holding a matched source is an include directory.
- A fixed list of common Windows import libraries is linked; unused ones add no imports. If a Plugin needs one that's missing, open an issue.
- Put defines in a header.
- The NSIS version of the Plugin API, the Free Pascal version and the Zig version are pinned, and only change in a release release.

## Outputs

| Name          | Description                                         |
| ------------- | --------------------------------------------------- |
| `plugins-dir` | Directory containing `Plugins/<target>/<name>.dll`. |
| `archive`     | Path of the Release Archive.                        |
| `installer`   | Path of the Package Installer.                      |

## Writing the plugin

### C/C++

Include the Plugin API the way NSIS installs it:

```c
#include <windows.h>
#include <nsis/pluginapi.h>
```

`pluginapi.c` is compiled in. `UNICODE` and `_UNICODE` are defined for `*-unicode` targets. A C++ plugin needs `extern "C"` on its exported functions.

> [!NOTE]
> `arm64-unicode` builds with `msvc` and `zig`; Ubuntu's MinGW has no arm64 compiler.
> Official NSIS releases only ship x86 stubs. amd64 plugins work with forks such as
> [negrutiu/nsis](https://github.com/negrutiu/nsis).

The C/C++ Toolchains differ in which C runtime a `crt: static` Plugin depends on:

| Toolchain | C runtime                                                                                             |
| --------- | ----------------------------------------------------------------------------------------------------- |
| `msvc`    | Linked into the DLL.                                                                                  |
| `mingw`   | Imported from `msvcrt.dll`, which every Windows has.                                                  |
| `zig`     | Imported from the Universal CRT, built into Windows 10 and later; Vista to 8.1 need update KB2999226. |

With `crt: none` no Toolchain imports a C runtime. `zig` then leaves `uuid` out of the linked libraries, so a Plugin using COM GUIDs such as `IID_IUnknown` defines them itself with `INITGUID`.

### Pascal

Use the unit NSIS ships:

```pascal
library Hello;

uses
  nsis, Windows;

procedure Greet(const hwndParent: HWND; const string_size: integer; const variables: NSISPTChar; const stacktop: pointer); cdecl;
begin
  Init(hwndParent, string_size, variables, stacktop);
  PushString('Hello, ' + PopString() + '!');
end;

exports
  Greet;

begin
end.
```

Code compiles in Delphi mode (`-Mdelphi`) unless the source sets `{$mode}`. `UNICODE` is defined for `*-unicode` targets, which switches `nsis.pas` to wide strings. The official Free Pascal installer is downloaded from SourceForge, checked against the MD5 listed there, and cached.

> [!NOTE]
> Free Pascal is not Delphi. Plugins that use the VCL (`Graphics`), Delphi-only
> units such as `WinSvc`, or assembler calling into Delphi's RTL need porting.
> Free Pascal 3.2 has no arm64 Windows target.

### Rust

Keep the crate in `Contrib/<name>/`, or put a workspace `Cargo.toml` at the top level with `Contrib/<name>` as a member, and point `project` at the Plugin's own `Cargo.toml`. The action builds it with Cargo for the `*-pc-windows-msvc` targets and relies on two things only:

- `[lib] crate-type = ["cdylib"]`. The DLL is renamed to `<name>.dll`, so the crate name doesn't have to match.
- `*-unicode` targets build the crate's default features. `x86-ansi` builds with `--no-default-features --features ansi`, so a crate that builds `x86-ansi` needs an `ansi` feature that switches it to ANSI strings.

Export functions as `#[unsafe(no_mangle)] pub extern "C" fn`. No Plugin API is supplied; bring a crate for it or write the stack handling yourself. A `rust-toolchain.toml` next to the manifest picks the Rust version, otherwise the runner's stable Rust is used. Size settings such as `opt-level`, `lto` and `panic = "abort"` belong in the crate's `[profile.release]`.

## Development

[mise](https://mise.jdx.dev/) installs the tools (Python, ruff, actionlint, hk) and the
[hk](https://hk.jdx.dev/) pre-commit hook:

```sh
mise install
mise run check   # lint, formatting, script self-check
mise run fix     # apply lint and formatting fixes
```

`action.yml` runs stdlib-only Python scripts from `scripts/`, which also run locally:

```sh
NAME=HelloC SOURCES='test/hello/Contrib/HelloC/*.c' TOOLCHAIN=mingw python3 scripts/build_c.py build
```

## License

[Apache License, Version 2.0](LICENSE)
