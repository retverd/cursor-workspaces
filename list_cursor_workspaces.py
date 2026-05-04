from __future__ import annotations

import json
import os
import sys
from pathlib import Path, PureWindowsPath
from urllib.parse import unquote, urlparse


def get_workspace_storage_candidates() -> list[Path]:
    candidates: list[Path] = []

    appdata = os.environ.get("APPDATA")
    if appdata:
        candidates.append(Path(appdata) / "Cursor" / "User" / "workspaceStorage")

    candidates.append(Path(r"C:\ProgramData\Cursor\User\workspaceStorage"))
    return candidates


def find_workspace_storage() -> Path | None:
    for candidate in get_workspace_storage_candidates():
        if candidate.is_dir():
            return candidate

    return None


def decode_windows_file_uri(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme.lower() != "file":
        return value

    path = unquote(parsed.path)
    netloc = unquote(parsed.netloc)

    if netloc:
        return str(PureWindowsPath(f"//{netloc}{path}"))

    if len(path) >= 3 and path[0] == "/" and path[2] == ":":
        path = path[1:]

    if len(path) >= 2 and path[1] == ":":
        path = path[0].upper() + path[1:]

    return str(PureWindowsPath(path))


def read_workspace_folder(workspace_json: Path) -> str | None:
    try:
        with workspace_json.open("r", encoding="utf-8") as file:
            workspace = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"{workspace_json.parent.name} -> не удалось прочитать workspace.json: {error}", file=sys.stderr)
        return None

    folder = workspace.get("folder")
    if not isinstance(folder, str):
        return None

    return decode_windows_file_uri(folder)


def get_folder_status(folder_path: str) -> str:
    return "e" if Path(folder_path).is_dir() else "n"


def iter_workspace_entries(workspace_storage: Path):
    for child in sorted(workspace_storage.iterdir(), key=lambda item: item.name.lower()):
        if not child.is_dir():
            continue

        workspace_json = child / "workspace.json"
        if not workspace_json.is_file():
            continue

        folder = read_workspace_folder(workspace_json)
        if folder is None:
            continue

        yield child.name, folder


def main() -> int:
    workspace_storage = find_workspace_storage()
    if workspace_storage is None:
        candidates = "\n".join(str(candidate) for candidate in get_workspace_storage_candidates())
        print(f"Не найдена папка workspaceStorage. Проверенные пути:\n{candidates}", file=sys.stderr)
        return 1

    for folder_name, workspace_path in iter_workspace_entries(workspace_storage):
        print(f"{folder_name} -> {get_folder_status(workspace_path)} -> {workspace_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
