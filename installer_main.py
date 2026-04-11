from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
import tkinter as tk
import ctypes
import winreg
from pathlib import Path
from tkinter import messagebox


APP_NAME = "Periflow"
APP_EXE_NAME = "Periflow.exe"
PAYLOAD_NAME = "Periflow_PC.exe"


def bundle_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def install_dir() -> Path:
    local_app_data = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return local_app_data / "Programs" / APP_NAME


def special_folder_path(csidl: int) -> Path:
    buffer = ctypes.create_unicode_buffer(260)
    result = ctypes.windll.shell32.SHGetFolderPathW(None, csidl, None, 0, buffer)
    if result != 0:
        raise OSError(f"Could not resolve special folder {csidl}.")
    return Path(buffer.value)


def write_uninstaller(target_dir: Path) -> Path:
    uninstall_ps1 = target_dir / "uninstall.ps1"
    uninstall_cmd = target_dir / "uninstall.cmd"
    script = textwrap.dedent(
        f"""
        $ErrorActionPreference = "SilentlyContinue"
        $installRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
        $startMenuDir = Join-Path ([Environment]::GetFolderPath("Programs")) "{APP_NAME}"
        $desktopShortcut = Join-Path ([Environment]::GetFolderPath("DesktopDirectory")) "{APP_NAME}.lnk"
        $regPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}"
        if (Test-Path $desktopShortcut) {{ Remove-Item -LiteralPath $desktopShortcut -Force }}
        if (Test-Path $startMenuDir) {{ Remove-Item -LiteralPath $startMenuDir -Recurse -Force }}
        if (Test-Path $regPath) {{ Remove-Item -LiteralPath $regPath -Recurse -Force }}
        if (Test-Path $installRoot) {{ Remove-Item -LiteralPath $installRoot -Recurse -Force }}
        """
    ).strip()
    uninstall_ps1.write_text(script + "\n", encoding="utf-8")
    uninstall_cmd.write_text(
        '@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1"\r\n',
        encoding="ascii",
    )
    return uninstall_cmd


def create_shortcuts(app_path: Path, uninstall_cmd: Path) -> None:
    desktop_shortcut = special_folder_path(0x10) / f"{APP_NAME}.lnk"
    start_menu_dir = special_folder_path(0x02) / APP_NAME
    start_menu_shortcut = start_menu_dir / f"{APP_NAME}.lnk"
    uninstall_shortcut = start_menu_dir / f"Uninstall {APP_NAME}.lnk"
    start_menu_dir.mkdir(parents=True, exist_ok=True)

    ps_script = textwrap.dedent(
        f"""
        $shell = New-Object -ComObject WScript.Shell
        New-Item -ItemType Directory -Force "{start_menu_dir}" | Out-Null
        $desktop = $shell.CreateShortcut("{desktop_shortcut}")
        $desktop.TargetPath = "{app_path}"
        $desktop.WorkingDirectory = "{app_path.parent}"
        $desktop.IconLocation = "{app_path},0"
        $desktop.Save()
        $start = $shell.CreateShortcut("{start_menu_shortcut}")
        $start.TargetPath = "{app_path}"
        $start.WorkingDirectory = "{app_path.parent}"
        $start.IconLocation = "{app_path},0"
        $start.Save()
        $uninstall = $shell.CreateShortcut("{uninstall_shortcut}")
        $uninstall.TargetPath = "{uninstall_cmd}"
        $uninstall.WorkingDirectory = "{app_path.parent}"
        $uninstall.IconLocation = "{app_path},0"
        $uninstall.Save()
        """
    ).strip()
    subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        check=True,
        capture_output=True,
        text=True,
    )


def register_uninstall(app_path: Path, uninstall_cmd: Path) -> None:
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"Software\Microsoft\Windows\CurrentVersion\Uninstall\{APP_NAME}") as key:
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, str(app_path))
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, APP_NAME)
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, str(app_path.parent))
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, str(uninstall_cmd))
        winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, str(uninstall_cmd))


def install() -> Path:
    root = bundle_root()
    candidates = [
        root / "payload" / PAYLOAD_NAME,
        root / "payload_dist" / PAYLOAD_NAME,
        root / "dist" / PAYLOAD_NAME,
        Path(__file__).resolve().parent / "dist" / PAYLOAD_NAME,
        Path(__file__).resolve().parent / "payload_dist" / PAYLOAD_NAME,
    ]
    source = next((path for path in candidates if path.exists()), None)
    if source is None:
        raise FileNotFoundError(f"Bundled app payload not found. Checked: {', '.join(str(item) for item in candidates)}")

    target_dir = install_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / APP_EXE_NAME
    shutil.copy2(source, target)

    uninstall_cmd = write_uninstaller(target_dir)
    create_shortcuts(target, uninstall_cmd)
    register_uninstall(target, uninstall_cmd)
    return target


def main() -> None:
    root = tk.Tk()
    root.withdraw()
    try:
        app_path = install()
    except Exception as exc:
        messagebox.showerror("Periflow Installer", f"Installation failed:\n{exc}")
        raise SystemExit(1) from exc

    subprocess.Popen([str(app_path)], cwd=str(app_path.parent))
    messagebox.showinfo("Periflow Installer", f"{APP_NAME} has been installed successfully.")


if __name__ == "__main__":
    main()
