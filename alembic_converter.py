#!/usr/bin/env python3
"""
Alembic Converter - Main Orchestrator Module
Coordinates multi-format export using modular exporters
"""

from pathlib import Path

# Import core modules
from core.alembic_reader import AlembicReader
from core.animation_detector import AnimationDetector

# Import exporters
from exporters.ae_exporter import AfterEffectsExporter
from exporters.usd_exporter import USDExporter


class AlembicToJSXConverter:
    """Multi-format Alembic converter (orchestrator/facade)

    This class coordinates the conversion process:
    1. Read Alembic file ONCE (via AlembicReader)
    2. Analyze animation types ONCE (via AnimationDetector)
    3. Export to selected formats (via format-specific exporters)

    Supports:
    - After Effects JSX + OBJ (skips vertex-animated meshes)
    - USD .usdc (with vertex animation support)
    - Maya USD .usdc (reuses USD exporter)
    """

    def __init__(self, progress_callback=None):
        """Initialize converter

        Args:
            progress_callback: Optional function to call for progress updates
                              Signature: callback(message: str) -> None
        """
        self.progress_callback = progress_callback

    def log(self, message):
        """Send progress updates to callback"""
        if self.progress_callback:
            self.progress_callback(message)
        print(message)

    def convert_multi_format(self, abc_file, output_dir, shot_name, fps=24, frame_count=None,
                            export_ae=True, export_usd=True, export_maya=True):
        """Convert Alembic to multiple formats

        This is the main entry point for v2.1.0 multi-format export.

        Args:
            abc_file: Path to input Alembic (.abc) file
            output_dir: Output directory for all formats
            shot_name: Shot name for file/folder naming
            fps: Frames per second (default: 24)
            frame_count: Number of frames (None = auto-detect)
            export_ae: Export to After Effects JSX + OBJ
            export_usd: Export to USD (.usdc)
            export_maya: Export to Maya USD (.usdc)

        Returns:
            dict: Results with keys:
                - 'success': bool
                - 'ae': AE export results (if export_ae=True)
                - 'usd': USD export results (if export_usd=True)
                - 'maya': Maya export results (if export_maya=True)
                - 'message': Summary message
        """
        try:
            self.log(f"\n{'='*60}")
            self.log(f"abcConverter v2.1.0 - Multi-Format Export")
            self.log(f"{'='*60}")
            self.log(f"Input: {abc_file}")
            self.log(f"Output: {output_dir}")
            self.log(f"Shot: {shot_name}")
            self.log(f"{'='*60}\n")

            results = {
                'success': False,
                'message': ''
            }

            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Step 1: Read Alembic file ONCE
            self.log("Step 1/4: Reading Alembic file...")
            reader = AlembicReader(abc_file)

            # Auto-detect frame count if not provided
            if frame_count is None:
                frame_count = reader.detect_frame_count(fps)
                self.log(f"  Auto-detected frame count: {frame_count}")
            else:
                self.log(f"  Frame count: {frame_count}")

            self.log(f"  FPS: {fps}")

            # Step 2: Analyze animation types ONCE
            self.log("\nStep 2/4: Analyzing animation types...")
            detector = AnimationDetector(tolerance=0.0001)
            animation_data = detector.analyze_scene(reader, frame_count, fps)

            # Log animation summary
            self.log(detector.get_animation_summary(animation_data))

            # Step 3: Export to selected formats
            self.log("\nStep 3/4: Exporting to selected formats...")

            # Export to After Effects
            if export_ae:
                self.log(f"\n--- After Effects Export ---")
                ae_dir = output_path / f"{shot_name}_ae"
                exporter = AfterEffectsExporter(self.progress_callback)
                results['ae'] = exporter.export(reader, ae_dir, shot_name, fps, frame_count, animation_data)

            # Export to USD
            if export_usd:
                self.log(f"\n--- USD Export ---")
                usd_dir = output_path / f"{shot_name}_usd"
                exporter = USDExporter(self.progress_callback)
                results['usd'] = exporter.export(reader, usd_dir, shot_name, fps, frame_count, animation_data)

            # Export to Maya (uses USD exporter)
            if export_maya:
                self.log(f"\n--- Maya USD Export ---")
                maya_dir = output_path / f"{shot_name}_maya"
                exporter = USDExporter(self.progress_callback)
                results['maya'] = exporter.export(reader, maya_dir, shot_name, fps, frame_count, animation_data)

            # Step 4: Summary
            self.log(f"\n{'='*60}")
            self.log(f"Export Complete!")
            self.log(f"{'='*60}")

            success_count = sum(1 for key in ['ae', 'usd', 'maya']
                              if key in results and results[key].get('success', False))

            results['success'] = success_count > 0
            results['message'] = f"Successfully exported {success_count} format(s)"

            self.log(f"\nSummary:")
            if 'ae' in results:
                status = "✓" if results['ae'].get('success') else "✗"
                self.log(f"  {status} After Effects: {results['ae'].get('message', 'N/A')}")
            if 'usd' in results:
                status = "✓" if results['usd'].get('success') else "✗"
                self.log(f"  {status} USD: {results['usd'].get('message', 'N/A')}")
            if 'maya' in results:
                status = "✓" if results['maya'].get('success') else "✗"
                self.log(f"  {status} Maya: {results['maya'].get('message', 'N/A')}")

            self.log(f"\n{results['message']}")
            self.log(f"{'='*60}\n")

            return results

        except Exception as e:
            self.log(f"\nERROR: {str(e)}")
            import traceback
            self.log(traceback.format_exc())
            return {
                'success': False,
                'message': f"Conversion failed: {str(e)}"
            }

    def convert(self, abc_file, jsx_file, fps=24, frame_count=120, comp_name="AlembicScene"):
        """Legacy conversion method for backward compatibility with v2.0.0

        This method maintains the original API for existing code/scripts.
        It internally calls convert_multi_format() with AE-only settings.

        Args:
            abc_file: Path to input Alembic (.abc) file
            jsx_file: Path to output JSX file
            fps: Frames per second (default: 24)
            frame_count: Number of frames (default: 120)
            comp_name: Composition name (default: "AlembicScene")

        Returns:
            bool: True if conversion succeeded, False otherwise
        """
        self.log("Running in legacy mode (v2.0.0 compatibility)")
        self.log("Note: Using new v2.1.0 architecture internally")

        # Extract output directory from JSX file path
        jsx_path = Path(jsx_file)
        output_dir = jsx_path.parent

        # Use the parent directory as output, but name it with the comp name
        result = self.convert_multi_format(
            abc_file=abc_file,
            output_dir=output_dir,
            shot_name=comp_name,
            fps=fps,
            frame_count=frame_count,
            export_ae=True,
            export_usd=False,
            export_maya=False
        )

        # If successful, move/rename the JSX file to match the expected path
        if result.get('success') and 'ae' in result:
            ae_result = result['ae']
            if ae_result.get('success'):
                # The AE exporter creates a folder like "comp_name_ae"
                # We need to move the JSX file to the specified jsx_file path
                generated_jsx = Path(ae_result['jsx_file'])
                if generated_jsx != jsx_path:
                    # Move JSX and OBJ files to the specified location
                    import shutil
                    jsx_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(generated_jsx), str(jsx_path))

                    # Move OBJ files
                    generated_dir = generated_jsx.parent
                    for obj_file in generated_dir.glob('*.obj'):
                        shutil.move(str(obj_file), str(jsx_path.parent / obj_file.name))

                    # Remove the generated folder if empty
                    try:
                        generated_dir.rmdir()
                    except:
                        pass

                self.log(f"\n✓ Conversion complete (legacy mode)")
                return True

        return False

    def detect_frame_count(self, abc_file, fps=24):
        """Detect frame count from Alembic file

        This is a convenience method that wraps AlembicReader.detect_frame_count()

        Args:
            abc_file: Path to Alembic (.abc) file
            fps: Frames per second

        Returns:
            int: Number of frames
        """
        reader = AlembicReader(abc_file)
        return reader.detect_frame_count(fps)
