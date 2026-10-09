#!/usr/bin/env python3
"""Compile installer.nsi for a Release Archive tree.

Configured through environment variables set by action.yml.
"""

import shutil
import tempfile
from pathlib import Path

import common
from common import BuildError, env, guard, run, set_output


def find_license(tree):
    """The license shown on the installer's page; None if the tree has none."""
    licenses = common.find_licenses(tree)
    if not licenses:
        return None
    top = [p for p in licenses if p.parent == tree]
    # A plain LICENSE (or LICENSE.md) is the whole story; it wins over LICENSE-MIT and friends
    if len(top) < 2 or common.is_plain_license(top[0]):
        return licenses[0]
    # Dual-licensed (LICENSE-MIT, LICENSE-APACHE): the page takes one file, so join them
    combined = Path(tempfile.mkdtemp()) / "LICENSE.txt"
    combined.write_text(
        ("\n" + "-" * 70 + "\n\n").join(
            f"{p.name}\n\n{p.read_text(encoding='utf-8', errors='replace')}"
            for p in top
        ),
        encoding="utf-8",
    )
    return combined


# The Release Archive folders the installer copies into NSISDIR
SHIPPED = ("Plugins", "Contrib", "Docs", "Examples", "Include")
# Folders of NSISDIR itself: created if missing, never removed. Graphics and
# language files go into the shared Contrib ones, so only their files are removed
STRUCTURE = {
    *SHIPPED,
    *(f"Plugins\\{t}" for t in common.TARGETS),
    "Contrib\\Graphics",
    *(f"Contrib\\Graphics\\{d}" for d in ("Checks", "Header", "Icons", "Wizard")),
    "Contrib\\Language files",
    "Contrib\\UIs",
}


def file_list(tree):
    """installer.nsi macros that install, then uninstall, each shipped path one at a time.

    Folders come before their contents, and the uninstall list is the reverse, so
    files are deleted before the folders that held them. NSISDIR's own folders
    are left out of the uninstall list.
    """
    paths = sorted(
        p
        for top in SHIPPED
        if (tree / top).is_dir()
        for p in [tree / top, *(tree / top).rglob("*")]
    )
    lines = []
    for macro, prefix, order in (
        ("PackageInstall", "", paths),
        ("PackageUninstall", "Un", reversed(paths)),
    ):
        lines.append(f"!macro {macro}")
        for p in order:
            rel = str(p.relative_to(tree)).replace("/", "\\")
            # = would end the path's INI key in the uninstall log, and $ is a
            # variable at runtime but literal in File's source path
            if "=" in rel or "$" in rel:
                raise BuildError(f"{rel}: the installer can't ship a path with = or $")
            if rel in STRUCTURE:
                if not prefix:
                    lines.append(f'  CreateDirectory "$INSTDIR\\{rel}"')
                continue
            kind = "Dir" if p.is_dir() else "File"
            lines.append(f'  !insertmacro {prefix}Package{kind} "{rel}"')
        lines.append("!macroend")
    return "\n".join(lines) + "\n"


def main():
    name, version, tree = env("NAME"), env("VERSION"), env("TREE")
    if not (name and version and tree):
        raise BuildError("name, version and tree are required")
    # makensis resolves relative paths against the script, not the working directory
    tree = Path(tree).resolve()
    if not tree.is_dir():
        raise BuildError(f"{tree} does not exist")

    installer = (
        Path(env("OUTPUT_DIR", "dist")).resolve() / f"{name}-{version}-setup.exe"
    )
    installer.parent.mkdir(parents=True, exist_ok=True)
    makensis = shutil.which("makensis")
    if not makensis:
        raise BuildError("makensis not found")

    files = Path(tempfile.mkdtemp()) / "files.nsh"
    files.write_text(file_list(tree), encoding="utf-8")

    cmd = [
        makensis,
        "-V2",
        f"-DNAME={name}",
        f"-DVERSION={version}",
        f"-DSRC={tree}",
        f"-DOUTFILE={installer}",
        f"-DFILES={files}",
    ]
    license = find_license(tree)
    if license:
        cmd.append(f"-DLICENSE={license}")
    elif env("STRICT") != "false":
        raise BuildError(f"{tree} has no LICENSE, the installer shows it on its page")
    cmd.append(str(Path(__file__).with_suffix(".nsi")))
    run(cmd)

    set_output("installer", installer)


if __name__ == "__main__":
    guard(main)
