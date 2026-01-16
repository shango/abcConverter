#!/usr/bin/env python3
"""
MultiConverter - Multi-Format Scene Converter
VFX-Experts Team
Converts Alembic and USD files to After Effects JSX, USD, and Maya formats
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import sys
import os

# Try to import Sun Valley theme
try:
    import sv_ttk
    HAS_SV_TTK = True
except ImportError:
    HAS_SV_TTK = False

# Import core converter from module
from alembic_converter import AlembicToJSXConverter


class MultiConverterGUI:
    """GUI Application"""

    def __init__(self, root):
        self.root = root
        self.root.title("MultiConverter v2.5.0 - VFX-Experts")
        self.root.geometry("500x780")
        self.root.resizable(False, False)

        # Apply Sun Valley dark theme if available
        if HAS_SV_TTK:
            sv_ttk.set_theme("dark")

        # Fallback colors for non-themed widgets (like tk.Text)
        self.colors = {
            'bg': '#1c1c1c',
            'entry_bg': '#2d2d2d',
            'text': '#ffffff',
            'text_dim': '#a0a0a0',
        }

        # Variables
        self.abc_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.scene_name = tk.StringVar(value="Shot001")
        self.fps = tk.IntVar(value=24)
        self.frame_count = tk.IntVar(value=120)  # Auto-detected, stored internally

        # Format selection (all checked by default)
        self.export_ae = tk.BooleanVar(value=True)
        self.export_usd = tk.BooleanVar(value=True)
        self.export_maya = tk.BooleanVar(value=True)
        self.export_maya_ma = tk.BooleanVar(value=True)

        self.setup_ui()

    def setup_ui(self):
        """Create the user interface with tabbed layout"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header frame (full width, above tabs)
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        title = ttk.Label(header_frame, text="MultiConverter", font=('Segoe UI', 20, 'bold'))
        title.pack()

        version = ttk.Label(header_frame, text="v2.5.0", font=('Segoe UI', 10))
        version.pack()

        subtitle = ttk.Label(header_frame, text="VFX-Experts  |  Scene Converter - Alembic/USD to AE, USD, Maya",
                            font=('Segoe UI', 9))
        subtitle.pack(pady=(5, 0))

        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # === TAB 1: Convert ===
        convert_tab = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(convert_tab, text="  Convert  ")

        # Input file
        ttk.Label(convert_tab, text="Input Scene File (.abc, .usd):").pack(anchor=tk.W, pady=(0, 5))
        input_frame = ttk.Frame(convert_tab)
        input_frame.pack(fill=tk.X, pady=(0, 15))

        abc_entry = ttk.Entry(input_frame, textvariable=self.abc_file)
        abc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_abc_btn = ttk.Button(input_frame, text="Browse...", command=self.browse_abc, width=10)
        browse_abc_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Output directory
        ttk.Label(convert_tab, text="Output Directory:").pack(anchor=tk.W, pady=(0, 5))
        output_frame = ttk.Frame(convert_tab)
        output_frame.pack(fill=tk.X, pady=(0, 15))

        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        browse_output_btn = ttk.Button(output_frame, text="Browse...", command=self.browse_output, width=10)
        browse_output_btn.pack(side=tk.LEFT, padx=(10, 0))

        # Settings frame
        settings_frame = ttk.LabelFrame(convert_tab, text="Export Settings", padding="15")
        settings_frame.pack(fill=tk.X, pady=(10, 15))

        # Scene name and FPS in a row
        row1 = ttk.Frame(settings_frame)
        row1.pack(fill=tk.X, pady=2)

        ttk.Label(row1, text="Scene Name:").pack(side=tk.LEFT)
        scene_name_entry = ttk.Entry(row1, textvariable=self.scene_name, width=20)
        scene_name_entry.pack(side=tk.LEFT, padx=(5, 20))

        ttk.Label(row1, text="FPS:").pack(side=tk.LEFT)
        fps_entry = ttk.Entry(row1, textvariable=self.fps, width=6)
        fps_entry.pack(side=tk.LEFT, padx=(5, 0))

        # Format selection checkboxes
        format_frame = ttk.LabelFrame(convert_tab, text="Export Formats", padding="15")
        format_frame.pack(fill=tk.X, pady=(0, 15))

        ae_check = ttk.Checkbutton(format_frame, text="After Effects JSX + OBJ",
                                   variable=self.export_ae)
        ae_check.pack(anchor=tk.W, pady=3)

        usd_check = ttk.Checkbutton(format_frame, text="USD (.usdc)",
                                    variable=self.export_usd)
        usd_check.pack(anchor=tk.W, pady=3)

        maya_check = ttk.Checkbutton(format_frame, text="Maya USD (.usdc)",
                                     variable=self.export_maya)
        maya_check.pack(anchor=tk.W, pady=3)

        maya_ma_check = ttk.Checkbutton(format_frame, text="Maya MA (.ma)",
                                        variable=self.export_maya_ma)
        maya_ma_check.pack(anchor=tk.W, pady=3)

        # Progress bar
        progress_frame = ttk.Frame(convert_tab)
        progress_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(progress_frame, text="Progress:").pack(anchor=tk.W, pady=(0, 5))
        self.progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X)

        # Convert button
        self.convert_btn = ttk.Button(convert_tab, text="Convert", command=self.start_conversion,
                                      style='Accent.TButton')
        self.convert_btn.pack(pady=(10, 0), ipadx=30, ipady=8)

        # === TAB 2: Log ===
        log_tab = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(log_tab, text="  Log  ")

        # Log text area (full size)
        log_frame = ttk.Frame(log_tab)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD,
                                bg=self.colors['entry_bg'],
                                fg=self.colors['text'],
                                insertbackground=self.colors['text'],
                                font=('Consolas', 10),
                                relief='flat',
                                borderwidth=0)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Clear log button
        clear_btn = ttk.Button(log_tab, text="Clear Log", command=self.clear_log)
        clear_btn.pack(pady=(10, 0))

    def browse_abc(self):
        """Browse for input scene file (Alembic or USD)"""
        filename = filedialog.askopenfilename(
            title="Select Scene File",
            filetypes=[
                ("Scene Files", "*.abc *.usd *.usda *.usdc"),
                ("Alembic Files", "*.abc"),
                ("USD Files", "*.usd *.usda *.usdc"),
                ("All Files", "*.*")
            ]
        )
        if filename:
            self.abc_file.set(filename)
            # Auto-suggest output directory
            if not self.output_dir.get():
                output_path = Path(filename).parent
                self.output_dir.set(str(output_path))
            # Auto-set scene name to filename (without extension)
            scene_name = Path(filename).stem
            self.scene_name.set(scene_name)
            # Auto-detect frame count from scene file
            try:
                converter = AlembicToJSXConverter()
                detected_frames = converter.detect_frame_count(filename, self.fps.get())
                self.frame_count.set(detected_frames)
                self.log(f"Loaded: {Path(filename).name}")
                self.log(f"Detected {detected_frames} frames")
            except Exception as e:
                self.log(f"Could not auto-detect frame count: {e}")

    def browse_output(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            title="Select Output Directory"
        )
        if directory:
            self.output_dir.set(directory)

    def log(self, message):
        """Add message to log text area"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def clear_log(self):
        """Clear the log text area"""
        self.log_text.delete(1.0, tk.END)

    def start_conversion(self):
        """Start the conversion process in a separate thread"""
        # Validate inputs
        if not self.abc_file.get():
            messagebox.showerror("Error", "Please select an input scene file (.abc or .usd)")
            return

        if not self.output_dir.get():
            messagebox.showerror("Error", "Please specify an output directory")
            return

        if not Path(self.abc_file.get()).exists():
            messagebox.showerror("Error", "Input file does not exist")
            return

        # Validate file extension
        valid_extensions = {'.abc', '.usd', '.usda', '.usdc'}
        file_ext = Path(self.abc_file.get()).suffix.lower()
        if file_ext not in valid_extensions:
            messagebox.showerror("Error", f"Invalid file type: {file_ext}\nSupported: .abc, .usd, .usda, .usdc")
            return

        # Check if at least one format is selected
        if not (self.export_ae.get() or self.export_usd.get() or self.export_maya.get() or self.export_maya_ma.get()):
            messagebox.showerror("Error", "Please select at least one export format")
            return

        # Clear log and switch to log tab
        self.log_text.delete(1.0, tk.END)
        self.notebook.select(1)  # Switch to Log tab

        # Disable button and start progress
        self.convert_btn.config(state='disabled')
        self.progress.start()

        # Run conversion in separate thread
        thread = threading.Thread(target=self.run_conversion)
        thread.daemon = True
        thread.start()

    def run_conversion(self):
        """Run the actual conversion"""
        try:
            converter = AlembicToJSXConverter(progress_callback=self.log)

            results = converter.convert_multi_format(
                input_file=self.abc_file.get(),
                output_dir=self.output_dir.get(),
                shot_name=self.scene_name.get(),
                fps=self.fps.get(),
                frame_count=self.frame_count.get(),
                export_ae=self.export_ae.get(),
                export_usd=self.export_usd.get(),
                export_maya=self.export_maya.get(),
                export_maya_ma=self.export_maya_ma.get()
            )

            if results.get('success'):
                # Build success message
                message_lines = ["Conversion complete!\n\n"]

                if 'ae' in results and results['ae'].get('success'):
                    ae_dir = Path(results['ae']['jsx_file']).parent
                    message_lines.append(f"After Effects: {ae_dir}")

                if 'usd' in results and results['usd'].get('success'):
                    usd_file = results['usd']['usd_file']
                    message_lines.append(f"USD: {usd_file}")

                if 'maya' in results and results['maya'].get('success'):
                    maya_file = results['maya']['usd_file']
                    message_lines.append(f"Maya: {maya_file}")

                if 'maya_ma' in results and results['maya_ma'].get('success'):
                    maya_ma_file = results['maya_ma']['ma_file']
                    message_lines.append(f"Maya MA: {maya_ma_file}")

                self.root.after(0, lambda: messagebox.showinfo(
                    "Success",
                    "\n".join(message_lines)
                ))
            else:
                self.root.after(0, lambda: messagebox.showwarning(
                    "Warning",
                    f"Some exports failed.\n\n{results.get('message', 'Check log for details.')}"
                ))

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Conversion failed:\n{str(e)}"))

        finally:
            self.root.after(0, self.conversion_complete)

    def conversion_complete(self):
        """Re-enable UI after conversion"""
        self.progress.stop()
        self.convert_btn.config(state='normal')


def main():
    root = tk.Tk()
    app = MultiConverterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
