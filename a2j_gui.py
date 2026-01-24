#!/usr/bin/env python3
"""
MultiConverter - Multi-Format Scene Converter
VFX-Experts Team
Converts Alembic, USD, and Maya files to After Effects JSX, USD, Maya, and FBX formats
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
        self.root.title("MultiConverter v2.7.0 - VFX-Experts")
        self.root.geometry("620x820")
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
            'warning': '#ffaa00',
        }

        # Variables
        self.abc_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.scene_name = tk.StringVar(value="Shot001")
        self.fps = tk.IntVar(value=24)
        self.frame_count = tk.IntVar(value=120)  # Auto-detected, stored internally

        # Input format detection
        self.detected_format = tk.StringVar(value="None")  # 'Alembic', 'USD', 'Maya', 'None'

        # Format selection (all checked by default)
        self.export_ae = tk.BooleanVar(value=True)
        self.export_usd = tk.BooleanVar(value=True)
        self.export_maya_ma = tk.BooleanVar(value=True)
        self.export_fbx = tk.BooleanVar(value=True)

        # Bind checkbox changes to update warnings
        self.export_ae.trace_add('write', lambda *args: self.update_warnings())
        self.export_usd.trace_add('write', lambda *args: self.update_warnings())
        self.export_maya_ma.trace_add('write', lambda *args: self.update_warnings())
        self.export_fbx.trace_add('write', lambda *args: self.update_warnings())

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

        version = ttk.Label(header_frame, text="v2.7.0", font=('Segoe UI', 10))
        version.pack()

        subtitle = ttk.Label(header_frame, text="VFX-Experts  |  Alembic / USD / Maya  →  AE, USD, Maya, FBX",
                            font=('Segoe UI', 9))
        subtitle.pack(pady=(5, 0))

        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # === TAB 1: Convert ===
        convert_tab = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(convert_tab, text="  Convert  ")

        # Input file
        ttk.Label(convert_tab, text="Input Scene File (.abc, .usd, .ma):").pack(anchor=tk.W, pady=(0, 5))
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

        # Format & Compatibility section (three columns)
        format_frame = ttk.LabelFrame(convert_tab, text="Format & Compatibility", padding="15")
        format_frame.pack(fill=tk.X, pady=(0, 15))

        # Configure three columns with weights
        format_frame.columnconfigure(0, weight=1)  # Input format
        format_frame.columnconfigure(1, weight=2)  # Warnings
        format_frame.columnconfigure(2, weight=1)  # Output formats

        # === LEFT COLUMN: Input Format ===
        input_col = ttk.Frame(format_frame)
        input_col.grid(row=0, column=0, sticky='nsew', padx=(0, 10))

        ttk.Label(input_col, text="Input Format", font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        ttk.Separator(input_col, orient='horizontal').pack(fill=tk.X, pady=(2, 8))

        # Format indicator (updates when file is loaded)
        self.format_indicator = ttk.Label(input_col, textvariable=self.detected_format,
                                          font=('Segoe UI', 11))
        self.format_indicator.pack(anchor=tk.W, pady=(5, 0))

        # Format description (wrapping enabled)
        self.format_desc = ttk.Label(input_col, text="",
                                     font=('Segoe UI', 8), foreground='gray',
                                     wraplength=100, justify='left')
        self.format_desc.pack(anchor=tk.W, pady=(2, 0))

        # Supported formats hint (shown when no file loaded)
        self.format_hints = ttk.Label(input_col,
                                      text="Supported:\n• Alembic (.abc)\n• USD (.usd)\n• Maya (.ma)",
                                      font=('Segoe UI', 10), foreground='gray',
                                      justify='left')
        self.format_hints.pack(anchor=tk.W, pady=(5, 0))

        # === CENTER COLUMN: Warnings ===
        warnings_col = ttk.Frame(format_frame)
        warnings_col.grid(row=0, column=1, sticky='nsew', padx=10)

        ttk.Label(warnings_col, text="Limitations", font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        ttk.Separator(warnings_col, orient='horizontal').pack(fill=tk.X, pady=(2, 8))

        # Warnings text widget (read-only)
        self.warnings_text = tk.Text(warnings_col, wrap=tk.WORD, height=6, width=30,
                                     bg=self.colors['entry_bg'],
                                     fg=self.colors['warning'],
                                     font=('Segoe UI', 10),
                                     relief='flat', borderwidth=0,
                                     state='disabled')
        self.warnings_text.pack(fill=tk.BOTH, expand=True)

        # === RIGHT COLUMN: Output Formats ===
        output_col = ttk.Frame(format_frame)
        output_col.grid(row=0, column=2, sticky='nsew', padx=(10, 0))

        ttk.Label(output_col, text="Export Formats", font=('Segoe UI', 9, 'bold')).pack(anchor=tk.W)
        ttk.Separator(output_col, orient='horizontal').pack(fill=tk.X, pady=(2, 8))

        self.ae_check = ttk.Checkbutton(output_col, text="After Effects",
                                         variable=self.export_ae)
        self.ae_check.pack(anchor=tk.W, pady=2)

        self.usd_check = ttk.Checkbutton(output_col, text="USD (.usdc)",
                                         variable=self.export_usd)
        self.usd_check.pack(anchor=tk.W, pady=2)

        self.maya_ma_check = ttk.Checkbutton(output_col, text="Maya (.ma)",
                                             variable=self.export_maya_ma)
        self.maya_ma_check.pack(anchor=tk.W, pady=2)

        self.fbx_check = ttk.Checkbutton(output_col, text="FBX (Unreal)",
                                         variable=self.export_fbx)
        self.fbx_check.pack(anchor=tk.W, pady=2)

        # Initialize warnings
        self.update_warnings()

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
        """Browse for input scene file (Alembic, USD, or Maya)"""
        filename = filedialog.askopenfilename(
            title="Select Scene File",
            filetypes=[
                ("Scene Files", "*.abc *.usd *.usda *.usdc *.ma"),
                ("Alembic Files", "*.abc"),
                ("USD Files", "*.usd *.usda *.usdc"),
                ("Maya ASCII Files", "*.ma"),
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

            # Detect input format and hide hints
            self.format_hints.pack_forget()  # Hide the hints once file is loaded
            ext = Path(filename).suffix.lower()

            # Reset all checkboxes to enabled first
            self.usd_check.config(state='normal')
            self.maya_ma_check.config(state='normal')
            self.export_usd.set(True)
            self.export_maya_ma.set(True)

            if ext == '.abc':
                self.detected_format.set("Alembic")
                self.format_desc.config(text="Camera, mesh, transform data")
            elif ext in ('.usd', '.usda', '.usdc'):
                self.detected_format.set("USD")
                self.format_desc.config(text="Camera, mesh, transform data")
                # Disable USD export when input is USD
                self.export_usd.set(False)
                self.usd_check.config(state='disabled')
            elif ext == '.ma':
                self.detected_format.set("Maya")
                self.format_desc.config(text="Camera, mesh, anim curves")
                # Disable Maya export when input is Maya
                self.export_maya_ma.set(False)
                self.maya_ma_check.config(state='disabled')
            else:
                self.detected_format.set("Unknown")
                self.format_desc.config(text="")

            # Update warnings based on new input format
            self.update_warnings()

            # Auto-detect frame count from scene file
            try:
                converter = AlembicToJSXConverter()
                detected_frames = converter.detect_frame_count(filename, self.fps.get())
                self.frame_count.set(detected_frames)
                self.log(f"Loaded: {Path(filename).name} ({self.detected_format.get()})")
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

    def update_warnings(self):
        """Update warnings text based on selected input/output formats"""
        warnings = []

        # Check which outputs are selected
        ae_selected = self.export_ae.get()
        fbx_selected = self.export_fbx.get()

        # Warnings specific to output formats
        if ae_selected:
            warnings.append("• Vertex animation not exported to After Effects")
        if fbx_selected:
            warnings.append("• FBX: Blend shapes exported, raw vertex cache not supported")

        # Universal warnings (always apply regardless of input format)
        warnings.append("• Rigs, skinning, constraints not supported")
        warnings.append("• Expressions, driven keys not supported")

        # Update the warnings text widget
        self.warnings_text.config(state='normal')
        self.warnings_text.delete(1.0, tk.END)
        self.warnings_text.insert(1.0, "\n".join(warnings))
        self.warnings_text.config(state='disabled')

    def start_conversion(self):
        """Start the conversion process in a separate thread"""
        # Validate inputs
        if not self.abc_file.get():
            messagebox.showerror("Error", "Please select an input scene file (.abc, .usd, or .ma)")
            return

        if not self.output_dir.get():
            messagebox.showerror("Error", "Please specify an output directory")
            return

        if not Path(self.abc_file.get()).exists():
            messagebox.showerror("Error", "Input file does not exist")
            return

        # Validate file extension
        valid_extensions = {'.abc', '.usd', '.usda', '.usdc', '.ma'}
        file_ext = Path(self.abc_file.get()).suffix.lower()
        if file_ext not in valid_extensions:
            messagebox.showerror("Error", f"Invalid file type: {file_ext}\nSupported: .abc, .usd, .usda, .usdc, .ma")
            return

        # Check if at least one format is selected
        if not (self.export_ae.get() or self.export_usd.get() or self.export_maya_ma.get() or self.export_fbx.get()):
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
                export_maya_ma=self.export_maya_ma.get(),
                export_fbx=self.export_fbx.get()
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

                if 'maya_ma' in results and results['maya_ma'].get('success'):
                    maya_ma_file = results['maya_ma']['ma_file']
                    message_lines.append(f"Maya MA: {maya_ma_file}")

                if 'fbx' in results and results['fbx'].get('success'):
                    fbx_file = results['fbx']['fbx_file']
                    message_lines.append(f"FBX: {fbx_file}")

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
