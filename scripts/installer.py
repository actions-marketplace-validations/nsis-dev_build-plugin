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

    cmd = [
        makensis,
        "-V2",
        f"-DNAME={name}",
        f"-DVERSION={version}",
        f"-DSRC={tree}",
        f"-DOUTFILE={installer}",
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
