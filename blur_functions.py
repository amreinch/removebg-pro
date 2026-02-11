"""
Blur tool functions using OpenCV only (no MediaPipe dependency)
"""
import cv2
import numpy as np
from typing import List, Tuple


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
        # Use OpenCV Haar Cascade for face detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        # Apply blur to each detected face
        for (x, y, w, h) in faces:
            # Extract the face region
            face_region = img[y:y+h, x:x+w]
            
            # Apply Gaussian blur
            blurred_face = cv2.GaussianBlur(face_region, kernel_size, 0)
            
            # Replace with blurred version
            img[y:y+h, x:x+w] = blurred_face
    
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
    Detect faces in an image using OpenCV Haar Cascade.
    
    Args:
        image_bytes: Image file bytes
    
    Returns:
        List of (x, y, width, height) tuples for each detected face
    """
    # Load image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Invalid image data")
    
    # Load face detector
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    
    # Convert numpy array to list of tuples
    return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
