"""
QuickTools - Tool Implementations
All tool processing logic in one place
"""
from PIL import Image
import qrcode
from pypdf import PdfWriter, PdfReader
import io
from typing import List, Tuple
import os


# ============================================================================
# QR CODE GENERATOR
# ============================================================================

def generate_qr_code(
    data: str,
    size: int = 300,
    border: int = 4,
    error_correction: str = "M"
) -> bytes:
    """
    Generate a QR code image.
    
    Args:
        data: Text/URL to encode
        size: Size in pixels (will be square)
        border: Border size in boxes
        error_correction: L, M, Q, or H (Low, Medium, Quartile, High)
    
    Returns:
        PNG image bytes
    """
    # Map error correction
    ec_map = {
        "L": qrcode.constants.ERROR_CORRECT_L,
        "M": qrcode.constants.ERROR_CORRECT_M,
        "Q": qrcode.constants.ERROR_CORRECT_Q,
        "H": qrcode.constants.ERROR_CORRECT_H,
    }
    
    qr = qrcode.QRCode(
        version=None,  # Auto-size
        error_correction=ec_map.get(error_correction, qrcode.constants.ERROR_CORRECT_M),
        box_size=10,
        border=border,
    )
    
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Resize to requested size
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    
    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    
    return buf.read()


# ============================================================================
# IMAGE RESIZE
# ============================================================================

def resize_image(
    image_bytes: bytes,
    width: int = None,
    height: int = None,
    maintain_aspect: bool = True,
    format: str = "PNG"
) -> bytes:
    """
    Resize an image.
    
    Args:
        image_bytes: Original image bytes
        width: Target width (None to auto-calculate)
        height: Target height (None to auto-calculate)
        maintain_aspect: Keep aspect ratio
        format: Output format (PNG, JPEG, WEBP)
    
    Returns:
        Resized image bytes
    """
    img = Image.open(io.BytesIO(image_bytes))
    
    # Convert RGBA to RGB for JPEG
    if format.upper() == "JPEG" and img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
        img = background
    
    original_width, original_height = img.size
    
    # Calculate dimensions
    if maintain_aspect:
        if width and not height:
            # Width specified, calculate height
            aspect_ratio = original_height / original_width
            height = int(width * aspect_ratio)
        elif height and not width:
            # Height specified, calculate width
            aspect_ratio = original_width / original_height
            width = int(height * aspect_ratio)
        elif width and height:
            # Both specified, use thumbnail to maintain aspect
            img.thumbnail((width, height), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format=format.upper())
            buf.seek(0)
            return buf.read()
    
    # Default: use original dimensions if neither specified
    if not width:
        width = original_width
    if not height:
        height = original_height
    
    # Resize
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    
    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format=format.upper())
    buf.seek(0)
    
    return buf.read()


def bulk_resize_images(
    images: List[Tuple[str, bytes]],
    width: int = None,
    height: int = None,
    maintain_aspect: bool = True,
    format: str = "PNG"
) -> List[Tuple[str, bytes]]:
    """
    Resize multiple images at once.
    
    Args:
        images: List of (filename, image_bytes) tuples
        width: Target width
        height: Target height
        maintain_aspect: Keep aspect ratio
        format: Output format
    
    Returns:
        List of (filename, resized_bytes) tuples
    """
    results = []
    
    for filename, image_bytes in images:
        resized = resize_image(image_bytes, width, height, maintain_aspect, format)
        
        # Update filename extension
        base_name = os.path.splitext(filename)[0]
        ext = format.lower() if format.lower() != "jpeg" else "jpg"
        new_filename = f"{base_name}_resized.{ext}"
        
        results.append((new_filename, resized))
    
    return results


# ============================================================================
# PDF TOOLS
# ============================================================================

def merge_pdfs(pdf_files: List[bytes]) -> bytes:
    """
    Merge multiple PDF files into one.
    
    Args:
        pdf_files: List of PDF file bytes
    
    Returns:
        Merged PDF bytes
    """
    merger = PdfWriter()
    
    for pdf_bytes in pdf_files:
        pdf_file = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)
        merger.append(reader)
    
    output = io.BytesIO()
    merger.write(output)
    output.seek(0)
    
    return output.read()


def split_pdf(pdf_bytes: bytes, pages: str = "all") -> List[bytes]:
    """
    Split a PDF into separate pages or ranges.
    
    Args:
        pdf_bytes: Original PDF bytes
        pages: Page specification:
            - "all" = one PDF per page
            - "1-3,5,7-9" = specific pages/ranges
    
    Returns:
        List of PDF bytes (one per page or range)
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    results = []
    
    if pages == "all":
        # Split into individual pages
        for i in range(total_pages):
            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            
            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            results.append(output.read())
    else:
        # Parse page specification
        ranges = pages.split(',')
        for range_str in ranges:
            range_str = range_str.strip()
            
            writer = PdfWriter()
            
            if '-' in range_str:
                # Range (e.g., "1-3")
                start, end = range_str.split('-')
                start = int(start) - 1  # Convert to 0-indexed
                end = int(end)
                
                for i in range(start, min(end, total_pages)):
                    writer.add_page(reader.pages[i])
            else:
                # Single page (e.g., "5")
                page_num = int(range_str) - 1  # Convert to 0-indexed
                if 0 <= page_num < total_pages:
                    writer.add_page(reader.pages[page_num])
            
            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            results.append(output.read())
    
    return results


def compress_pdf(pdf_bytes: bytes) -> bytes:
    """
    Compress a PDF (basic compression).
    
    Args:
        pdf_bytes: Original PDF bytes
    
    Returns:
        Compressed PDF bytes
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    
    # Copy all pages
    for page in reader.pages:
        writer.add_page(page)
    
    # Compress
    for page in writer.pages:
        page.compress_content_streams()
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    
    return output.read()
