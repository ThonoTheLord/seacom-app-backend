#!/usr/bin/env python3
"""Create PNG versions of company logos for PDF use."""

from PIL import Image, ImageDraw
from pathlib import Path

assets_path = Path(__file__).parent / "app" / "assets"

# Create SAMO TELECOMS logo
try:
    samo_img = Image.new('RGBA', (300, 100), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(samo_img)
    # Simple text logo - can be replaced with actual logo image
    draw.text((10, 30), "SAMO TELECOMS", fill=(11, 34, 101, 255), font=None)
    samo_img.save(assets_path / "samo-logo.png")
    print("✓ Created SAMO TELECOMS logo (samo-logo.png)")
except Exception as e:
    print(f"✗ Failed to create SAMO logo: {e}")

# Create SEACOM logo  
try:
    seacom_img = Image.new('RGBA', (300, 100), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(seacom_img)
    # Simple text logo - can be replaced with actual logo image
    draw.text((10, 30), "SEACOM", fill=(11, 34, 101, 255), font=None)
    seacom_img.save(assets_path / "seacom-logo.png")
    print("✓ Created SEACOM logo (seacom-logo.png)")
except Exception as e:
    print(f"✗ Failed to create SEACOM logo: {e}")

print("\nNote: These are simple text-based placeholders.")
print("Replace with actual logo PNG files for production use.")


