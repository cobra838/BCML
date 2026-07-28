import base64
import csv
import json
import struct
import shutil
from configparser import ConfigParser
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Dict

import oead
import yaml
from aamp import yaml_util as ayu
from aamp import ParameterIO, ParameterObject, ParameterList, Writer
from byml import yaml_util as byu
from bcml import util, install, bcml as rsext

# from bcml.mergers.texts import read_msbt
from bcml.mergers.rstable import RstbMerger, get_stock_rstb
from bcml.util import RulesParser, TempSettingsContext

WIIU_TITLE_IDS = {"00050000101C9300", "00050000101C9400", "00050000101C9500"}
SWITCH_TITLE_IDS = {"01007EF00011E000", "01007EF00011F001"}


def detect_old_mod_platform(mod_dir: Path, rules_path: Path = None) -> str:
    switch_paths = {
        "01007EF00011E000",
        "01007EF00011F001",
        "01007ef00011e000",
        "01007ef00011f001",
        "base",
        "dlc",
    }
    wiiu_paths = {"content", "aoc", "Content", "Aoc"}
    if any((mod_dir / path).exists() for path in switch_paths):
        return "switch"
    if any((mod_dir / path).exists() for path in wiiu_paths):
        return "wiiu"

    probe_files = [
        mod_dir / "logs" / "packs.log",
        mod_dir / "logs" / "rstb.log",
    ]
    for probe in probe_files:
        if not probe.exists():
            continue
        text = probe.read_text(encoding="utf-8", errors="ignore")
        if "01007EF00011E000/romfs" in text or "01007EF00011F001/romfs" in text:
            return "switch"
        if "content/" in text or "content\\" in text or "aoc/" in text or "aoc\\" in text:
            return "wiiu"

    if rules_path and rules_path.exists():
        rules = RulesParser()
        rules.read(str(rules_path))
        raw_ids = str(rules["Definition"].get("titleIds", ""))
        title_ids = {title_id.strip() for title_id in raw_ids.split(",") if title_id.strip()}
        if title_ids & SWITCH_TITLE_IDS:
            return "switch"
        if title_ids & WIIU_TITLE_IDS:
            return "wiiu"

    return "wiiu" if util.get_settings("wiiu") else "switch"


def convert_old_mods(source: Path = None):
    mod_dir = util.get_modpack_dir()
    old_path = source or util.get_cemu_dir() / "graphicPacks" / "BCML"
    print("Copying old mods...")
    shutil.rmtree(mod_dir, ignore_errors=True)
    shutil.copytree(old_path, mod_dir)
    print("Converting old mods...")
    for i, mod in enumerate(
        sorted({d for d in mod_dir.glob("*") if d.is_dir() and d.name != "9999_BCML"})
    ):
        print(f"Converting {mod.name[4:]}")
        try:
            convert_old_mod(mod, True)
        except Exception as err:
            shutil.rmtree(mod)
            install.refresh_merges()
            raise RuntimeError(
                f"BCML was unable to convert {mod.name[4:]}. Error: {str(err)}. Your old "
                f"mods have not been modified. {i} mod(s) were successfully imported."
            ) from err
    shutil.rmtree(old_path, ignore_errors=True)


def convert_old_mod(mod: Path, delete_old: bool = False):
    platform = detect_old_mod_platform(mod, mod / "rules.txt")
    rules_to_info(mod / "rules.txt", platform=platform, delete_old=delete_old)
    if (mod / "logs").exists():
        with TempSettingsContext({"wiiu": platform == "wiiu"}):
            convert_old_logs(mod)


def convert_old_settings():
    old_settings = ConfigParser()
    old_settings.read(str(util.get_data_dir() / "settings.ini"))
    cemu_dir = old_settings["Settings"]["cemu_dir"]
    mlc_dir = old_settings["Settings"]["mlc_dir"]
    game_dir = old_settings["Settings"]["game_dir"]
    update_dir = util.guess_update_dir(Path(mlc_dir), Path(game_dir))
    dlc_dir = util.guess_aoc_dir(Path(mlc_dir), Path(game_dir))
    settings = {
        "cemu_dir": cemu_dir,
        "game_dir": game_dir,
        "game_dir_nx": "",
        "load_reverse": old_settings["Settings"]["load_reverse"] == "True",
        "update_dir": str(update_dir or ""),
        "dlc_dir": str(dlc_dir or ""),
        "dlc_dir_nx": "",
        "store_dir": str(util.get_data_dir()),
        "site_meta": old_settings["Settings"]["site_meta"],
        "no_guess": old_settings["Settings"]["guess_merge"] == "False",
        "lang": old_settings["Settings"]["lang"],
        "no_cemu": False,
        "wiiu": True,
    }
    setattr(util.get_settings, "settings", settings)
    (util.get_data_dir() / "settings.ini").unlink()
    util.save_settings()


def parse_rules(rules_path: Path, platform: str = "wiiu") -> Dict[str, Any]:
    rules = RulesParser()
    rules.read(str(rules_path))
    info = {
        "name": str(rules["Definition"]["name"]).strip("\"' "),
        "desc": str(rules["Definition"].get("description", "")).strip("\"' "),
        "url": str(rules["Definition"].get("url", "")).strip("\"' "),
        "image": str(rules["Definition"].get("image", "")).strip("\"' "),
        "version": "1.0.0",
        "depends": [],
        "options": {},
        "platform": platform,
        "priority": 100,
    }
    id_string = f"{info['name']}=={info['version']}"
    info["id"] = base64.urlsafe_b64encode(id_string.encode("utf8")).decode("utf8")
    try:
        info["priority"] = int(rules["Definition"]["fsPriority"])
    except KeyError:
        info["priority"] = int(getattr(rules["Definition"], "fspriority", 100))
    return info


def rules_to_info(
    rules_path: Path, platform: str = "wiiu", delete_old: bool = False
):
    print("Converting meta file...")
    info = parse_rules(rules_path, platform=platform)
    (rules_path.parent / "info.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2)
    )
    if delete_old:
        rules_path.unlink()


def convert_old_logs(mod_dir: Path):
    print("Upgrading old logs...")
    if (mod_dir / "logs" / "packs.log").exists():
        print("Upgrading pack log...")
        _convert_pack_log(mod_dir)
    if (mod_dir / "logs" / "rstb.log").exists():
        print("Upgrading RSTB log...")
        _convert_rstb_log(mod_dir)
    if any((mod_dir / "logs").glob("texts_*.yml")) or any(
        (mod_dir / "logs").glob("newtexts_*.sarc")
    ):
        print("Upgrading text logs...")
        _convert_text_logs(mod_dir / "logs")
    for log in {l for l in mod_dir.glob("logs/*.yml") if not "texts" in l.stem}:
        if log.name == "deepmerge.yml":
            print("Upgrading deep merge log...")
            _convert_aamp_log(log)
        elif log.name == "gamedata.yml":
            print("Upgrading game data log...")
            _convert_gamedata_log(log)
        elif log.name == "savedata.yml":
            print("Upgrading save data log...")
            _convert_savedata_log(log)
        elif log.name == "map.yml":
            print("Upgrading map log...")
            _convert_map_log(log)
        else:
            pass


def _convert_rstb_log(mod: Path):
    rstb_log = mod / "logs" / "rstb.log"
    rstb_json = mod / "logs" / "rstb.json"
    base_diff = {}
    merger = RstbMerger()
    merger._table = get_stock_rstb()
    with rstb_log.open("r", encoding="utf-8", newline="") as rlog:
        reader = csv.DictReader(rlog)
        if reader.fieldnames and "rstb" in reader.fieldnames:
            for row in reader:
                name = str(row.get("name", "")).strip()
                if not name:
                    raw_path = str(row.get("path", "")).strip().replace("\\", "/")
                    name = raw_path.split("//", 1)[-1].replace(".s", ".")
                try:
                    size = int(str(row.get("rstb", "")).strip())
                except ValueError:
                    continue
                if name and not merger.should_exclude(name, size):
                    base_diff[name] = size
    if base_diff:
        rstb_json.write_text(
            json.dumps(base_diff, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
    try:
        with util.start_pool() as pool:
            files = install.find_modded_files(mod, pool=pool)
            merger = RstbMerger()
            merger.set_pool(pool)
            merger.log_diff(mod, files)
    except Exception:
        if not base_diff:
            raise
    if base_diff and rstb_json.exists():
        recalc_diff = json.loads(rstb_json.read_text(encoding="utf-8"))
        rstb_json.write_text(
            json.dumps(
                {**base_diff, **recalc_diff},
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
    rstb_log.unlink()


def _convert_pack_log(mod: Path):
    packs = {}
    with (mod / "logs" / "packs.log").open("r") as rlog:
        csv_loop = csv.reader(rlog)
        for row in csv_loop:
            if "logs" in str(row[1]) or str(row[0]) == "name":
                continue
            packs[str(row[0])] = Path(str(row[1])).as_posix().replace("\\", "/")
    (mod / "logs" / "packs.log").unlink()
    (mod / "logs" / "packs.json").write_text(
        json.dumps(packs, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _convert_aamp_log(log: Path):
    loader = yaml.CLoader
    ayu.register_constructors(loader)
    doc = yaml.load(log.read_text("utf-8"), Loader=loader)
    pio = ParameterIO("log", 0)
    root = ParameterList()
    for file, plist in doc.items():
        if not plist.lists:
            continue
        root.set_list(file, plist.list("param_root"))
    file_table = ParameterObject()
    for i, file in enumerate(doc):
        if not doc[file].lists:
            continue
        file_table.set_param(f"File{i}", file)
    root.set_object("FileTable", file_table)
    pio.set_list("param_root", root)
    log.unlink()
    log.with_suffix(".aamp").write_bytes(Writer(pio).get_bytes())


def _convert_text_log(log: Path) -> dict:
    lang = log.stem[6:]
    data = yaml.safe_load(log.read_text("utf-8"))
    log.unlink()
    return {lang: {file: data[file]["entries"] for file in data}}


def _read_msbt_py(data: bytes) -> dict:
    bom = data[8:10]
    endian = ">" if bom == b"\xfe\xff" else "<"

    def u16(offset: int) -> int:
        return struct.unpack_from(endian + "H", data, offset)[0]

    def u32(offset: int) -> int:
        return struct.unpack_from(endian + "I", data, offset)[0]

    def read_utf16z(start: int, limit: int) -> str:
        chars = []
        pos = start
        while pos + 1 < limit:
            val = u16(pos)
            pos += 2
            if val == 0:
                break
            chars.append(chr(val))
        return "".join(chars)

    labels = {}
    lbl1 = data.index(b"LBL1")
    group_count = u32(lbl1 + 0x10)
    for i in range(group_count):
        count = u32(lbl1 + 0x14 + i * 8)
        offset = u32(lbl1 + 0x18 + i * 8)
        pos = lbl1 + 0x10 + offset
        for _ in range(count):
            size = data[pos]
            pos += 1
            label = data[pos : pos + size].decode("utf-8")
            pos += size
            labels[u32(pos)] = label
            pos += 4

    attributes = {}
    if b"ATR1" in data:
        atr1 = data.index(b"ATR1")
        attr_count = u32(atr1 + 0x10)
        attr_base = atr1 + 0x10
        attr_end = atr1 + 0x10 + u32(atr1 + 4)
        for i in range(attr_count):
            offset = u32(atr1 + 0x18 + i * 4)
            attributes[i] = read_utf16z(attr_base + offset, attr_end)

    def flush_text(chars, contents):
        if chars:
            text = "".join(chars)
            contents.append({"text": text})
            chars.clear()

    def parse_contents(raw: bytes) -> list:
        contents = []
        chars = []
        pos = 0
        while pos + 1 < len(raw):
            val = struct.unpack_from(endian + "H", raw, pos)[0]
            pos += 2
            if val == 0:
                break
            if val != 0x000E:
                chars.append(chr(val))
                continue

            flush_text(chars, contents)
            kind = struct.unpack_from(endian + "H", raw, pos)[0]
            pos += 2
            if kind == 1 and pos + 3 < len(raw):
                length = struct.unpack_from(endian + "H", raw, pos)[0]
                unknown = struct.unpack_from(endian + "H", raw, pos + 2)[0]
                pos += 4
                words = []
                for _ in range(length):
                    if pos + 1 >= len(raw):
                        break
                    words.append(struct.unpack_from(endian + "H", raw, pos)[0])
                    pos += 2
                contents.append(
                    {
                        "control": {
                            "kind": "choice",
                            "choice_labels": words[:-2] if len(words) >= 2 else [],
                            "selected_index": words[-1] if len(words) >= 1 else 0,
                            "cancel_index": words[-2] if len(words) >= 2 else 0,
                            "unknown": unknown,
                        }
                    }
                )
            elif kind == 2 and pos + 5 < len(raw):
                variable_kind = struct.unpack_from(endian + "H", raw, pos)[0]
                pos += 6
                name_chars = []
                while pos + 1 < len(raw):
                    ch = struct.unpack_from(endian + "H", raw, pos)[0]
                    pos += 2
                    if ch == 0:
                        break
                    name_chars.append(chr(ch))
                contents.append(
                    {
                        "control": {
                            "kind": "variable",
                            "variable_kind": variable_kind,
                            "name": "".join(name_chars),
                        }
                    }
                )
            elif kind == 3 and pos + 5 < len(raw):
                pos += 4
                packed = struct.unpack_from(endian + "H", raw, pos)[0]
                pos += 2
                contents.append(
                    {
                        "control": {
                            "kind": "sound",
                            "unknown": [packed >> 8, packed & 0xFF],
                        }
                    }
                )
            else:
                break
        flush_text(chars, contents)
        return contents

    txt2 = data.index(b"TXT2")
    txt_count = u32(txt2 + 0x10)
    txt_base = txt2 + 0x10
    txt_end = txt2 + 0x10 + u32(txt2 + 4)
    offsets = [u32(txt2 + 0x14 + i * 4) for i in range(txt_count)]
    entries = {}
    for i, offset in enumerate(offsets):
        start = txt_base + offset
        end = txt_base + (
            offsets[i + 1] if i + 1 < len(offsets) else (txt_end - txt_base)
        )
        entries[labels.get(i, str(i))] = {
            "attributes": attributes.get(i, ""),
            "contents": parse_contents(data[start:end]),
        }
    return {"entries": entries}


def _read_msbt(data: bytes) -> dict:
    if hasattr(rsext.mergers.texts, "read_msbt"):
        return rsext.mergers.texts.read_msbt(data)
    return _read_msbt_py(data)


def _convert_text_logs(logs_path: Path):
    diffs = {}
    with util.start_pool() as pool:
        for diff in pool.imap_unordered(
            _convert_text_log, logs_path.glob("texts_*.yml")
        ):
            diffs.update(diff)
    fails = set()
    for text_pack in logs_path.glob("newtexts_*.sarc"):
        lang = text_pack.stem[9:]
        sarc = oead.Sarc(text_pack.read_bytes())
        for file in sarc.get_files():
            if lang not in diffs:
                diffs[lang] = {}
            try:
                diffs[lang].update(
                    {
                        file.name.replace(".msbt", ".msyt"): (
                            _read_msbt(bytes(file.data))["entries"]
                        )
                    }
                )
            except RuntimeError:
                print(
                    f"Warning: {file.name} could not be processed and will not be used"
                )
                fails.add(file.name)
                continue
        util.vprint(f"{len(fails)} text files failed to process:\n{fails}")
        text_pack.unlink()
    if diffs:
        (logs_path / "texts.json").write_text(
            json.dumps(diffs, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def _convert_gamedata_log(log: Path):
    diff = oead.byml.from_text(log.read_text("utf-8"))
    log.write_text(
        oead.byml.to_text(
            oead.byml.Dictionary(
                {
                    data_type: {"add": data, "del": oead.byml.Array()}
                    for data_type, data in diff.items()
                }
            )
        ),
        encoding="utf-8",
    )


def _convert_savedata_log(log: Path):
    diff = oead.byml.from_text(log.read_text("utf-8"))
    log.write_text(
        oead.byml.to_text(oead.byml.Dictionary({"add": diff, "del": oead.byml.Array()})),
        encoding="utf-8",
    )


def _convert_map_log(log: Path):
    loader = yaml.CLoader
    byu.add_constructors(loader)
    diff = yaml.load(log.read_text("utf-8"), Loader=loader)
    new_diff = {}
    for unit, changes in diff.items():
        new_changes = {
            "add": changes["add"],
            "del": changes["del"],
            "mod": {str(hashid): actor for hashid, actor in changes["mod"].items()},
        }
        new_diff[unit] = new_changes
    dumper = yaml.CDumper
    byu.add_representers(dumper)
    log.write_text(
        yaml.dump(new_diff, Dumper=dumper, allow_unicode=True), encoding="utf-8"
    )
