#!/usr/bin/env python3
"""Download the NYX and Miranda datasets for the Falcons artifact.

Place this file in Falcons_PPoPP_Artifacts/test and run it with Python 3.
Only the Python standard library is required.
"""

from pathlib import Path, PurePosixPath
import shutil
import sys
import tarfile
import tempfile
import time
from urllib.request import Request, urlopen


DATASETS = {
    "NYX": {
        "url": "https://g-d0cd3f.fd635.8443.data.globus.org/raw-data/EXASKY/NYX/SDRBENCH-EXASKY-NYX-512x512x512.tar.gz",
        "archive_dir": "SDRBENCH-EXASKY-NYX-512x512x512",
        "files": (
            "baryon_density.f32",
            "dark_matter_density.f32",
            "temperature.f32",
            "velocity_x.f32",
            "velocity_y.f32",
            "velocity_z.f32",
        ),
        "file_size": 512 * 512 * 512 * 4,
    },
    "Miranda": {
        "url": "https://g-d0cd3f.fd635.8443.data.globus.org/raw-data/Miranda/SDRBENCH-Miranda-256x384x384.tar.gz",
        "archive_dir": "SDRBENCH-Miranda-256x384x384",
        "files": (
            "density.d64",
            "diffusivity.d64",
            "pressure.d64",
            "velocityx.d64",
            "velocityy.d64",
            "velocityz.d64",
            "viscocity.d64",
        ),
        "file_size": 256 * 384 * 384 * 8,
    },
}

CHUNK_SIZE = 1024 * 1024
OUTPUT_DIR = Path(__file__).resolve().parent / "Datasets"


def validate_dataset(directory, config):
    """Check that all fields expected by the benchmark are present and complete."""
    for filename in config["files"]:
        path = directory / filename
        if not path.is_file():
            raise ValueError(f"Missing dataset file: {path}")
        actual_size = path.stat().st_size
        if actual_size != config["file_size"]:
            raise ValueError(
                f"Incorrect file size: {path} "
                f"({actual_size} bytes; expected {config['file_size']})"
            )


def download(url, destination):
    request = Request(url, headers={"User-Agent": "Falcons-PPoPP-Artifact/1.0"})
    with urlopen(request, timeout=60) as response, destination.open("wb") as output:
        total_header = response.headers.get("Content-Length")
        total = int(total_header) if total_header else None
        downloaded = 0
        last_update = 0.0
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            output.write(chunk)
            downloaded += len(chunk)
            now = time.monotonic()
            if now - last_update >= 2:
                if total:
                    message = f"{downloaded / total:.1%} ({downloaded / 1e9:.2f}/{total / 1e9:.2f} GB)"
                else:
                    message = f"{downloaded / 1e9:.2f} GB downloaded"
                print(f"\r  {message}", end="", flush=True)
                last_update = now
        print()
        if total is not None and downloaded != total:
            raise OSError(f"Incomplete download: {downloaded} of {total} bytes")


def extract(archive_path, destination, expected_root):
    """Extract the single archive directory directly under destination."""
    with tarfile.open(archive_path, mode="r|gz") as archive:
        for member in archive:
            name = PurePosixPath(member.name)
            if (
                name.is_absolute()
                or ".." in name.parts
                or "\\" in member.name
                or not name.parts
                or name.parts[0] != expected_root
            ):
                raise ValueError(f"Unexpected archive path: {member.name}")

            parts = name.parts[1:]
            if not parts:
                if not member.isdir():
                    raise ValueError(f"Unexpected archive entry: {member.name}")
                continue

            target = destination.joinpath(*parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            elif member.isfile():
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise ValueError(f"Cannot read archive entry: {member.name}")
                print(f"  Extracting {Path(*parts)}", flush=True)
                with source, target.open("wb") as output:
                    shutil.copyfileobj(source, output, length=CHUNK_SIZE)
            else:
                raise ValueError(f"Unsupported archive entry: {member.name}")


def prepare_dataset(name, config, output_dir):
    target = output_dir / name
    if target.exists() or target.is_symlink():
        if not target.is_dir():
            raise ValueError(f"Destination already exists and is not a directory: {target}")
        validate_dataset(target, config)
        print(f"{name}: dataset already exists, skipping: {target}")
        return

    # Work on the same filesystem and publish the directory only after validation.
    with tempfile.TemporaryDirectory(prefix=f".{name}-", dir=output_dir) as temp:
        temp_dir = Path(temp)
        archive_path = temp_dir / "dataset.tar.gz"
        extracted = temp_dir / "data"
        extracted.mkdir()

        print(f"{name}: downloading {config['url']}", flush=True)
        download(config["url"], archive_path)
        print(f"{name}: extracting", flush=True)
        extract(archive_path, extracted, config["archive_dir"])
        validate_dataset(extracted, config)

        if target.exists() or target.is_symlink():
            raise FileExistsError(f"Destination appeared during download: {target}")
        extracted.rename(target)
        print(f"{name}: ready: {target}", flush=True)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    failures = []
    for name, config in DATASETS.items():
        try:
            prepare_dataset(name, config, OUTPUT_DIR)
        except (OSError, ValueError, tarfile.TarError) as error:
            failures.append(name)
            print(f"{name}: {error}", file=sys.stderr, flush=True)
    if failures:
        print("Failed datasets: " + ", ".join(failures), file=sys.stderr)
        return 1
    print("Both datasets are ready.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nDownload interrupted.", file=sys.stderr)
        sys.exit(130)
