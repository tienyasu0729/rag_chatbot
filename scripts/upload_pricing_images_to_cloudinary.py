"""
Upload local pricing images to Cloudinary and print imageAssets payload.

Env vars:
- CLOUDINARY_CLOUD_NAME
- CLOUDINARY_API_KEY
- CLOUDINARY_API_SECRET
Optional:
- CLOUDINARY_UPLOAD_FOLDER
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


GROUP_ALIASES = {
    "front": "front",
    "front_chech_trai": "front",
    "front_chech_phai": "front",
    "rear": "rear",
    "back": "rear",
    "duoi_xe": "other",
    "left_side": "left_side",
    "left_side_gan_dung": "left_side",
    "left": "left_side",
    "right_side": "right_side",
    "right_side_gan_dung": "right_side",
    "right": "right_side",
    "interior_front": "interior_front",
    "interior_rear": "interior_rear",
    "dashboard": "dashboard",
    "taplo": "dashboard",
    "odometer": "odometer",
    "odo": "odometer",
    "engine_bay": "engine_bay",
    "khoang_may": "engine_bay",
    "tire": "tire",
    "lop": "tire",
    "damage_detail": "damage_detail",
    "scratch": "damage_detail",
    "dent": "damage_detail",
    "document": "document",
    "giay_to": "document",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upload pricing test images to Cloudinary.")
    parser.add_argument(
        "--folder",
        default=r"C:\Users\VAN-NAM\Downloads\dinhgiaxe",
        help="Folder containing local images.",
    )
    parser.add_argument(
        "--prefix",
        default="vehicle-pricing",
        help="Cloudinary public_id prefix/folder.",
    )
    parser.add_argument(
        "--request-id",
        default="req_20260505_001",
        help="Printed only for easier payload assembly.",
    )
    return parser.parse_args()


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing env var: {name}")
    return value


def infer_declared_group(filename: str) -> str:
    stem = Path(filename).stem.lower()
    normalized = (
        stem.replace("-", "_")
        .replace(" ", "_")
        .replace("__", "_")
    )
    for key, group in GROUP_ALIASES.items():
        if key in normalized:
            return group
    return "other"


def cloudinary_signature(params: dict[str, str], api_secret: str) -> str:
    filtered = {
        key: value
        for key, value in params.items()
        if value is not None and value != "" and key not in {"file", "api_key", "resource_type", "cloud_name"}
    }
    joined = "&".join(f"{key}={filtered[key]}" for key in sorted(filtered))
    return hashlib.sha1(f"{joined}{api_secret}".encode("utf-8")).hexdigest()


def encode_multipart_formdata(fields: dict[str, str], file_field: str, filename: str, file_bytes: bytes) -> tuple[bytes, str]:
    boundary = f"----PricingUpload{uuid.uuid4().hex}"
    lines: list[bytes] = []
    for key, value in fields.items():
        lines.extend(
            [
                f"--{boundary}".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"'.encode("utf-8"),
                b"",
                str(value).encode("utf-8"),
            ]
        )

    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    lines.extend(
        [
            f"--{boundary}".encode("utf-8"),
            f'Content-Disposition: form-data; name="{file_field}"; filename="{Path(filename).name}"'.encode("utf-8"),
            f"Content-Type: {mime_type}".encode("utf-8"),
            b"",
            file_bytes,
        ]
    )
    lines.append(f"--{boundary}--".encode("utf-8"))
    body = b"\r\n".join(lines) + b"\r\n"
    return body, boundary


def upload_one(path: Path, *, cloud_name: str, api_key: str, api_secret: str, prefix: str) -> dict:
    timestamp = str(int(time.time()))
    public_id = f"{prefix}/{path.stem.lower().replace(' ', '_')}"
    params = {
        "timestamp": timestamp,
        "public_id": public_id,
        "folder": prefix,
        "overwrite": "true",
    }
    signature = cloudinary_signature(params, api_secret)
    fields = {
        **params,
        "signature": signature,
        "api_key": api_key,
    }
    body, boundary = encode_multipart_formdata(fields, "file", path.name, path.read_bytes())
    url = f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload"
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Upload failed for {path.name}: HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Upload failed for {path.name}: {exc.reason}") from exc

    return {
        "localFile": str(path),
        "url": payload["secure_url"],
        "publicId": payload["public_id"],
        "source": "cloudinary",
        "declaredGroup": infer_declared_group(path.name),
        "bytes": payload.get("bytes"),
        "format": payload.get("format"),
    }


def collect_files(folder: Path) -> list[Path]:
    if not folder.exists():
        raise RuntimeError(f"Folder not found: {folder}")
    files = [item for item in folder.iterdir() if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS]
    if not files:
        raise RuntimeError(f"No image files found in: {folder}")
    return sorted(files)


def main() -> int:
    args = parse_args()
    folder = Path(args.folder)
    try:
        cloud_name = required_env("CLOUDINARY_CLOUD_NAME")
        api_key = required_env("CLOUDINARY_API_KEY")
        api_secret = required_env("CLOUDINARY_API_SECRET")
        files = collect_files(folder)
        uploaded = []
        for path in files:
            print(f"Uploading: {path.name}")
            uploaded.append(
                upload_one(
                    path,
                    cloud_name=cloud_name,
                    api_key=api_key,
                    api_secret=api_secret,
                    prefix=args.prefix,
                )
            )

        image_assets = [
            {
                "url": item["url"],
                "publicId": item["publicId"],
                "source": item["source"],
                "declaredGroup": item["declaredGroup"],
            }
            for item in uploaded
        ]

        print("\nUploaded image summary:")
        for item in uploaded:
            print(f"- {Path(item['localFile']).name} -> {item['declaredGroup']} -> {item['url']}")

        print("\nimageAssets JSON:")
        print(json.dumps(image_assets, ensure_ascii=False, indent=2))

        print("\nSuggested payload fragment:")
        print(
            json.dumps(
                {
                    "requestId": args.request_id,
                    "imageAssets": image_assets,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
