import numpy as np
from PIL import Image
import colorsys
from collections import Counter
import re
import random

def get_dominant_color(image, num_colors=5, resize_width=150):
    """
    Extract dominant colors from an image using the simpler, more reliable method.
    
    Args:
        image: PIL Image object
        num_colors: Number of dominant colors to return
        resize_width: Width to resize image to for faster processing
        
    Returns:
        list: List of dicts with dominant colors in hex format and their frequency
    """
    # Resize image for faster processing
    height = int(resize_width * image.height / image.width)
    image = image.resize((resize_width, height), Image.LANCZOS)
    
    # Convert to RGB if not already
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Get image data as numpy array
    np_image = np.array(image)
    
    # Reshape the array to be a list of pixels
    pixels = np_image.reshape(-1, 3)
    
    # Filter out pure white and near-white pixels
    filtered_pixels = []
    for pixel in pixels:
        # Skip if all channels are > 245 (near white)
        if all(channel > 245 for channel in pixel):
            continue
        # Skip if all channels are < 10 (near black) 
        if all(channel < 10 for channel in pixel):
            continue
        # Skip near-gray pixels that are too light
        if max(pixel) - min(pixel) < 10 and sum(pixel)/3 > 240:
            continue
        filtered_pixels.append(tuple(pixel))
    
    # If we filtered too much, use original pixels but skip pure white/black
    if len(filtered_pixels) < 100:
        filtered_pixels = [tuple(pixel) for pixel in pixels 
                          if not (all(c == 255 for c in pixel) or all(c == 0 for c in pixel))]
    
    # Count occurrences of each color
    color_count = Counter(filtered_pixels)
    
    # Get the most common colors
    dominant_colors = color_count.most_common(num_colors * 2)  # Get extra to filter
    
    # Convert to hex format and calculate frequency
    total_pixels = len(filtered_pixels)
    result = []
    
    for color, count in dominant_colors:
        # Skip if this is too close to white or black
        if all(c > 250 for c in color) or all(c < 5 for c in color):
            continue
            
        hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
        frequency = count / total_pixels
        result.append({
            'rgb': color,
            'hex': hex_color.upper(),
            'frequency': frequency
        })
        
        if len(result) >= num_colors:
            break
    
    # If no good colors found, return middle gray as fallback
    if not result:
        result = [{
            'rgb': (128, 128, 128),
            'hex': '#808080',
            'frequency': 1.0
        }]
    
    return result

def hex_to_rgb(hex_color):
    """
    Convert hex color to RGB tuple.
    
    Args:
        hex_color: Color in hex format (e.g., '#FF5733')
        
    Returns:
        tuple: RGB values (0-255)
    """
    # Remove '#' if present
    hex_color = hex_color.lstrip('#')
    
    # Convert hex to RGB
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    """
    Convert RGB tuple to hex format.
    
    Args:
        rgb: RGB tuple (values 0-255)
        
    Returns:
        str: Color in hex format (e.g., '#FF5733')
    """
    return '#{:02X}{:02X}{:02X}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def get_relative_luminance(rgb):
    """
    Calculate relative luminance of a color according to WCAG 2.0.
    
    Args:
        rgb: RGB tuple (values 0-255)
        
    Returns:
        float: Relative luminance value
    """
    # Convert RGB values to sRGB
    r = rgb[0] / 255
    g = rgb[1] / 255
    b = rgb[2] / 255
    
    # Apply transformation
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    
    # Calculate luminance
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def get_contrast_ratio(color1, color2):
    """
    Calculate contrast ratio between two colors according to WCAG 2.0.
    
    Args:
        color1: Color in hex format (e.g., '#FF5733')
        color2: Color in hex format (e.g., '#3349FF')
        
    Returns:
        float: Contrast ratio (1-21)
    """
    # Convert hex to RGB
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    # Calculate luminance
    lum1 = get_relative_luminance(rgb1)
    lum2 = get_relative_luminance(rgb2)
    
    # Calculate contrast ratio
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    
    return (lighter + 0.05) / (darker + 0.05)

def get_complementary_color(hex_color, min_contrast=3.0):
    """
    Generate a complementary color for the given color.
    Simple approach: opposite hue with good contrast.
    
    Args:
        hex_color: Color in hex format (e.g., '#FF5733')
        min_contrast: Minimum desired contrast ratio
        
    Returns:
        str: Complementary color in hex format
    """
    # Convert hex to RGB then HSV
    rgb = hex_to_rgb(hex_color)
    h, s, v = colorsys.rgb_to_hsv(rgb[0]/255, rgb[1]/255, rgb[2]/255)
    
    # Get complementary hue (opposite on color wheel)
    h_comp = (h + 0.5) % 1.0
    
    # Adjust saturation and value for good contrast
    # If original is light, make complementary darker
    if v > 0.7:
        v_comp = v * 0.3
        s_comp = min(1.0, s * 1.2)
    # If original is dark, make complementary lighter
    elif v < 0.3:
        v_comp = 0.9
        s_comp = s * 0.8
    # If original is mid-tone, invert the value
    else:
        v_comp = 1.0 - v
        s_comp = s
    
    # Convert back to RGB
    r, g, b = colorsys.hsv_to_rgb(h_comp, s_comp, v_comp)
    rgb_comp = (int(r * 255), int(g * 255), int(b * 255))
    
    # Check if this is the problematic cyan color rgb(89, 178, 178)
    # Allow some tolerance for similar colors
    if (85 <= rgb_comp[0] <= 93 and 
        174 <= rgb_comp[1] <= 182 and 
        174 <= rgb_comp[2] <= 182):
        # Generate an alternative color by trying different hue rotations
        # Use input color as seed for consistent alternatives
        seed_value = sum(ord(c) for c in hex_color)
        random.seed(seed_value)
        
        # Try different hue shifts
        hue_shifts = [0.333, 0.667, 0.25, 0.75, 0.125, 0.875]
        hue_shift = random.choice(hue_shifts)
        h_alt = (h + hue_shift) % 1.0
        
        # Vary saturation and value based on original
        if v > 0.5:
            v_alt = random.uniform(0.15, 0.35)
            s_alt = random.uniform(0.6, 0.9)
        else:
            v_alt = random.uniform(0.65, 0.85)
            s_alt = random.uniform(0.4, 0.7)
            
        r, g, b = colorsys.hsv_to_rgb(h_alt, s_alt, v_alt)
        rgb_comp = (int(r * 255), int(g * 255), int(b * 255))
    
    hex_comp = rgb_to_hex(rgb_comp)
    
    # Check if contrast is sufficient
    contrast = get_contrast_ratio(hex_color, hex_comp)
    
    # If contrast is too low, force to opposite extreme
    if contrast < min_contrast:
        orig_lum = get_relative_luminance(rgb)
        if orig_lum > 0.5:
            # Original is light, use very dark complementary
            v_comp = 0.1
        else:
            # Original is dark, use very light complementary
            v_comp = 0.9
        
        r, g, b = colorsys.hsv_to_rgb(h_comp, s_comp, v_comp)
        rgb_comp = (int(r * 255), int(g * 255), int(b * 255))
        hex_comp = rgb_to_hex(rgb_comp)
    
    return hex_comp

def generate_text_color_with_contrast(background_color, avoid_color=None, min_contrast=4.5):
    """
    Generate a text color that contrasts well with the background and avoids similarity to avoid_color.
    
    Args:
        background_color: Background color in hex format
        avoid_color: Color to avoid being too similar to (optional)
        min_contrast: Minimum contrast ratio required (WCAG AA requires 4.5:1)
        
    Returns:
        str: Text color in hex format
    """
    bg_rgb = hex_to_rgb(background_color)
    bg_luminance = get_relative_luminance(bg_rgb)
    
    # Try these colors in order
    candidates = []
    
    # Primary candidates based on background luminance
    if bg_luminance > 0.5:
        candidates.extend(['#000000', '#1A1A1A', '#333333'])
    else:
        candidates.extend(['#FFFFFF', '#F5F5F5', '#E0E0E0'])
    
    # Additional candidates
    candidates.extend(['#FFFFFF', '#000000', '#333333', '#666666', '#999999', '#CCCCCC'])
    
    for color in candidates:
        contrast_bg = get_contrast_ratio(background_color, color)
        
        if avoid_color:
            contrast_avoid = get_contrast_ratio(avoid_color, color)
            # Ensure good contrast with both background and avoid_color
            if contrast_bg >= min_contrast and contrast_avoid >= 3.0:
                return color
        else:
            if contrast_bg >= min_contrast:
                return color
    
    # Fallback: return black or white (whichever has better contrast)
    white_contrast = get_contrast_ratio(background_color, '#FFFFFF')
    black_contrast = get_contrast_ratio(background_color, '#000000')
    
    return '#FFFFFF' if white_contrast > black_contrast else '#000000'

def generate_text_color_from_dominant(dominant_color, complementary_color, min_contrast=4.5):
    """
    Generate a text color based on the dominant color.
    
    If dominant already has good contrast with complementary (>= 4.5:1), use dominant.
    Otherwise, generate 100 random colors and pick the one closest to 4.5:1 contrast.
    
    Args:
        dominant_color: Dominant color in hex format
        complementary_color: Complementary color in hex format
        min_contrast: Target contrast ratio (default 4.5:1)
        
    Returns:
        str: Text color in hex format
    """
    # First check if dominant color already has good contrast with complementary
    dom_comp_contrast = get_contrast_ratio(dominant_color, complementary_color)
    
    if dom_comp_contrast >= min_contrast:
        # Dominant color already has good contrast, use it as text color
        return dominant_color
    
    # Otherwise, generate random colors and find the one closest to target contrast
    # Use a seed based on the input colors for reproducibility
    seed_string = dominant_color + complementary_color
    seed_value = sum(ord(c) for c in seed_string)
    random.seed(seed_value)
    
    best_color = dominant_color
    best_diff = abs(dom_comp_contrast - min_contrast)
    
    # Generate 100 random colors
    for _ in range(100):
        # Generate random RGB values
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        
        # Convert to hex
        random_color = rgb_to_hex((r, g, b))
        
        # Check contrast with complementary
        contrast = get_contrast_ratio(complementary_color, random_color)
        
        # Calculate how close this is to our target (4.5:1)
        diff = abs(contrast - min_contrast)
        
        # Keep track of the best one
        if diff < best_diff:
            best_diff = diff
            best_color = random_color
            
            # If we found exactly 4.5:1, we can stop
            if diff < 0.01:
                break
    
    return best_color 