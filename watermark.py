"""
Watermark utilities for free tier images
"""
from PIL import Image, ImageDraw, ImageFont
import math


def add_watermark(image: Image.Image, watermark_text: str = "PREVIEW") -> Image.Image:
    """
    Add diagonal watermark overlay to image
    
    Args:
        image: PIL Image to watermark
        watermark_text: Text to use as watermark
    
    Returns:
        Watermarked PIL Image
    """
    # Make a copy to avoid modifying original
    watermarked = image.copy()
    
    # Convert to RGBA if not already
    if watermarked.mode != 'RGBA':
        watermarked = watermarked.convert('RGBA')
    
    # Create transparent overlay
    overlay = Image.new('RGBA', watermarked.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Calculate font size based on image dimensions
    width, height = watermarked.size
    font_size = max(int(min(width, height) / 15), 20)
    
    try:
        # Try to use a nice font
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()
    
    # Calculate text size
    bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Tile watermark across ENTIRE image (repetitive)
    diagonal = math.sqrt(width**2 + height**2)
    
    # Calculate spacing
    x_spacing = text_width * 2
    y_spacing = text_height * 3
    
    # Number of repetitions - based on diagonal to ensure full coverage after rotation
    x_count = int(diagonal / x_spacing) + 2
    y_count = int(diagonal / y_spacing) + 2
    
    # Start from negative to cover entire area after rotation
    x_start = -int(diagonal / 4)
    y_start = -int(diagonal / 4)
    
    # Draw watermark in a dense grid pattern
    for i in range(x_count):
        for j in range(y_count):
            x = x_start + (i * x_spacing)
            y = y_start + (j * y_spacing)
            
            # Semi-transparent white text with black outline
            draw.text(
                (x, y),
                watermark_text,
                font=font,
                fill=(255, 255, 255, 60),  # White with 23% opacity
                stroke_width=2,
                stroke_fill=(0, 0, 0, 40)  # Black outline with 15% opacity
            )
    
    # Rotate overlay
    overlay_rotated = overlay.rotate(-25, expand=False, resample=Image.Resampling.BICUBIC)
    
    # Composite watermark onto image
    watermarked = Image.alpha_composite(watermarked, overlay_rotated)
    
    return watermarked


def add_corner_watermark(image: Image.Image, text: str = "PREVIEW") -> Image.Image:
    """
    Add small watermark in bottom-right corner (alternative style)
    
    Args:
        image: PIL Image to watermark
        text: Watermark text
    
    Returns:
        Watermarked PIL Image
    """
    watermarked = image.copy()
    
    if watermarked.mode != 'RGBA':
        watermarked = watermarked.convert('RGBA')
    
    overlay = Image.new('RGBA', watermarked.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Smaller font for corner
    width, height = watermarked.size
    font_size = max(int(min(width, height) / 30), 16)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Get text size
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Position in bottom-right corner with padding
    padding = 20
    x = width - text_width - padding
    y = height - text_height - padding
    
    # Draw with shadow effect
    shadow_offset = 2
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 100))  # Shadow
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 180))  # White text
    
    watermarked = Image.alpha_composite(watermarked, overlay)
    
    return watermarked
