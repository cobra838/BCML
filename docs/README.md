# NOTICE: BCML has been discontinued

BCML is a very old, very inefficient solution for overall mod management, which
is a role it was not originally meant for. There are several issues with it that
are unable to be solved, on a fundamental level.

Among these issues, the most pertinent is that BCML adds bugs to the merged mods
that do not exist in the mods, themselves, causing actors to fail to load, causing
panic moons, and, in extreme cases, causing crashes.

Several years ago, we wrote [UKMM](https://github.com/GingerAvalanche/ukmm/tree/master)
to solve these issues, and more. Though it is still in beta, it is already the more
capable mod manager, containing many more features, bug fixes, improvements, and
all-around capabilities.

Please use that, instead of trying to download or fork this.

And if you *do* decide to use this, then please, for the love of all things holy, don't
patch 3.10.8 - go back and branch off of the 3.10.4 commit, from before support was
removed for 60%+ of the mods in the BotW ecosystem.

![BCML Logo](https://i.imgur.com/OiqKPx0.png)

# BCML: BOTW Cross-Platform Mod Loader

A mod merging and managing tool for _The Legend of Zelda: Breath of the Wild_

![BCML Banner](https://i.imgur.com/vmZanVl.png)

## Purpose

Why a mod loader for BOTW? Installing a mod is usually easy enough once you have a
homebrewed console or an emulator. Is there a need for a special tool?

Yes. As soon as you start trying to install multiple mods, you will find complications.
The BOTW game ROM is fundamentally structured for performance and storage use on a
family console, without any support for modification. As such, files like the
[resource size table](https://zeldamods.org/wiki/Resource_system) or
[TitleBG.pack](https://zeldamods.org/wiki/TitleBG.pack) will almost inevitably begin to
clash once you have more than a mod or two. Symptoms can include mods simply taking no
effect, odd bugs, actors that don't load, hanging on the load screen, or complete
crashing. BCML exists to resolve this problem. It identifies, isolates, and merges the
changes made by each mod into a single modpack that just works.

## Prerequisites

-   Windows 10+ (7-8 _might_ work but are not officially supported) or basically any modern Linux
    distribution
-   A legal, unpacked game dump of _The Legend of Zelda: Breath of the Wild_ for Switch
    (version 1.6.0) or Wii U (version 1.5.0)
-   [The latest x64 Visual C++ redistributable](https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads#section-2)
-   Cemu (optional)

## Install from wheel

The package index contains CPython 3.9-3.14 wheels for Windows x64, Linux x64, and macOS arm64. The portable build is CPython 3.14.

### pip

```bash
py -3.14 -m pip install --upgrade -r https://cobra838.github.io/BCML/latest.txt

py -3.14 -m bcml
```

## Building from Source

Building from source requires, in addition to the general prerequisites:

-   Python 3.9+

-   Rust 1.99 (nightly)+

-   Node.js v24+

Tested versions:

```bash
uv run --no-project --python 3.14 python --version
# Python 3.14.5

rustc --version
# rustc 1.101.0-nightly (ea137335b 2026-10-05)

node --version
# v26.10.0
```

### Environment Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/)  
Then install Python:

```bash
uv python install 3.14
```

Install [rustup](https://rust-lang.github.io/rustup/installation/)  
Then install Rust nightly:

```bash
rustup toolchain install nightly
rustup default nightly
```
___

The uv environment is used to build BCML.  
To run BCML, also install Python separately: [Python 3.14](https://www.python.org/downloads).

You can install Windows Python with [Python install manager](https://www.python.org/ftp/python/pymanager).  
Install the MSI version, not the MSIX!  
Then install Python:

```bash
py install 3.14
```


### Development Environment

Use uv to create a CPython 3.14 environment and install the application and build dependencies:

For cmd:

```cmd
uv venv --python 3.14 .venv
call .venv\Scripts\activate
uv pip install -r requirements.txt
uv pip install -r requirements-build.txt
```

For Linux Bash:

```bash
uv venv --python 3.14 .venv
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -r requirements-build.txt
```

`requirements.txt` contains the dependencies BCML needs at runtime.
`requirements-build.txt` contains Maturin, MkDocs, and PyInstaller for local builds.

### Development Build

This validates Rust code, rebuilds frontend assets, rebuilds the Rust Python extension, reinstalls the wheel, and packages BCML using PyInstaller.

```bash
rustup run nightly cargo check
npm --prefix bcml/assets install
npm --prefix bcml/assets run build
python -m mkdocs build -d ./bcml/assets/help
rustup run nightly maturin build --release --interpreter python
uv pip install --force-reinstall --no-deps --no-index --find-links ./target/wheels bcml
python -c "from pathlib import Path; import shutil; source = next(Path('.venv/Lib/site-packages/bcml').glob('bcml*.pyd')); shutil.copy2(source, 'bcml')"
python -m PyInstaller --onedir --windowed --name BCML --distpath ./0dist --workpath ./build/pyinstaller --collect-all bcml --collect-all aamp --collect-all byml --collect-all botw_utils --collect-all rstb --icon bcml/data/bcml.ico --add-data ".venv/Lib/site-packages/aamp/botw_hashed_names.txt;aamp" bcml/__main__.py
```

### Quick Rebuild

Use this after dependencies are already installed.

```bash
rustup run nightly cargo check
npm --prefix bcml/assets run build
rustup run nightly maturin build --release --interpreter python
uv pip install --force-reinstall --no-deps --no-index --find-links ./target/wheels bcml
python -c "from pathlib import Path; import shutil; source = next(Path('.venv/Lib/site-packages/bcml').glob('bcml*.pyd')); shutil.copy2(source, 'bcml')"
python -m PyInstaller --onedir --windowed --name BCML --distpath ./0dist --workpath ./build/pyinstaller --collect-all bcml --collect-all aamp --collect-all byml --collect-all botw_utils --collect-all rstb --icon bcml/data/bcml.ico --add-data ".venv/Lib/site-packages/aamp/botw_hashed_names.txt;aamp" bcml/__main__.py
```

### Build wheel only

```bash
rustup run nightly cargo check
npm --prefix bcml/assets install
npm --prefix bcml/assets run build
python -m mkdocs build -d ./bcml/assets/help
rustup run nightly maturin build --release --interpreter python
uv pip install --force-reinstall --no-deps --no-index --find-links ./target/wheels bcml
```

## Tested dependencies, Windows x64, Python 3.14:

```bash
❯ uv pip install -r requirements.txt
Resolved 20 packages in 341ms
      Built proxy-tools==0.1.0
Prepared 1 package in 1.28s
Installed 20 packages in 210ms
 + aamp==1.4.1.post1
 + botw-utils==0.2.3
 + byml==2.4.5.post1
 + certifi==2026.7.22
 + cffi==2.1.1
 + charset-normalizer==3.5.2
 + clr-loader==0.3.1
 + idna==3.20
 + oead==1.4.0 (from https://cobra838.github.io/oead/wheels/oead-1.4.0-cp314-cp314-win_amd64.whl)
 + packaging==26.3
 + proxy-tools==0.1.0
 + pycparser==3.0
 + pythonnet==3.2.0
 + pywebview==6.2.1
 + pyyaml==6.0.3
 + requests==2.34.2
 + rstb==1.2.2
 + sortedcontainers==2.4.0
 + urllib3==2.8.0
 + xxhash==4.0.1
```

```bash
❯ uv pip install -r requirements-build.txt
Resolved 36 packages in 345ms
Installed 29 packages in 5.75s
 + altgraph==0.17.5
 + babel==2.18.0
 + backrefs==8.0
 + click==8.5.0
 + colorama==0.4.6
 + ghp-import==2.1.0
 + jinja2==3.1.6
 + markdown==3.11
 + markupsafe==3.0.4
 + maturin==1.15.0
 + mergedeep==1.3.4
 + mkdocs==1.6.1
 + mkdocs-get-deps==0.2.2
 + mkdocs-material==9.7.7
 + mkdocs-material-extensions==1.3.1
 + paginate==0.5.7
 + pathspec==1.1.1
 + pefile==2024.8.26
 + platformdirs==4.12.3
 + pygments==2.21.0
 + pyinstaller==6.22.3
 + pyinstaller-hooks-contrib==2026.8
 + pymdown-extensions==12.1
 + python-dateutil==2.9.0.post0
 + pywin32-ctypes==0.2.3
 + pyyaml-env-tag==1.1
 + setuptools==84.0.0
 + six==1.17.0
 + watchdog==6.0.0
```

## Usage and Troubleshooting

For information on how to use BCML, see the Help dialog in-app or read the documentation
[on the repo](https://github.com/NiceneNerd/BCML/tree/master/docs). For issues and
troubleshooting, please check the official
[Troubleshooting](https://github.com/NiceneNerd/BCML/wiki/Troubleshooting) page.

## Contributing

-   Issues: <https://github.com/NiceneNerd/BCML/issues>
-   Source: <https://github.com/NiceneNerd/BCML>

BOTW is an immensely complex game, and there are a number of new mergers that could be
written. If you find an aspect of the game that can be complicated by mod conflicts, but
BCML doesn't yet handle it, feel free to try writing a merger for it and submitting a
PR.

Python and JSX code for BCML is subject to formatting standards. Python should be
formatted with Black. JSX should be formatted with Prettier, using the following
settings:

```json
{
    "prettier.arrowParens": "avoid",
    "prettier.jsxBracketSameLine": true,
    "prettier.printWidth": 88,
    "prettier.tabWidth": 4,
    "prettier.trailingComma": "none"
}
```

## License

This software is licensed under the terms of the GNU General Public License, version 3
or later. The source is publicly available on
[GitHub](https://github.com/NiceneNerd/BCML).

This software includes the 7-Zip console application `7z.exe` and the library `7z.dll`,
which are licensed under the GNU Lesser General Public License. The source code for this
application is available for free at <https://www.7-zip.org/download.html>.

This software includes part of a modified copy of the `pywebview` Python package,
copyright 2020 Roman Sirokov under the BSD-3-Clause License. The source code for the
original library is available for free at <https://github.com/r0x0r/pywebview>.
