#!/usr/bin/env python3
"""
Check if Alembic files are HDF5 or Ogawa format
"""

import sys

def check_alembic_format(filename):
    """Check if an Alembic file is HDF5 or Ogawa format"""
    try:
        with open(filename, 'rb') as f:
            # Read first 8 bytes
            header = f.read(8)

            # HDF5 files start with: \x89HDF\r\n\x1a\n
            # Ogawa files start with: Ogawa (0x4F67617761)

            if header.startswith(b'\x89HDF'):
                return "HDF5"
            elif header.startswith(b'Ogawa'):
                return "Ogawa"
            else:
                return f"Unknown (header: {header.hex()})"
    except Exception as e:
        return f"Error: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_abc_format.py <file1.abc> [file2.abc] ...")
        sys.exit(1)

    for filename in sys.argv[1:]:
        format_type = check_alembic_format(filename)
        print(f"{filename}: {format_type}")
