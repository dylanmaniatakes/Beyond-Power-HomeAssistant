from __future__ import annotations

from io import BytesIO

STARTUP_IMAGE_TARGET_SIZE_PX = 720
STARTUP_IMAGE_INITIAL_JPEG_QUALITY = 92
STARTUP_IMAGE_TARGET_MAX_BYTES = 56_000
STARTUP_IMAGE_MIN_JPEG_QUALITY = 18
STARTUP_IMAGE_JPEG_QUALITY_STEP = 4


def prepare_startup_image_bytes(
    source_bytes: bytes,
    *,
    target_size_px: int = STARTUP_IMAGE_TARGET_SIZE_PX,
) -> bytes:
    try:
        from PIL import Image, ImageOps
    except ImportError as err:
        raise ValueError("Pillow is required to prepare startup images. Disable preparation to upload a JPEG as-is.") from err

    with Image.open(BytesIO(source_bytes)) as image:
        image = ImageOps.exif_transpose(image)
        resampling = getattr(Image, "Resampling", Image).LANCZOS
        cropped = ImageOps.fit(
            image,
            (target_size_px, target_size_px),
            method=resampling,
            centering=(0.5, 0.5),
        )
        flattened = Image.new("RGB", cropped.size, (0, 0, 0))
        if cropped.mode == "RGBA":
            flattened.paste(cropped, mask=cropped.getchannel("A"))
        else:
            flattened.paste(cropped.convert("RGB"))

    quality = STARTUP_IMAGE_INITIAL_JPEG_QUALITY
    while True:
        buffer = BytesIO()
        flattened.save(buffer, format="JPEG", quality=quality)
        jpeg_bytes = add_ipad_like_startup_photo_metadata(
            buffer.getvalue(),
            width=target_size_px,
            height=target_size_px,
        )
        if len(jpeg_bytes) <= STARTUP_IMAGE_TARGET_MAX_BYTES or quality <= STARTUP_IMAGE_MIN_JPEG_QUALITY:
            validate_startup_jpeg_bytes(jpeg_bytes)
            return jpeg_bytes
        quality -= STARTUP_IMAGE_JPEG_QUALITY_STEP


def validate_startup_jpeg_bytes(jpeg_bytes: bytes) -> None:
    if not _is_jpeg(jpeg_bytes):
        raise ValueError("Startup image must be a JPEG when image preparation is disabled.")
    if len(jpeg_bytes) == 0:
        raise ValueError("Startup image is empty.")


def add_ipad_like_startup_photo_metadata(
    jpeg_bytes: bytes,
    *,
    width: int,
    height: int,
) -> bytes:
    if not _is_jpeg(jpeg_bytes):
        return jpeg_bytes
    insert_offset = _find_post_jfif_offset(jpeg_bytes)
    app1 = _build_ipad_like_exif_segment(width, height)
    return jpeg_bytes[:insert_offset] + app1 + IPAD_LIKE_APP13_SEGMENT + jpeg_bytes[insert_offset:]


def _is_jpeg(data: bytes) -> bool:
    return len(data) >= 4 and data[0] == 0xFF and data[1] == 0xD8


def _find_post_jfif_offset(jpeg_bytes: bytes) -> int:
    if len(jpeg_bytes) < 6:
        return 2
    marker = jpeg_bytes[3]
    if jpeg_bytes[2] != 0xFF or marker != 0xE0:
        return 2
    length = (jpeg_bytes[4] << 8) | jpeg_bytes[5]
    next_offset = 2 + 2 + length
    return max(2, min(next_offset, len(jpeg_bytes)))


def _build_ipad_like_exif_segment(width: int, height: int) -> bytes:
    payload = (
        b"Exif\x00\x00"
        + bytes((0x4D, 0x4D, 0x00, 0x2A))
        + bytes((0x00, 0x00, 0x00, 0x08))
        + bytes((0x00, 0x01))
        + bytes((0x87, 0x69))
        + bytes((0x00, 0x04))
        + bytes((0x00, 0x00, 0x00, 0x01))
        + bytes((0x00, 0x00, 0x00, 0x1A))
        + bytes((0x00, 0x00, 0x00, 0x00))
        + bytes((0x00, 0x03))
        + bytes((0xA0, 0x01, 0x00, 0x03))
        + bytes((0x00, 0x00, 0x00, 0x01))
        + bytes((0x00, 0x01, 0x00, 0x00))
        + bytes((0xA0, 0x02, 0x00, 0x04))
        + bytes((0x00, 0x00, 0x00, 0x01))
        + _int_to_be32(width)
        + bytes((0xA0, 0x03, 0x00, 0x04))
        + bytes((0x00, 0x00, 0x00, 0x01))
        + _int_to_be32(height)
        + bytes((0x00, 0x00, 0x00, 0x00))
    )
    length = len(payload) + 2
    return bytes((0xFF, 0xE1, (length >> 8) & 0xFF, length & 0xFF)) + payload


def _int_to_be32(value: int) -> bytes:
    return bytes(
        (
            (value >> 24) & 0xFF,
            (value >> 16) & 0xFF,
            (value >> 8) & 0xFF,
            value & 0xFF,
        ),
    )


IPAD_LIKE_APP13_SEGMENT = bytes(
    (
        0xFF,
        0xED,
        0x00,
        0x38,
        0x50,
        0x68,
        0x6F,
        0x74,
        0x6F,
        0x73,
        0x68,
        0x6F,
        0x70,
        0x20,
        0x33,
        0x2E,
        0x30,
        0x00,
        0x38,
        0x42,
        0x49,
        0x4D,
        0x04,
        0x04,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x38,
        0x42,
        0x49,
        0x4D,
        0x04,
        0x25,
        0x00,
        0x00,
        0x00,
        0x00,
        0x00,
        0x10,
        0xD4,
        0x1D,
        0x8C,
        0xD9,
        0x8F,
        0x00,
        0xB2,
        0x04,
        0xE9,
        0x80,
        0x09,
        0x98,
        0xEC,
        0xF8,
        0x42,
        0x7E,
    ),
)
