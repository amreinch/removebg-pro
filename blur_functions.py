"""
Blur tool functions - tries MediaPipe first, falls back to OpenCV
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
        # Try MediaPipe first (more accurate), fall back to OpenCV
        try:
            import mediapipe as mp
            
            # Convert BGR to RGB for MediaPipe
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w = img.shape[:2]
            
            # Initialize Face Mesh
            with mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=10,
                refine_landmarks=True,
                min_detection_confidence=0.5
            ) as face_mesh:
                
                results = face_mesh.process(img_rgb)
                
                if results.multi_face_landmarks:
                    # Process each detected face
                    for face_landmarks in results.multi_face_landmarks:
                        # Create mask for this face
                        mask = np.zeros((h, w), dtype=np.uint8)
                        
                        # MediaPipe FACEMESH_FACE_OVAL indices define the face contour
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
                        
                        # Create convex hull from face oval points
                        points = np.array(points, dtype=np.int32)
                        hull = cv2.convexHull(points)
                        
                        # Fill the convex hull to create face mask
                        cv2.fillConvexPoly(mask, hull, 255)
                        
                        # Smooth mask edges for natural blending
                        mask = cv2.GaussianBlur(mask, (31, 31), 15)
                        
                        # Apply Gaussian blur to entire image
                        blurred_img = cv2.GaussianBlur(img, kernel_size, 0)
                        
                        # Blend original and blurred using the mask
                        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
                        img_float = img.astype(float)
                        blurred_float = blurred_img.astype(float)
                        img = (mask_3ch * blurred_float + (1 - mask_3ch) * img_float).astype(np.uint8)
        
        except (ImportError, AttributeError) as e:
            # MediaPipe failed, fall back to OpenCV Haar Cascade
            print(f"MediaPipe unavailable ({e}), using OpenCV Haar Cascade")
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
    Detect faces in an image - tries MediaPipe first, falls back to OpenCV.
    
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
    
    # Try MediaPipe first
    try:
        import mediapipe as mp
        
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
    
    except (ImportError, AttributeError) as e:
        # MediaPipe failed, fall back to OpenCV Haar Cascade
        print(f"MediaPipe unavailable ({e}), using OpenCV Haar Cascade")
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
