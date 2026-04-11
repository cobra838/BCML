import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from multiprocessing import set_start_method, Process, freeze_support
from os import chmod  # pylint: disable=ungrouped-imports
from pathlib import Path
from random import randint
from subprocess import Popen, DEVNULL
from shutil import rmtree
from threading import Thread
from time import sleep

import webview

from bcml import DEBUG, util, _oneclick
import bcml
from bcml.util import Messager, LOG, SYSTEM
from bcml._api import Api
from bcml._server import start_server

logger = None  # pylint: disable=invalid-name


def stop_it(messager: Messager = None):
    if messager:
        messager.save()
    try:
        del globals()["logger"]
    except KeyError:
        pass
    if SYSTEM == "Windows":
        Popen(
            "taskkill /F /IM subprocess.exe /T".split(),
            stdout=DEVNULL,
            stderr=DEVNULL,
            creationflags=0x08000000,
        )
        rmtree(Path() / "blob_storage", ignore_errors=True)
        rmtree(Path() / "webrtc_event_logs", ignore_errors=True)
        return
    else:
        os.killpg(0, 9)


def configure_cef(debug):
    from webview.platforms.cef import (  # pylint: disable=import-outside-toplevel
        settings,
    )

    cache = util.get_storage_dir() / "cef_cache"
    cef_settings = {
        "cache_path": str(cache),
        "context_menu": {"enabled": debug, "devtools": True},
    }
    if getattr(sys, "frozen", False):
        bundle_dir = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        cef_bundle = bundle_dir / "cefpython3"
        if cef_bundle.exists():
            cef_settings.update(
                {
                    "resources_dir_path": str(cef_bundle),
                    "locales_dir_path": str(cef_bundle / "locales"),
                    "browser_subprocess_path": str(cef_bundle / "subprocess.exe"),
                }
            )
    settings.update(cef_settings)
    if not cache.exists():
        cache.mkdir(parents=True, exist_ok=True)


def main(debug: bool = False):
    freeze_support()
    set_start_method("spawn", True)
    global logger  # pylint: disable=invalid-name,global-statement
    logger = None

    try:
        if SYSTEM != "Windows":
            os.setpgrp()
        LOG.parent.mkdir(parents=True, exist_ok=True)
        for folder in util.get_work_dir().glob("*"):
            rmtree(folder)
        (util.get_data_dir() / "tmp_settings.json").unlink()
    except (FileNotFoundError, OSError, PermissionError):
        pass

    _oneclick.register_handlers()
    oneclick = Thread(target=_oneclick.listen)
    oneclick.daemon = True
    oneclick.start()

    server_port = util.get_open_port()
    server = Process(target=start_server, args=(server_port,))
    server.daemon = True
    server.start()
    host = f"http://localhost:{server_port}"

    api = Api(host)

    if not debug:
        debug = DEBUG or "bcml-debug" in sys.argv or "--debug" in sys.argv

    gui: str
    if SYSTEM == "Windows":
        from webview.platforms.winforms import _is_chromium

        if _is_chromium():
            gui = "edgechromium"
        else:
            util.download_webview2()
    else:
        gui = "qt"
        os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"

    now = datetime.now()
    if (
        now.month == 4
        and now.day == 1
        and not (util.get_data_dir() / ".fooled").exists()
    ):
        (util.get_data_dir() / ".fooled").write_bytes(b"")
        url = (
            [
                "https://www.youtube.com/embed/Lrj2Hq7xqQ8",
                "https://www.youtube.com/embed/8B1fu3AuDrQ",
                "https://www.youtube.com/embed/jRMHp7_kPec",
                "https://www.youtube.com/embed/N9qYF9DZPdw",
                "https://www.youtube.com/embed/j1FGaCNN1aw",
            ][randint(0, 4)]
        ) + "?autoplay=1"
        width, height = 640, 360
    else:
        url = f"{host}/index.html"
        width, height = 907, 680

    api.window = webview.create_window(
        "BOTW Cross-Platform Mod Loader",
        url=url,
        js_api=api,
        text_select=DEBUG,
        width=width,
        height=height,
        min_size=(width if width == 750 else 820, 600),
    )
    logger = Messager(api.window)
    api.window.events.closing += stop_it

    # messager = Messager(api.window)
    # with redirect_stderr(sys.stdout):
    #     with redirect_stdout(messager):  # type: ignore
    sleep(0.25)
    webview.start(gui=gui, debug=debug, http_server=True, func=_oneclick.process_arg)
    api.cleanup()
    stop_it()  # messager=messager)


def main_debug():
    main(True)


if __name__ == "__main__":
    main()
