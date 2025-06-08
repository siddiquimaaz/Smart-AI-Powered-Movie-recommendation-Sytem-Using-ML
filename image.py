#!/usr/bin/env python3
"""
Themed Placeholder Generator
============================
A standalone script to generate premium dark-themed placeholder images
matching your movie app's aesthetic.

Requirements:
    pip install Pillow

Usage:
    python themed_placeholder.py
    
    # Or import as module:
    from themed_placeholder import create_placeholder, create_movie_placeholder
"""

from PIL import Image, ImageDraw, ImageFont
import base64
import io
import os
from typing import Tuple, Optional, Union


class ThemedPlaceholderGenerator:
    """Generate premium dark-themed placeholder images"""
    
    # Theme colors matching your CSS
    COLORS = {
        'bg_primary': '#0f0f23',
        'bg_secondary': '#1a0a2e', 
        'bg_tertiary': '#16213e',
        'accent_primary': '#7c3aed',
        'accent_secondary': '#a855f7',
        'accent_light': '#c084fc',
        'text_primary': '#ffffff',
        'text_secondary': '#e2e8f0',
        'text_muted': '#a8b3cf',
        'text_placeholder': '#6b7280',
        'cyan': '#06b6d4',
        'emerald': '#10b981',
        'red': '#ef4444',
        'yellow': '#fbbf24'
    }
    
    def __init__(self):
        self.default_font = None
        self.load_fonts()
    
    def load_fonts(self):
        """Load fonts with fallback"""
        font_paths = [
            # Windows
            'C:/Windows/Fonts/arial.ttf',
            'C:/Windows/Fonts/calibri.ttf',
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    self.default_font = font_path
                    break
            except:
                continue
    
    def hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def create_gradient_background(self, width: int, height: int, 
                                 start_color: str, end_color: str) -> Image.Image:
        """Create a vertical gradient background"""
        img = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(img)
        
        start_rgb = self.hex_to_rgb(start_color)
        end_rgb = self.hex_to_rgb(end_color)
        
        for y in range(height):
            ratio = y / height
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
            
            draw.line([(0, y), (width, y)], fill=(r, g, b))
        
        return img
    
    def get_font(self, size: int) -> ImageFont.ImageFont:
        """Get font with specified size"""
        try:
            if self.default_font:
                return ImageFont.truetype(self.default_font, size)
            else:
                return ImageFont.load_default()
        except:
            return ImageFont.load_default()
    
    def draw_text_centered(self, draw: ImageDraw.Draw, text: str, 
                          position: Tuple[int, int], font: ImageFont.ImageFont, 
                          color: str, img_width: int):
        """Draw text centered horizontally"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        x = (img_width - text_width) // 2
        y = position[1]
        
        draw.text((x, y), text, fill=color, font=font)
    
    def create_basic_placeholder(self, width: int = 300, height: int = 400, 
                               text: str = "No Image", 
                               bg_color: Optional[str] = None,
                               text_color: Optional[str] = None) -> Image.Image:
        """Create a basic themed placeholder"""
        
        bg_color = bg_color or self.COLORS['bg_primary']
        text_color = text_color or self.COLORS['text_secondary']
        
        # Create gradient background
        img = self.create_gradient_background(width, height, 
                                            self.COLORS['bg_primary'], 
                                            self.COLORS['bg_secondary'])
        draw = ImageDraw.Draw(img)
        
        # Add subtle border
        border_color = self.hex_to_rgb(self.COLORS['accent_primary'])
        draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=2)
        
        # Add text
        font = self.get_font(24)
        lines = text.split('\n')
        
        total_text_height = len(lines) * 30
        start_y = (height - total_text_height) // 2
        
        for i, line in enumerate(lines):
            y = start_y + (i * 30)
            self.draw_text_centered(draw, line, (0, y), font, text_color, width)
        
        return img
    
    def create_movie_placeholder(self, width: int = 300, height: int = 450,
                               title: str = "Movie Title",
                               subtitle: str = "Poster Not Available") -> Image.Image:
        """Create a movie poster placeholder with cinematic styling"""
        
        # Create gradient background
        img = self.create_gradient_background(width, height, 
                                            self.COLORS['bg_primary'], 
                                            self.COLORS['bg_tertiary'])
        draw = ImageDraw.Draw(img)
        
        # Add film strip decoration
        self._add_film_strip(draw, width, height)
        
        # Add decorative frame
        frame_color = self.hex_to_rgb(self.COLORS['accent_primary'])
        draw.rectangle([5, 5, width-6, height-6], outline=frame_color, width=3)
        
        # Add inner glow effect
        glow_color = self.hex_to_rgb(self.COLORS['accent_secondary'])
        for i in range(3):
            alpha = 50 - (i * 15)
            draw.rectangle([8+i, 8+i, width-9-i, height-9-i], 
                         outline=glow_color + (alpha,), width=1)
        
        # Add cinema icon
        self._add_cinema_icon(draw, width, height // 3)
        
        # Add main text
        title_font = self.get_font(20)
        subtitle_font = self.get_font(16)
        
        # Draw subtitle
        y_pos = height * 0.65
        self.draw_text_centered(draw, subtitle, (0, int(y_pos)), 
                              title_font, self.COLORS['text_secondary'], width)
        
        # Draw title (with text wrapping)
        wrapped_title = self._wrap_text(title, 18)
        y_pos = height * 0.75
        
        for line in wrapped_title:
            self.draw_text_centered(draw, line, (0, int(y_pos)), 
                                  subtitle_font, self.COLORS['text_muted'], width)
            y_pos += 25
        
        return img
    
    def _add_film_strip(self, draw: ImageDraw.Draw, width: int, height: int):
        """Add film strip holes decoration"""
        hole_size = 8
        hole_spacing = 25
        strip_color = self.hex_to_rgb(self.COLORS['accent_primary'])
        
        # Left strip
        for y in range(15, height - 15, hole_spacing):
            draw.ellipse([8, y, 8 + hole_size, y + hole_size], fill=strip_color)
        
        # Right strip  
        for y in range(15, height - 15, hole_spacing):
            draw.ellipse([width - 16, y, width - 8, y + hole_size], fill=strip_color)
    
    def _add_cinema_icon(self, draw: ImageDraw.Draw, width: int, y: int):
        """Add a simple cinema/camera icon"""
        icon_size = 40
        x = (width - icon_size) // 2
        
        icon_color = self.hex_to_rgb(self.COLORS['accent_light'])
        
        # Camera body
        draw.rectangle([x, y, x + icon_size, y + icon_size * 0.7], 
                      fill=icon_color, outline=self.hex_to_rgb(self.COLORS['text_muted']))
        
        # Lens
        lens_size = 20
        lens_x = x + (icon_size - lens_size) // 2
        lens_y = y + 5
        draw.ellipse([lens_x, lens_y, lens_x + lens_size, lens_y + lens_size], 
                    outline=self.hex_to_rgb(self.COLORS['text_secondary']), width=2)
        
        # Lens center
        center_size = 8
        center_x = lens_x + (lens_size - center_size) // 2
        center_y = lens_y + (lens_size - center_size) // 2
        draw.ellipse([center_x, center_y, center_x + center_size, center_y + center_size], 
                    fill=self.hex_to_rgb(self.COLORS['bg_primary']))
    
    def _wrap_text(self, text: str, max_length: int) -> list:
        """Wrap text to fit within specified length"""
        if len(text) <= max_length:
            return [text]
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_length:
                current_line += (" " + word) if current_line else word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def create_error_placeholder(self, width: int = 300, height: int = 400,
                               error_code: str = "404",
                               message: str = "Not Found") -> Image.Image:
        """Create an error placeholder (404, 500, etc.)"""
        
        img = self.create_gradient_background(width, height,
                                            self.COLORS['bg_primary'],
                                            self.COLORS['bg_secondary'])
        draw = ImageDraw.Draw(img)
        
        # Add error styling
        error_color = self.hex_to_rgb(self.COLORS['red'])
        draw.rectangle([0, 0, width-1, height-1], outline=error_color, width=3)
        
        # Large error code
        error_font = self.get_font(48)
        self.draw_text_centered(draw, error_code, (0, height//2 - 60), 
                              error_font, self.COLORS['red'], width)
        
        # Error message
        msg_font = self.get_font(18)
        self.draw_text_centered(draw, message, (0, height//2 + 10), 
                              msg_font, self.COLORS['text_muted'], width)
        
        return img
    
    def save_image(self, img: Image.Image, filename: str, format: str = 'PNG'):
        """Save image to file"""
        img.save(filename, format=format)
        print(f"✅ Saved: {filename}")
    
    def to_base64(self, img: Image.Image, format: str = 'PNG') -> str:
        """Convert image to base64 string"""
        buffer = io.BytesIO()
        img.save(buffer, format=format)
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/{format.lower()};base64,{img_str}"


# Convenience functions for easy usage
def create_placeholder(width: int = 300, height: int = 400, 
                      text: str = "No Image") -> Image.Image:
    """Create a basic placeholder image"""
    generator = ThemedPlaceholderGenerator()
    return generator.create_basic_placeholder(width, height, text)


def create_movie_placeholder(width: int = 300, height: int = 450,
                           title: str = "Movie Title",
                           subtitle: str = "Poster Not Available") -> Image.Image:
    """Create a movie poster placeholder"""
    generator = ThemedPlaceholderGenerator()
    return generator.create_movie_placeholder(width, height, title, subtitle)


def create_error_placeholder(width: int = 300, height: int = 400,
                           error_code: str = "404",
                           message: str = "Not Found") -> Image.Image:
    """Create an error placeholder"""
    generator = ThemedPlaceholderGenerator()
    return generator.create_error_placeholder(width, height, error_code, message)


def save_placeholder(img: Image.Image, filename: str):
    """Save placeholder image"""
    img.save(filename)
    print(f"✅ Saved: {filename}")


def placeholder_to_base64(img: Image.Image) -> str:
    """Convert placeholder to base64"""
    generator = ThemedPlaceholderGenerator()
    return generator.to_base64(img)


# Example usage and testing
if __name__ == "__main__":
    print("🎬 Themed Placeholder Generator")
    print("=" * 40)
    
    generator = ThemedPlaceholderGenerator()
    
    # Create output directory
    os.makedirs("placeholders", exist_ok=True)
    
    # Generate different types of placeholders
    print("\n📝 Generating placeholders...")
    
    # 1. Basic placeholder
    basic = generator.create_basic_placeholder(300, 400, "No Image\nAvailable")
    generator.save_image(basic, "placeholders/basic_placeholder.png")
    
    # 2. Movie poster placeholder
    movie = generator.create_movie_placeholder(300, 450, "The Dark Knight", "Poster Unavailable")
    generator.save_image(movie, "placeholders/movie_placeholder.png")
    
    # 3. Error placeholder
    error = generator.create_error_placeholder(400, 300, "404", "Image Not Found")
    generator.save_image(error, "placeholders/error_placeholder.png")
    
    # 4. Different sizes
    small = generator.create_movie_placeholder(200, 300, "Small", "Placeholder")
    generator.save_image(small, "placeholders/small_placeholder.png")
    
    large = generator.create_movie_placeholder(400, 600, "Large Movie Title", "High Res Placeholder")
    generator.save_image(large, "placeholders/large_placeholder.png")
    
    # 5. Generate base64 version
    print("\n🔗 Generating base64 version...")
    base64_img = generator.to_base64(movie)
    with open("placeholders/movie_placeholder_base64.txt", "w") as f:
        f.write(base64_img)
    print("✅ Saved: placeholders/movie_placeholder_base64.txt")
    
    print(f"\n🎉 Done! Generated {5} placeholder images in 'placeholders/' folder")
    print("\n📋 Usage in your code:")
    print("from themed_placeholder import create_movie_placeholder")
    print("img = create_movie_placeholder(300, 450, 'Movie Title', 'Not Available')")
    print("img.save('my_placeholder.png')")