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

## Setup

There are two main ways to install BCML.

### PyPI

Install Python 3.7 - 3.10 (**64 bit version**), making sure to add it to your PATH, and then
run `pip install bcml`.

**Note for Linux users**: Because of the ways different distros handle Python packaging,
it often works better to install BCML in some contained environment. There are a few options for
this. The easiest would be to use [`pipx`](https://github.com/pypa/pipx). You can install `pipx`
through pip, and then run `pipx install bcml`. In some cases you might need to also run `pipx
inject bcml pywebview[qt]`.

**Note for Linux white screen bug**: Try setting the environmental variable: `QTWEBENGINE_DISABLE_SANDBOX=1`.

Another option for Linux users is using a virtual environment ("venv"). To do so, you can run
something like this:

```sh
python -m venv bcml_env
source bcml_env/bin/activate # will activate the venv
pip install bcml
```

**Full Linux Example with CEMU**

`sudo pacman -S python39` Adjust for you distribution, arch defaults to a newer python

```mkdir -p ~/.local/share/cemu/graphicPacks/BreathOfTheWild_BCML
python3.9 -m venv /.local/bcml_env
source ~/.local/bcml_env/bin/activate
python3.9 -m pip install bcml
~/.local/bcml_env/bin/bcml
```

to launch BCML in the future

`source ~/.local/bcml_env/bin/activate; ~/.local/bcml_env/bin/bcml`

- In BCML, check 'without cemu' and set export path to '~/.local/share/cemu/graphicPacks/BreathOfTheWild_BCML'
- install your mods
- execute `curl https://pastebin.com/raw/igCLK2tz -o ~/.local/share/cemu/graphicPacks/BreathOfTheWild_BCML/rules.txt`

* If your mods still don't load, verify that ~/.local/share/cemu/graphicPacks/BreathOfTheWild_BCML/rules.txt exist and try 'disable links for master mod' in BCML settings

## Install from wheel

```
py -3.9 -m pip install --force-reinstall "https://raw.githubusercontent.com/cobra838/BCML/master/target/wheels/bcml-3.10.8-cp39-none-win_amd64.whl"
```

## Building from Source

Building from source requires, in addition to the general prerequisites:

-   Python 3.9 64 bit

-   Rust 1.71 (nightly)

-   Node.js v14+

Tested versions:

```bash
rustc --version
# rustc 1.71.0-nightly (39c6804b9 2023-04-19)

node --version
# v24.13.1
```

### Python Dependencies

```bash
pip install -r requirements.txt
python.exe -m pip install --force-reinstall \
    pip \
    wheel \
    setuptools \
    pyinstaller \
    mkdocs \
    mkdocs-material \
    "maturin>=0.12,<0.13"
```

Tested versions:

wheel 0.46.3  
setuptools 82.0.1  
pyinstaller 6.20.0
mkdocs 1.6.1  
mkdocs-material 9.7.6
maturin 0.12.20  


### Development Build

This validates Rust code, rebuilds frontend assets, rebuilds the Rust Python extension, reinstalls the wheel, and packages BCML using PyInstaller.

```bash
set -e
rm -f Cargo.lock
rustc --version
rustup show active-toolchain
cargo --version
cargo check
cd bcml/assets
npm run build
cd ../..
py -3.9 -m mkdocs build -d ./bcml/assets/help
maturin build --release --interpreter python
wheel="$(ls -t ./target/wheels/*.whl | head -n 1)"
py -3.9 -m pip install --force-reinstall "$wheel"
PYD_PATH=$(py -3.9 -c "import sysconfig; print(sysconfig.get_paths()['purelib'] + r'/bcml/bcml.cp39-win_amd64.pyd')")
py -3.9 -m PyInstaller --onedir --windowed --name BCML \
  --distpath "./0dist" \
  --workpath "./build/pyinstaller" \
  --collect-all bcml \
  --collect-all aamp \
  --collect-all byml \
  --collect-all botw_utils \
  --collect-all rstb \
  --icon "bcml/data/bcml.ico" \
  --add-binary "$PYD_PATH;bcml" \
  bcml/__main__.py
```

### Quick Rebuild

Use this after dependencies are already installed.

```bash
set -e
rm -f Cargo.lock
rustc --version
rustup show active-toolchain
cargo --version
cargo check
cd bcml/assets
npm run build
cd ../..
maturin build --release --interpreter python
wheel="$(ls -t ./target/wheels/*.whl | head -n 1)"
py -3.9 -m pip install --force-reinstall "$wheel"
PYD_PATH=$(py -3.9 -c "import sysconfig; print(sysconfig.get_paths()['purelib'] + r'/bcml/bcml.cp39-win_amd64.pyd')")
py -3.9 -m PyInstaller --onedir --windowed --name BCML \
  --distpath "./0dist" \
  --workpath "./build/pyinstaller" \
  --collect-all bcml \
  --collect-all aamp \
  --collect-all byml \
  --collect-all botw_utils \
  --collect-all rstb \
  --icon "bcml/data/bcml.ico" \
  --add-binary "$PYD_PATH;bcml" \
  bcml/__main__.py
```

### Build wheel only

```bash
set -e
rm -f Cargo.lock
rustc --version
rustup show active-toolchain
cargo --version
cargo check
cd bcml/assets
npm run build
cd ../..
py -3.9 -m mkdocs build -d ./bcml/assets/help
maturin build --release --interpreter python
wheel="$(ls -t ./target/wheels/*.whl | head -n 1)"
py -3.9 -m pip install --force-reinstall "$wheel"
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
