#!/usr/bin/env python3
"""
MultiConverter v2.5.0 - Command Line Version
Multi-format scene converter (Alembic/USD to After Effects, USD, Maya MA)
"""

import argparse
import sys
from pathlib import Path

# Import the converter class from core module
from alembic_converter import AlembicToJSXConverter

# Supported file extensions
VALID_EXTENSIONS = {'.abc', '.usd', '.usda', '.usdc'}


def main():
    parser = argparse.ArgumentParser(
        prog='MultiConverter',
        description='Convert Alembic (.abc) or USD (.usd/.usda/.usdc) files to multiple formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export Alembic to all formats (default)
  python a2j.py input.abc --output-dir ./output

  # Export USD to specific formats
  python a2j.py input.usd --output-dir ./output --format ae maya_ma

  # Specify custom settings
  python a2j.py input.abc --output-dir ./output --shot-name Shot001 --fps 30 --frames 240

  # Legacy mode (backward compatible with v2.0.0)
  python a2j.py input.abc output.jsx --fps 24 --frames 120

Supported input formats:
  .abc     - Alembic scene files
  .usd     - USD scene files (text or binary)
  .usda    - USD ASCII format
  .usdc    - USD crate (binary) format

Output format descriptions:
  ae       - After Effects JSX + OBJ (skips vertex-animated meshes)
  usd      - USD .usdc binary format (with vertex animation support)
  maya     - Maya USD .usdc format (Maya 2022+ compatible)
  maya_ma  - Maya MA .ma native ASCII (references source for vertex animation)
        """
    )

    parser.add_argument('input', type=str, help='Input scene file (.abc, .usd, .usda, .usdc)')
    parser.add_argument('output', type=str, nargs='?',
                       help='[Legacy] Output JSX file OR use --output-dir for v2.3.0')
    parser.add_argument('--output-dir', type=str,
                       help='Output directory for all formats (creates subfolders per format)')
    parser.add_argument('--shot-name', type=str,
                       help='Shot name for files/folders (default: derived from input filename)')
    parser.add_argument('--format', nargs='+', choices=['ae', 'usd', 'maya', 'maya_ma'],
                       default=['ae', 'usd', 'maya', 'maya_ma'],
                       help='Formats to export (default: all formats)')
    parser.add_argument('--fps', type=int, default=24,
                       help='Frame rate (default: 24)')
    parser.add_argument('--frames', type=int,
                       help='Duration in frames (default: auto-detect from input file)')

    # Legacy compatibility arguments
    parser.add_argument('--comp-name', type=str,
                       help='[Legacy v2.0.0] Composition name (use --shot-name instead)')

    args = parser.parse_args()

    # Validate input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # Validate file extension
    file_ext = input_path.suffix.lower()
    if file_ext not in VALID_EXTENSIONS:
        print(f"Error: Unsupported file format: {file_ext}", file=sys.stderr)
        print(f"Supported formats: {', '.join(sorted(VALID_EXTENSIONS))}", file=sys.stderr)
        sys.exit(1)

    # Detect legacy mode vs new mode
    legacy_mode = False
    if args.output and not args.output_dir:
        # Legacy mode: second positional arg is JSX file path
        if args.output.endswith('.jsx'):
            legacy_mode = True
            output_jsx = args.output
            print("Running in legacy mode (v2.0.0 compatibility)")
            print("Note: Use --output-dir for v2.3.0 multi-format export\n")
        else:
            # Assume it's a directory
            args.output_dir = args.output

    if not legacy_mode and not args.output_dir:
        print("Error: Please specify --output-dir <directory>", file=sys.stderr)
        print("       OR use legacy mode: python a2j.py input.abc output.jsx", file=sys.stderr)
        sys.exit(1)

    # Set shot name
    shot_name = args.shot_name or args.comp_name or input_path.stem

    # Create converter with progress callback
    def progress_callback(message):
        print(message)

    converter = AlembicToJSXConverter(progress_callback=progress_callback)

    # Auto-detect frame count if not specified
    if args.frames is None:
        print("Auto-detecting frame count...")
        try:
            frame_count = converter.detect_frame_count(str(input_path), args.fps)
            print(f"Detected {frame_count} frames from input file\n")
        except Exception as e:
            print(f"Warning: Could not auto-detect frame count: {e}")
            frame_count = 120
            print(f"Using default: {frame_count} frames\n")
    else:
        frame_count = args.frames

    # Perform conversion
    if legacy_mode:
        # Legacy v2.0.0 mode
        print("="*60)
        print(f"Converting: {input_path.name}")
        print(f"Output: {output_jsx}")
        print(f"Shot: {shot_name}")
        print(f"FPS: {args.fps}")
        print(f"Frames: {frame_count}")
        print("="*60 + "\n")

        try:
            success = converter.convert(
                abc_file=str(input_path),
                jsx_file=output_jsx,
                fps=args.fps,
                frame_count=frame_count,
                comp_name=shot_name
            )

            if success:
                print("\n" + "="*60)
                print("✓ Conversion completed successfully!")
                print(f"✓ JSX file: {output_jsx}")
                print(f"✓ OBJ files: {Path(output_jsx).parent}")
                print("="*60)
            else:
                print("\n✗ Conversion failed", file=sys.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"\n✗ Conversion failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)

    else:
        # New v2.3.0 multi-format mode
        export_ae = 'ae' in args.format
        export_usd = 'usd' in args.format
        export_maya = 'maya' in args.format
        export_maya_ma = 'maya_ma' in args.format

        formats_str = ', '.join(args.format)

        try:
            results = converter.convert_multi_format(
                input_file=str(input_path),
                output_dir=args.output_dir,
                shot_name=shot_name,
                fps=args.fps,
                frame_count=frame_count,
                export_ae=export_ae,
                export_usd=export_usd,
                export_maya=export_maya,
                export_maya_ma=export_maya_ma
            )

            # Check results
            if results.get('success'):
                print("\n" + "="*60)
                print("✓ Multi-format export completed!")

                if 'ae' in results and results['ae'].get('success'):
                    ae_dir = Path(results['ae']['jsx_file']).parent
                    print(f"✓ After Effects: {ae_dir}")

                if 'usd' in results and results['usd'].get('success'):
                    print(f"✓ USD: {results['usd']['usd_file']}")

                if 'maya' in results and results['maya'].get('success'):
                    print(f"✓ Maya: {results['maya']['usd_file']}")

                if 'maya_ma' in results and results['maya_ma'].get('success'):
                    print(f"✓ Maya MA: {results['maya_ma']['ma_file']}")

                print("="*60)
            else:
                print("\n✗ Some exports failed:", file=sys.stderr)
                print(f"   {results.get('message', 'Check log above')}", file=sys.stderr)
                sys.exit(1)

        except Exception as e:
            print(f"\n✗ Conversion failed: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
