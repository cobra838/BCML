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

```
py -3.9 -m pip install --force-reinstall "https://raw.githubusercontent.com/cobra838/BCML/master/target/wheels/bcml-3.10.8-cp39-none-win_amd64.whl"
```

## Building from Source

Building from source requires, in addition to the general prerequisites:

-   Python 3.9+

-   Rust 1.99 (nightly)

-   Node.js v14+

Tested versions:

```bash
uv run python --version
# Python 3.14.6

rustc --version
# rustc 1.99.0-nightly (9f36de775 2026-07-19)

node --version
# v26.5.0
```

### Development Environment

Use [uv](https://github.com/astral-sh/uv) to create a CPython 3.14 environment and install the application and build dependencies:

```cmd
uv venv --python 3.14 .build-venv
uv pip install --python .build-venv\Scripts\python.exe -r requirements.txt
uv pip install --python .build-venv\Scripts\python.exe -r requirements-build.txt
```

`requirements.txt` contains the dependencies BCML needs at runtime.
`requirements-build.txt` contains Maturin, MkDocs, and PyInstaller for local builds.


### Development Build

This validates Rust code, rebuilds frontend assets, rebuilds the Rust Python extension, reinstalls the wheel, and packages BCML using PyInstaller.

```cmd
rustup run nightly cargo check
npm --prefix bcml\assets install
npm --prefix bcml\assets run build
.build-venv\Scripts\python.exe -m mkdocs build -d .\bcml\assets\help
rustup run nightly .build-venv\Scripts\maturin.exe build --release --interpreter .build-venv\Scripts\python.exe
uv pip install --python .build-venv\Scripts\python.exe --force-reinstall --no-deps --no-index --find-links .\target\wheels bcml
for /f "delims=" %P in ('dir /b .build-venv\Lib\site-packages\bcml\bcml*.pyd') do copy /y ".build-venv\Lib\site-packages\bcml\%P" bcml\
.build-venv\Scripts\python.exe -m PyInstaller --onedir --windowed --name BCML --distpath .\0dist --workpath .\build\pyinstaller --collect-all bcml --collect-all aamp --collect-all byml --collect-all botw_utils --collect-all rstb --icon bcml\data\bcml.ico --add-data ".build-venv\Lib\site-packages\aamp\botw_hashed_names.txt;aamp" bcml\__main__.py
```

### Quick Rebuild

Use this after dependencies are already installed.

```cmd
rustup run nightly cargo check
npm --prefix bcml\assets run build
rustup run nightly .build-venv\Scripts\maturin.exe build --release --interpreter .build-venv\Scripts\python.exe
uv pip install --python .build-venv\Scripts\python.exe --force-reinstall --no-deps --no-index --find-links .\target\wheels bcml
for /f "delims=" %P in ('dir /b .build-venv\Lib\site-packages\bcml\bcml*.pyd') do copy /y ".build-venv\Lib\site-packages\bcml\%P" bcml\
.build-venv\Scripts\python.exe -m PyInstaller --onedir --windowed --name BCML --distpath .\0dist --workpath .\build\pyinstaller --collect-all bcml --collect-all aamp --collect-all byml --collect-all botw_utils --collect-all rstb --icon bcml\data\bcml.ico --add-data ".build-venv\Lib\site-packages\aamp\botw_hashed_names.txt;aamp" bcml\__main__.py
```

### Build wheel only

```cmd
rustup run nightly cargo check
npm --prefix bcml\assets run build
.build-venv\Scripts\python.exe -m mkdocs build -d .\bcml\assets\help
rustup run nightly .build-venv\Scripts\maturin.exe build --release --interpreter .build-venv\Scripts\python.exe
uv pip install --python .build-venv\Scripts\python.exe --force-reinstall --no-deps --no-index --find-links .\target\wheels bcml
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
