#!/usr/bin/env python3
"""Check the Plugin repository in the working directory follows the NSISDIR-shaped layout.

Configured through the environment variables NAME, TOOLCHAIN and STRICT, set by action.yml.
"""

import struct
import sys
from pathlib import Path

from common import TARGETS, BuildError, env, find_license, is_doc, pe_machine
from toolchain import SOURCE_EXTS

# Folders that mirror NSISDIR, spelled the way NSIS spells them
KNOWN_DIRS = ("Contrib", "Docs", "Examples", "Include", "Plugins")


def check(root, name, headers_only=False, strict=True, prebuilt=False):
    """(errors, warnings, suggestions), each a list of (path relative to root, message).

    Not strict, the violations legacy packages can't fix themselves are warnings instead.
    Prebuilt, Plugins/<target>/<name>.dll is committed instead of built from Contrib/<name>/.
    """
    errors, warnings, suggestions = [], [], []
    lenient = errors if strict else warnings
    top = {p.name: p for p in root.iterdir()}

    for known in KNOWN_DIRS:
        for entry in top:
            if entry != known and entry.lower() == known.lower():
                errors.append((entry, f"rename {entry}/ to {known}/"))

    if "Plugins" in top and not prebuilt:
        errors.append(("Plugins", "Plugins/ is built by the action, don't commit it"))
    shipped = 0
    for dll in sorted(root.rglob("*.dll")):
        rel = dll.relative_to(root)
        if any(part.startswith(".") for part in rel.parts):
            continue
        parts = rel.parts
        if not prebuilt:
            errors.append((rel.as_posix(), "don't commit DLLs, the action builds them"))
        elif not (
            len(parts) == 3
            and parts[0] == "Plugins"
            and parts[1] in TARGETS
            and parts[2] == f"{name}.dll"
        ):
            errors.append(
                (rel.as_posix(), f"only Plugins/<target>/{name}.dll is allowed")
            )
        else:
            machine = TARGETS[parts[1]][2]
            try:
                got = pe_machine(dll.read_bytes())
            except (BuildError, struct.error):
                got = None
            if got != machine:
                errors.append((rel.as_posix(), f"not a {parts[1].split('-')[0]} DLL"))
            shipped += 1
    if prebuilt and not shipped:
        errors.append(
            (f"Plugins/x86-ansi/{name}.dll", f"commit Plugins/<target>/{name}.dll")
        )

    contrib = top.get("Contrib")
    subdirs = {p.name: p for p in contrib.iterdir()} if contrib else {}
    if headers_only or prebuilt:
        pass
    elif name not in subdirs:
        near = [s for s in subdirs if s.lower() == name.lower()]
        errors.append(
            (f"Contrib/{name}", f"rename Contrib/{near[0]}/ to Contrib/{name}/")
            if near
            else (f"Contrib/{name}", f"put the source in Contrib/{name}/")
        )
    elif not any(p.suffix.lower() in SOURCE_EXTS for p in subdirs[name].rglob("*")):
        errors.append(
            (
                f"Contrib/{name}",
                f"Contrib/{name}/ has no source ({', '.join(sorted(SOURCE_EXTS))})",
            )
        )

    for folder in ("Docs", "Examples"):
        for entry in sorted(top[folder].iterdir()) if folder in top else ():
            if entry.name != name:
                errors.append(
                    (
                        f"{folder}/{entry.name}",
                        f"move {folder}/{entry.name} into {folder}/{name}/",
                    )
                )

    if find_license(root) is None:
        lenient.append(
            (
                "LICENSE",
                f"add a LICENSE at the top level or in Docs/{name}/, the installer shows it",
            )
        )
    if not any(is_doc(p, ("README",)) for p in top.values()):
        suggestions.append(
            ("README.md", "consider a top-level README, it ships in the archive")
        )
    return errors, warnings, suggestions


def main():
    name = env("NAME")
    if not name:
        print("::error::name is required", flush=True)
        return 1
    toolchain = env("TOOLCHAIN")
    errors, warnings, suggestions = check(
        Path.cwd(),
        name,
        toolchain == "none",
        env("STRICT") != "false",
        toolchain == "prebuilt",
    )
    for level, findings in (
        ("error", errors),
        ("warning", warnings),
        ("notice", suggestions),
    ):
        for path, message in findings:
            print(f"::{level} file={path}::{message}")
    print(
        f"{len(errors)} error(s), {len(warnings)} warning(s), {len(suggestions)} suggestion(s)"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
