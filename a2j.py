#!/usr/bin/env python3
"""
Alembic to After Effects JSX Converter - Command Line Version
Convert Alembic files to AE compatible JSX with OBJ export
"""

import argparse
import sys
from pathlib import Path

# Import the converter class from core module
# Both CLI and GUI use the same converter for 100% parity
from alembic_converter import AlembicToJSXConverter


def main():
    parser = argparse.ArgumentParser(
        description='Convert Alembic (.abc) files to After Effects JSX scripts with OBJ export',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion with auto-detection
  python a2j.py input.abc output.jsx

  # Specify custom frame rate and duration
  python a2j.py input.abc output.jsx --fps 30 --frames 240

  # Custom composition name
  python a2j.py input.abc output.jsx --comp-name "MyScene"

  # Full example
  python a2j.py scene.abc scene.jsx --fps 24 --frames 165 --comp-name "TrackingScene"
        """
    )

    parser.add_argument('input', type=str, help='Input Alembic (.abc) file path')
    parser.add_argument('output', type=str, help='Output JSX (.jsx) file path')
    parser.add_argument('--fps', type=int, default=24, help='Frame rate (default: 24)')
    parser.add_argument('--frames', type=int, help='Duration in frames (default: auto-detect from Alembic)')
    parser.add_argument('--comp-name', type=str, help='Composition name (default: derived from input filename)')

    args = parser.parse_args()

    # Validate input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    if not input_path.suffix.lower() == '.abc':
        print(f"Warning: Input file doesn't have .abc extension: {args.input}", file=sys.stderr)

    # Set composition name
    comp_name = args.comp_name if args.comp_name else input_path.stem

    # Create converter with progress callback
    def progress_callback(message):
        print(message)

    converter = AlembicToJSXConverter(progress_callback=progress_callback)

    # Auto-detect frame count if not specified
    if args.frames is None:
        print("Auto-detecting frame count...")
        try:
            frame_count = converter.detect_frame_count(str(input_path), args.fps)
            print(f"Detected {frame_count} frames from Alembic file")
        except Exception as e:
            print(f"Warning: Could not auto-detect frame count: {e}")
            frame_count = 120
            print(f"Using default: {frame_count} frames")
    else:
        frame_count = args.frames

    # Perform conversion
    print("\n" + "="*60)
    print(f"Converting: {input_path.name}")
    print(f"Output: {args.output}")
    print(f"Composition: {comp_name}")
    print(f"FPS: {args.fps}")
    print(f"Frames: {frame_count}")
    print("="*60 + "\n")

    try:
        converter.convert(
            abc_file=str(input_path),
            jsx_file=args.output,
            fps=args.fps,
            frame_count=frame_count,
            comp_name=comp_name
        )

        print("\n" + "="*60)
        print("✓ Conversion completed successfully!")
        print(f"✓ JSX file: {args.output}")
        print(f"✓ OBJ files: {Path(args.output).parent}")
        print("="*60)
        print("\nNext steps:")
        print("1. Open After Effects")
        print("2. Go to: File → Scripts → Run Script File")
        print(f"3. Select: {args.output}")
        print("4. The composition will auto-open with all elements")

    except Exception as e:
        print(f"\n✗ Conversion failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
