"""QR code generation. QRs are rendered on demand and never stored."""

from __future__ import annotations

import io

import qrcode


def qr_png(data: str) -> bytes:
    """Render a QR code as PNG bytes."""
    image = qrcode.make(data, box_size=8, border=2)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
