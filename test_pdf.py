#!/usr/bin/env python3
from app.services.pdf import PDFService

try:
    service = PDFService()
    print("✓ PDF service imports successfully")
    print(f"✓ Assets path: {service.assets_path}")
    print(f"✓ Assets path exists: {service.assets_path.exists()}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
