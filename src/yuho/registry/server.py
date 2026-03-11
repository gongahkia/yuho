"""Minimal package registry HTTP server.

Implements the registry API for package discovery, install, and publish.
Can serve as a standalone registry or generate a static JSON index for
GitHub Pages hosting.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger("yuho.registry")


@dataclass
class PackageEntry:
    """A package in the registry index."""
    name: str
    version: str
    description: str = ""
    namespace: str = "" # e.g. "singapore"
    checksum: str = ""
    dependencies: List[str] = field(default_factory=list)
    published_at: str = ""


class RegistryIndex:
    """In-memory package index."""
    def __init__(self, data_dir: Optional[str] = None) -> None:
        self._packages: Dict[str, Dict[str, Any]] = {} # name -> version_map
        self._data_dir = Path(data_dir) if data_dir else Path.home() / ".yuho-registry"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _index_path(self) -> Path:
        return self._data_dir / "index.json"

    def _load(self) -> None:
        p = self._index_path()
        if p.exists():
            try:
                self._packages = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                self._packages = {}

    def _save(self) -> None:
        self._index_path().write_text(json.dumps(self._packages, indent=2), encoding="utf-8")

    def search(self, query: str = "", namespace: str = "") -> List[Dict[str, Any]]:
        results = []
        for name, versions in self._packages.items():
            if query and query.lower() not in name.lower():
                continue
            if namespace:
                latest_meta = self.get_package(name)
                ns = (latest_meta or {}).get("namespace", "")
                if ns != namespace:
                    continue
            latest = max(versions.keys()) if versions else ""
            results.append({"name": name, "latest": latest, "versions": list(versions.keys())})
        return results

    def resolve_deps(self, name: str, version: Optional[str] = None, _seen: Optional[set] = None) -> List[str]:
        """Resolve transitive dependencies. Returns list of 'name@version' strings."""
        if _seen is None:
            _seen = set()
        key = f"{name}@{version}" if version else name
        if key in _seen:
            return []
        _seen.add(key)
        pkg = self.get_package(name, version)
        if not pkg:
            return []
        result = [key]
        for dep in pkg.get("dependencies", []):
            dep_name, _, dep_ver = dep.partition("@")
            result.extend(self.resolve_deps(dep_name, dep_ver or None, _seen))
        return result

    def get_package(self, name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        pkg = self._packages.get(name)
        if not pkg:
            return None
        if version:
            return pkg.get(version)
        latest = max(pkg.keys()) if pkg else None
        return pkg.get(latest) if latest else None

    def publish(self, name: str, version: str, metadata: Dict[str, Any]) -> None:
        if name not in self._packages:
            self._packages[name] = {}
        self._packages[name][version] = metadata
        self._save()

    def export_static(self, output_dir: str) -> None:
        """Export as static JSON files for GitHub Pages hosting."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        # index
        (out / "packages.json").write_text(json.dumps(self.search(), indent=2), encoding="utf-8")
        # per-package
        for name, versions in self._packages.items():
            pkg_dir = out / "packages" / name
            pkg_dir.mkdir(parents=True, exist_ok=True)
            (pkg_dir / "index.json").write_text(json.dumps({"name": name, "versions": versions}, indent=2), encoding="utf-8")


class RegistryHandler(BaseHTTPRequestHandler):
    """HTTP handler for the registry server."""

    def _send_json(self, status: int, data: Any) -> None:
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)
        index: RegistryIndex = self.server.index # type: ignore
        if path == "/v1/packages":
            query = qs.get("q", [""])[0]
            namespace = qs.get("namespace", [""])[0]
            self._send_json(200, index.search(query, namespace=namespace))
        elif path.startswith("/v1/packages/") and path.endswith("/deps"):
            parts = path.split("/")
            name = parts[3] if len(parts) > 4 else ""
            deps = index.resolve_deps(name)
            self._send_json(200, {"package": name, "dependencies": deps})
        elif path.startswith("/v1/packages/"):
            parts = path.split("/")
            name = parts[3] if len(parts) > 3 else ""
            version = parts[4] if len(parts) > 4 else None
            pkg = index.get_package(name, version)
            if pkg:
                self._send_json(200, pkg)
            else:
                self._send_json(404, {"error": "Package not found"})
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/v1/packages":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            name = body.get("name", "")
            version = body.get("version", "")
            if not name or not version:
                self._send_json(400, {"error": "name and version required"})
                return
            index: RegistryIndex = self.server.index # type: ignore
            index.publish(name, version, body)
            self._send_json(201, {"published": f"{name}@{version}"})
        else:
            self._send_json(404, {"error": "Not found"})

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug(format, *args)


class RegistryServer(ThreadingHTTPServer):
    def __init__(self, address: tuple, index: RegistryIndex) -> None:
        super().__init__(address, RegistryHandler)
        self.index = index


def run_registry(host: str = "127.0.0.1", port: int = 8082, data_dir: Optional[str] = None) -> None:
    """Start the registry server."""
    index = RegistryIndex(data_dir)
    server = RegistryServer((host, port), index)
    logger.info(f"Registry server at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()

