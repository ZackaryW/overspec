"""Immutable source documents and shared filesystem snapshot reads."""

from dataclasses import dataclass

from zuu.case2 import FileSystemSnapshot


@dataclass(frozen=True)
class Document:
    origin: str
    content: bytes
    provenance: dict | None = None


class DocumentReader:
    def __init__(self):
        self.contents = {}
        self.evidence = []

    def read(self, paths, describe):
        identities = {p: (p.stat().st_dev, p.stat().st_ino) for p in paths}
        pending = {}
        for path, identity in identities.items():
            if identity not in self.contents:
                pending.setdefault(identity, path)
        if pending:
            snapshot = FileSystemSnapshot.capture(pending.values())
            self.evidence.append(snapshot)
            for entry in snapshot.files:
                path = snapshot.roots[entry.root_index]
                self.contents[identities[path]] = entry.content
        result = []
        for path in paths:
            origin, provenance = describe(path)
            result.append(Document(origin, self.contents[identities[path]], provenance))
        return result
