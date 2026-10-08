# NSIS Package Layout Specification

Version 0.1 (draft)

This document specifies how an NSIS Package repository is laid out and what its release contains, so that other tools can validate and package the same repositories as this action. How a Plugin is built (toolchains, flags, C runtime) is out of scope.

The key words MUST, MUST NOT, SHOULD and MAY are to be interpreted as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119).

## 1. Terms

- **Package**: what one repository releases. It has one **name**, `<name>`, matching `[A-Za-z0-9_-]+`. Names are case-sensitive.
- **Plugin Package**: a Package that releases a DLL called from NSIS scripts as `<name>::Function`.
- **Data Package**: a Package with nothing to build, such as headers, graphics or language files.
- **Prebuilt Package**: a Plugin Package that commits its DLLs instead of their source, for plugins whose source is lost. It is NOT RECOMMENDED: its DLLs can't be rebuilt or verified.
- **Target**: one of `x86-ansi`, `x86-unicode`, `amd64-unicode`, `arm64-unicode`.
- **License file**: a regular file whose name, cut at the first `.`, `-` or `_` and compared case-insensitively, is `LICENSE`, `LICENCE`, `COPYING` or `UNLICENSE`. For example `LICENSE`, `License.md` and `LICENSE-MIT` all count.
- **Readme file**: as a License file, with the stem `README`.

## 2. Repository layout

The repository root is laid out like NSISDIR.

| Path               | Plugin Package                                                         | Data Package                    | Shipped                                   |
| ------------------ | ---------------------------------------------------------------------- | ------------------------------- | ----------------------------------------- |
| `Contrib/<name>/`  | MUST exist and MUST contain at least one source file (§2.3)            | MAY exist, as MAY other subfolders of `Contrib/` | Plugin: no. Data: all of `Contrib/` |
| `Docs/<name>/`     | MAY exist                                                              | MAY exist                       | yes                                       |
| `Examples/<name>/` | MAY exist                                                              | MAY exist                       | yes                                       |
| `Include/`         | MAY exist, with any content                                            | MAY exist, with any content     | yes                                       |
| License file       | MUST exist at the top level or under `Docs/<name>/`                    | same                            | top level only                            |
| Readme file        | SHOULD exist at the top level                                          | same                            | yes                                       |
| `Plugins/`         | MUST NOT exist, except in a Prebuilt Package (§2.5)                    | MUST NOT exist                  | built (§3)                                |

### 2.1 Spelling

The folders `Contrib`, `Docs`, `Examples`, `Include` and `Plugins` MUST be spelled exactly so. A top-level entry that differs from one of them only in letter case, such as `docs/`, is an error.

### 2.2 Exclusivity

- `Docs/` and `Examples/` MUST NOT contain anything but `<name>/`.
- `Contrib/<name>/` MUST match `<name>` exactly, including case.

### 2.3 Source files

A source file is any file under `Contrib/<name>/`, at any depth, with one of the extensions `.c`, `.cpp`, `.cxx`, `.cc`, `.rc`, `.dpr`, `.lpr`, `.pas` or `.rs`, compared case-insensitively.

### 2.4 Forbidden content

- There MUST NOT be a `*.dll` file anywhere in the repository. Paths with a component starting with `.`, such as `.git/`, are exempt.
- There MUST NOT be a top-level `Plugins/`.

A Prebuilt Package is exempt from both, as §2.5 says.

### 2.5 Prebuilt Package

- `Contrib/<name>/` MAY exist and is not shipped.
- `Plugins/<target>/<name>.dll` MUST exist for at least one Target. Each DLL's PE machine MUST match its Target, as in §3.
- There MUST NOT be any other `*.dll` file, with the same exemption as in §2.4.
- A validator SHOULD warn that the Package is prebuilt.

### 2.6 Everything else

Other top-level entries, such as `scripts/`, `.github/`, `CHANGELOG.md` or a workspace `Cargo.toml`, are allowed. They are ignored and MUST NOT be shipped.

## 3. Release Archive

A zip named `<name>-<version>.zip`, where `<version>` is the release tag with one leading `v` removed. A build not made from a tag MAY use any other identifier, such as the short commit SHA.

Its root maps onto NSISDIR and contains exactly:

- Plugin Package: `Plugins/<target>/<name>.dll` for each Target built. Each DLL's PE machine MUST match its Target: `0x014C` for x86, `0x8664` for amd64, `0xAA64` for arm64.
- `Docs/`, `Examples/` and `Include/` as in the repository, those that exist.
- Data Package: `Contrib/` as in the repository.
- The top-level License and Readme files.

## 4. Package Installer

Producing an installer is OPTIONAL. If produced, it is named `<name>-<version>-setup.exe` and:

- MUST copy the Release Archive's folders into an existing NSIS installation, and MUST NOT install the License or Readme files.
- MUST show a license page if the Release Archive's repository has a License file. Its text is every top-level License file, shortest name first, joined; without one, the shallowest License file under `Docs/<name>/`. Without any License file, which only a lenient validator accepts, there is no license page.

## 5. Conformance

- A **validator** conforms if it rejects every repository that violates a MUST or MUST NOT of §2 and accepts every other. It SHOULD report a missing Readme file as a warning.
- A validator MAY offer a **lenient** mode for legacy Packages whose authors can no longer be asked to fix them. In it, the violations listed below MUST be reported as warnings instead of rejecting the repository; every other rule applies unchanged. The list:
  - no License file (§2)
- A **packager** MAY package a repository that a lenient validator accepts.
- A packager conforms if, given a valid repository, it produces a Release Archive as specified in §3, and an installer, if any, as specified in §4.
