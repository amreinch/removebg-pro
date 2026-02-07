"""
RemoveBG Pro - AI Background Remover Service
Main application file
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove
from PIL import Image
import io
import uuid
from pathlib import Path
import shutil
import os
from datetime import datetime

app = FastAPI(
    title="RemoveBG Pro API",
    description="AI-powered background removal service",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
STATIC_DIR = Path("static")

for directory in [UPLOAD_DIR, OUTPUT_DIR, STATIC_DIR]:
    directory.mkdir(exist_ok=True)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main web interface"""
    html_path = Path("static/index.html")
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return HTMLResponse(content="""
        <html>
            <body>
                <h1>RemoveBG Pro API</h1>
                <p>API is running! Visit /docs for API documentation.</p>
                <p>Web interface coming soon...</p>
            </body>
        </html>
    """)


@app.post("/api/remove-background")
async def remove_background(
    file: UploadFile = File(...),
    format: str = "png"
):
    """
    Remove background from uploaded image
    
    Args:
        file: Image file (JPG, PNG, WebP)
        format: Output format (png, jpg, webp)
    
    Returns:
        Processed image with transparent background
    """
    # Validate file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Validate file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(status_code=400, detail="File too large. Max 10MB")
    
    try:
        # Generate unique ID
        file_id = str(uuid.uuid4())
        
        # Save original file
        input_path = UPLOAD_DIR / f"{file_id}_original{Path(file.filename).suffix}"
        with open(input_path, "wb") as f:
            f.write(contents)
        
        # Process image - remove background
        input_image = Image.open(io.BytesIO(contents))
        
        # Remove background using rembg
        output_image = remove(input_image)
        
        # Save processed image
        output_format = format.lower()
        if output_format not in ["png", "jpg", "jpeg", "webp"]:
            output_format = "png"
            
        output_filename = f"{file_id}.{output_format}"
        output_path = OUTPUT_DIR / output_filename
        
        if output_format in ["jpg", "jpeg"]:
            # JPG doesn't support transparency, add white background
            background = Image.new("RGB", output_image.size, (255, 255, 255))
            background.paste(output_image, mask=output_image.split()[3] if len(output_image.split()) == 4 else None)
            background.save(output_path, format="JPEG", quality=95)
        else:
            output_image.save(output_path, format=output_format.upper())
        
        # Get file sizes
        original_size = os.path.getsize(input_path)
        output_size = os.path.getsize(output_path)
        
        # Return result
        return {
            "success": True,
            "file_id": file_id,
            "output_url": f"/outputs/{output_filename}",
            "download_url": f"/api/download/{file_id}",
            "original_filename": file.filename,
            "output_filename": output_filename,
            "original_size": original_size,
            "output_size": output_size,
            "format": output_format,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/api/download/{file_id}")
async def download_file(file_id: str):
    """Download processed image"""
    # Find file with any extension
    for ext in ["png", "jpg", "jpeg", "webp"]:
        file_path = OUTPUT_DIR / f"{file_id}.{ext}"
        if file_path.exists():
            return FileResponse(
                file_path,
                media_type=f"image/{ext}",
                filename=f"removed-bg-{file_id}.{ext}"
            )
    
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "RemoveBG Pro API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/stats")
async def get_stats():
    """Get service statistics"""
    total_processed = len(list(OUTPUT_DIR.glob("*")))
    total_uploads = len(list(UPLOAD_DIR.glob("*")))
    
    return {
        "total_processed": total_processed,
        "total_uploads": total_uploads,
        "timestamp": datetime.utcnow().isoformat()
    }


# Cleanup old files (runs on startup)
@app.on_event("startup")
async def startup_cleanup():
    """Clean up files older than 24 hours"""
    import time
    
    current_time = time.time()
    max_age = 24 * 60 * 60  # 24 hours
    
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        for file_path in directory.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age:
                    file_path.unlink()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
