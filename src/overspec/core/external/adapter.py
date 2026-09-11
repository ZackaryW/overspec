"""Authenticated read-only Saucepan API boundary; no acquisition or mirroring."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from zuu.case2 import FileSystemSnapshot
from zuu.case5 import ConfinedPath, TargetState

from ..storage import digest


def create_client(connection):
    try:
        from saucepan_sdk import Saucepan
    except ImportError:
        raise ValueError(
            "Install the overspec[saucepan] extra and the Saucepan executable to use this connection"
        ) from None
    return Saucepan(app="overspec", marker=connection.marker, binary=connection.binary)


def call(client, method, *args):
    try:
        return getattr(client, method)(*args)
    except Exception:  # noqa: BLE001 -- sanitize arbitrary SDK/backend errors here
        # SDK stderr may contain arbitrary backend data. Keep proof material private.
        raise ValueError(
            f"Saucepan {method} failed; check the executable, overspec marker and scoped store, then retry"
        ) from None


@dataclass(frozen=True)
class Repository:
    root: Path
    artifact: dict

    def origin(self, path):
        return f"saucepan:{self.artifact['source_id']}/{path.relative_to(self.root).as_posix()}"

    def provenance(self, path, layout):
        return {
            "source_id": self.artifact["source_id"],
            "snapshot": self.artifact["snapshot_id"],
            "revision": self.artifact["revision"],
            "path": path.relative_to(self.root).as_posix(),
            "layout": layout,
        }


def verify_content(root, manifest):
    if not isinstance(manifest, dict):
        raise ValueError("Saucepan invalid content manifest")  # noqa: TRY004 -- CLI validation contract
    snapshot = FileSystemSnapshot.capture([root])
    actual = {e.relative_path: e for e in snapshot.entries if e.relative_path != "."}
    if actual.keys() != manifest.keys():
        raise ValueError("Saucepan content does not match its manifest")
    for name, record in manifest.items():
        if (
            not isinstance(record, dict)
            or set(record) != {"digest", "executable"}
            or type(record["executable"]) is not bool
        ):
            raise ValueError("Saucepan invalid file record")
        content = actual[name].content
        observed = hashlib.sha256(content).hexdigest() if content is not None else None
        if observed != record["digest"]:
            raise ValueError("Saucepan content digest mismatch; reacquire the source")


def repositories(client):
    view = call(client, "view")
    if (
        not isinstance(view, dict)
        or type(view.get("version")) is not int
        or view["version"] != 1
        or view.get("app") != "overspec"
        or not isinstance(view.get("entries"), dict)
    ):
        raise ValueError("Saucepan unsupported view or wrong app scope")
    if call(client, "verify", view) != {"verified": True}:
        raise ValueError("Saucepan view proof could not be verified")
    grouped = {}
    for key, item in view["entries"].items():
        if (
            not isinstance(item, dict)
            or item.get("id") != key
            or not {
                "source_id",
                "snapshot_id",
                "revision",
                "folder",
                "files",
                "source",
                "content_id",
            }
            <= item.keys()
            or any(
                not isinstance(item[k], str) or not item[k]
                for k in ("source_id", "snapshot_id", "revision", "content_id")
            )
            or not re.fullmatch(r"[0-9a-f]{64}", item["source_id"])
            or not isinstance(item["folder"], (str, type(None)))
            or not isinstance(item["source"], dict)
            or item["source"].get("provider") not in ("git", "url", "local")
        ):
            raise ValueError("Saucepan malformed artifact")
        grouped.setdefault(item["source_id"], []).append(item)
    roots, excluded, currents = [], [], {}
    for source_id, items in sorted(grouped.items()):
        state = call(client, "history", source_id)
        if (
            not isinstance(state, dict)
            or "current" not in state
            or not isinstance(state["current"], (dict, type(None)))
        ):
            raise ValueError("Saucepan missing or malformed source history")
        current = state["current"]
        if current is not None and not isinstance(current.get("id"), str):
            raise ValueError("Saucepan invalid current snapshot")
        currents[source_id] = current
        selected = [
            item
            for item in items
            if current is not None
            and item["folder"] is None
            and item["snapshot_id"] == current["id"]
        ]
        if not selected:
            excluded.append(
                {
                    "source_id": source_id,
                    "reason": "Acquire the whole current root under Saucepan's overspec scope; historical, pinned-only and folder-only content is excluded",
                }
            )
            continue
        if len(selected) != 1:
            raise ValueError("Saucepan ambiguous current root")
        item = selected[0]
        for key in ("revision", "files", "content_id"):
            if current.get(key) != item[key]:
                raise ValueError(
                    "Saucepan current root metadata disagrees with artifact"
                )
        location = call(client, "path", item["id"])
        if not isinstance(location, str) or not Path(location).is_absolute():
            raise ValueError("Saucepan current root is unavailable")
        root = Path(location)
        try:
            ConfinedPath(root.relative_to(root.anchor).as_posix()).inspect(
                Path(root.anchor), allowed=(TargetState.DIRECTORY,)
            )
            verify_content(root, item["files"])
        except (OSError, ValueError) as exc:
            raise ValueError(f"Saucepan root verification failed: {exc}") from None
        roots.append(Repository(root.resolve(strict=True), item))
    return roots, excluded, digest({"view": view, "current": currents})
