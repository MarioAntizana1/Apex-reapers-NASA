"""Descarga HTTP paralela por rangos, con reanudacion y SHA-256.

Uso:
    python Scripts/util_descarga_paralela.py URL DESTINO [--hilos 12]

Escribe primero DESTINO.part, reanuda desde el tamano existente y solo
renombra a DESTINO cuando el fichero tiene el tamano exacto del servidor.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import threading
import time
from pathlib import Path

import requests

UA = "AresAtlas/1.0 (NASA Space Apps 2026; evidencia cientifica)"
CHUNK = 4 << 20


def head_size(url: str) -> tuple[int, str]:
    response = requests.head(
        url, allow_redirects=True, timeout=(30, 90), headers={"User-Agent": UA}
    )
    response.raise_for_status()
    size = response.headers.get("Content-Length")
    if not size:
        raise RuntimeError("El servidor no declara Content-Length")
    return int(size), response.url


def worker(url: str, fd: int, start: int, end: int, estado: dict, idx: int) -> None:
    headers = {"User-Agent": UA, "Range": f"bytes={start}-{end}"}
    for attempt in range(1, 6):
        try:
            with requests.get(
                url, headers=headers, stream=True, timeout=(30, 120), allow_redirects=True
            ) as response:
                response.raise_for_status()
                if response.status_code != 206:
                    raise RuntimeError(f"HTTP {response.status_code}: sin soporte de rangos")
                pos = start
                for chunk in response.iter_content(CHUNK):
                    if not chunk:
                        continue
                    os.pwrite(fd, chunk, pos)
                    pos += len(chunk)
                    with estado["lock"]:
                        estado["bytes"] += len(chunk)
                if pos != end + 1:
                    raise RuntimeError(f"rango incompleto: {pos:,} de {end + 1:,}")
                estado["ok"][idx] = True
                return
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] hilo {idx} intento {attempt}: {exc}", flush=True)
            time.sleep(min(2 ** attempt, 15))
    estado["ok"][idx] = False


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("destino")
    parser.add_argument("--hilos", type=int, default=12)
    args = parser.parse_args()

    dest = Path(args.destino)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    checkpoint = part.with_suffix(part.suffix + ".json")

    size, final_url = head_size(args.url)
    if dest.exists() and dest.stat().st_size == size:
        print(f"[skip] {dest.name} ya completo ({size:,} B)")
        return 0

    fd = os.open(part, os.O_RDWR | os.O_CREAT)
    try:
        existing = os.fstat(fd).st_size
        if checkpoint.exists():
            saved = json.loads(checkpoint.read_text())
            if saved["url"] != args.url or saved["size"] != size:
                raise RuntimeError("El checkpoint no corresponde al recurso solicitado")
            existing = saved["prefix"]
        elif existing >= size:
            print("[err ] .part sin checkpoint; tamaño no demuestra integridad. Se conserva.")
            return 1
        checkpoint.write_text(json.dumps({"url": args.url, "size": size, "prefix": existing}))
        os.ftruncate(fd, size)
        pendiente = size - existing
        if pendiente <= 0:
            print("[ok  ] nada pendiente")
        else:
            hilos = max(1, min(args.hilos, pendiente // (8 << 20) or 1))
            tramo = pendiente // hilos
            rangos = []
            for i in range(hilos):
                inicio = existing + i * tramo
                fin = size - 1 if i == hilos - 1 else inicio + tramo - 1
                rangos.append((inicio, fin))

            estado = {"lock": threading.Lock(), "bytes": 0, "ok": [False] * hilos}
            inicio_t = time.time()
            print(
                f"[get ] {dest.name}: {existing:,} B ya, {pendiente:,} B en {hilos} hilos",
                flush=True,
            )
            threads = [
                threading.Thread(
                    target=worker,
                    args=(final_url, fd, a, b, estado, i),
                    daemon=True,
                )
                for i, (a, b) in enumerate(rangos)
            ]
            for thread in threads:
                thread.start()

            while any(thread.is_alive() for thread in threads):
                time.sleep(2)
                with estado["lock"]:
                    hechos = estado["bytes"]
                transcurrido = max(time.time() - inicio_t, 0.001)
                velocidad = hechos / transcurrido / 1e6
                pct = 100 * (existing + hechos) / size
                print(
                    f"[----] {pct:5.1f}%  {hechos:,}/{pendiente:,} B  {velocidad:.2f} MB/s",
                    flush=True,
                )
            for thread in threads:
                thread.join()

            if not all(estado["ok"]):
                print("[err ] hay rangos incompletos; se conserva el .part", flush=True)
                return 1

        os.fsync(fd)
    finally:
        os.close(fd)

    if part.stat().st_size != size:
        print(f"[err ] tamano final {part.stat().st_size:,} != {size:,}")
        return 1
    part.replace(dest)
    checkpoint.unlink()
    print(f"[ok  ] {dest.name} {size:,} B  sha256={sha256(dest)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
