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


# ============================================================================
# IMAGE TO PDF CONVERTER
# ============================================================================

def images_to_pdf(image_bytes_list: List[bytes]) -> bytes:
    """
    Convert one or more images to a single PDF.
    
    Args:
        image_bytes_list: List of image file bytes (JPG, PNG, WebP, etc.)
    
    Returns:
        PDF bytes containing all images
    """
    import img2pdf
    
    # img2pdf can handle multiple images at once
    pdf_bytes = img2pdf.convert(image_bytes_list)
    return pdf_bytes


# ============================================================================
# PDF TO IMAGES CONVERTER
# ============================================================================

def pdf_to_images(
    pdf_bytes: bytes,
    output_format: str = "png",
    dpi: int = 200,
    page_numbers: List[int] = None
) -> List[bytes]:
    """
    Convert PDF pages to images.
    
    Args:
        pdf_bytes: PDF file bytes
        output_format: 'png' or 'jpg'
        dpi: Resolution (default 200, higher = better quality but larger files)
        page_numbers: List of page numbers to convert (1-indexed), None = all pages
    
    Returns:
        List of image bytes (one per page)
    """
    from pdf2image import convert_from_bytes
    
    # Convert PDF to PIL images
    images = convert_from_bytes(
        pdf_bytes,
        dpi=dpi,
        fmt=output_format
    )
    
    # Filter pages if specified
    if page_numbers:
        images = [images[i-1] for i in page_numbers if 0 < i <= len(images)]
    
    # Convert PIL images to bytes
    result = []
    for img in images:
        output = io.BytesIO()
        
        # Save as requested format
        if output_format.lower() == 'jpg':
            # Convert RGBA to RGB for JPEG
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            img.save(output, format='JPEG', quality=95, optimize=True)
        else:
            img.save(output, format='PNG', optimize=True)
        
        output.seek(0)
        result.append(output.read())
    
    return result


# ============================================================================
# BLUR SENSITIVE DATA
# ============================================================================

def blur_image(
    image_bytes: bytes,
    mode: str = "auto",
    blur_regions: List[Tuple[int, int, int, int]] = None,
    blur_strength: str = "medium"
) -> bytes:
    """
    Blur sensitive information in images.
    
    Args:
        image_bytes: Original image bytes
        mode: 'auto' for face detection, 'manual' for custom regions
        blur_regions: List of (x, y, width, height) tuples for manual mode
        blur_strength: 'low', 'medium', or 'high'
    
    Returns:
        Blurred image bytes
    """
    import cv2
    import numpy as np
    
    # Load image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Invalid image data")
    
    # Map blur strength to kernel size
    blur_map = {
        'low': (23, 23),
        'medium': (51, 51),
        'high': (99, 99)
    }
    kernel_size = blur_map.get(blur_strength, (51, 51))
    
    if mode == "auto":
        # Use MediaPipe Face Mesh for precise face detection and masking
        import mediapipe as mp
        
        # Convert BGR to RGB for MediaPipe
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Initialize Face Mesh
        with mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=10,
            refine_landmarks=True,
            min_detection_confidence=0.5
        ) as face_mesh:
            
            results = face_mesh.process(img_rgb)
            
            if results.multi_face_landmarks:
                h, w = img.shape[:2]
                
                # Process each detected face
                for face_landmarks in results.multi_face_landmarks:
                    # Create mask for this face
                    mask = np.zeros((h, w), dtype=np.uint8)
                    
                    # MediaPipe FACEMESH_FACE_OVAL indices define the face contour
                    # This includes forehead, cheeks, jawline, and chin
                    FACE_OVAL = [
                        10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
                        397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
                        172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109
                    ]
                    
                    # Convert normalized landmarks to pixel coordinates
                    points = []
                    for idx in FACE_OVAL:
                        landmark = face_landmarks.landmark[idx]
                        x_px = int(landmark.x * w)
                        y_px = int(landmark.y * h)
                        points.append([x_px, y_px])
                    
                    # Create convex hull from face oval points for smooth mask
                    points = np.array(points, dtype=np.int32)
                    hull = cv2.convexHull(points)
                    
                    # Fill the convex hull to create face mask
                    cv2.fillConvexPoly(mask, hull, 255)
                    
                    # Smooth mask edges for natural blending
                    mask = cv2.GaussianBlur(mask, (31, 31), 15)
                    
                    # Apply Gaussian blur to entire image
                    blurred_img = cv2.GaussianBlur(img, kernel_size, 0)
                    
                    # Normalize mask to 0-1 range
                    mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
                    
                    # Blend blurred and original using the mask
                    img_float = img.astype(float)
                    blurred_float = blurred_img.astype(float)
                    img = (mask_3ch * blurred_float + (1 - mask_3ch) * img_float).astype(np.uint8)
    
    elif mode == "manual" and blur_regions:
        # Blur custom regions
        for (x, y, w, h) in blur_regions:
            # Ensure coordinates are within image bounds
            x, y = max(0, x), max(0, y)
            w = min(w, img.shape[1] - x)
            h = min(h, img.shape[0] - y)
            
            if w > 0 and h > 0:
                # Extract region
                region = img[y:y+h, x:x+w]
                # Apply Gaussian blur
                blurred_region = cv2.GaussianBlur(region, kernel_size, 0)
                # Replace with blurred version
                img[y:y+h, x:x+w] = blurred_region
    
    # Convert back to bytes
    _, buffer = cv2.imencode('.png', img)
    return buffer.tobytes()


def detect_faces(image_bytes: bytes) -> List[Tuple[int, int, int, int]]:
    """
    Detect faces in an image using MediaPipe and return their bounding boxes.
    
    Args:
        image_bytes: Image file bytes
    
    Returns:
        List of (x, y, width, height) tuples for each detected face
    """
    import cv2
    import numpy as np
    import mediapipe as mp
    
    # Load image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Invalid image data")
    
    # Convert BGR to RGB for MediaPipe
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w = img.shape[:2]
    
    face_boxes = []
    
    with mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=10,
        min_detection_confidence=0.5
    ) as face_mesh:
        
        results = face_mesh.process(img_rgb)
        
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                # Calculate bounding box from all landmarks
                x_coords = [int(lm.x * w) for lm in face_landmarks.landmark]
                y_coords = [int(lm.y * h) for lm in face_landmarks.landmark]
                
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                
                width = x_max - x_min
                height = y_max - y_min
                
                face_boxes.append((x_min, y_min, width, height))
    
    return face_boxes
