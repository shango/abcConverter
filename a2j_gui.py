#!/usr/bin/env python3
"""
Alembic to After Effects JSX Converter - GUI Version
User-friendly interface for converting Alembic files to AE compatible JSX with OBJ export
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import sys
import os

# Import core converter from module
from alembic_converter import AlembicToJSXConverter


class AlembicToJSXGUI:
    """GUI Application"""

    def __init__(self, root):
        self.root = root
        self.root.title("abcConverter v2.1.0")
        self.root.geometry("650x900")
        self.root.resizable(False, False)

        # Grayscale theme colors
        self.colors = {
            'bg': '#2a2a2a',           # Dark gray background
            'bg_light': '#3a3a3a',     # Slightly lighter gray
            'accent': '#4a4a4a',       # Medium gray accent
            'highlight': '#7a7a7a',    # Light gray highlight
            'text': '#ffffff',         # White text for better visibility
            'text_dim': '#a0a0a0',     # Dimmed gray text
            'entry_bg': '#1a1a1a',     # Very dark gray entry background
            'entry_text': '#ffffff',   # White text in entries
            'button_bg': '#555555',    # Medium-dark gray button
            'button_hover': '#666666', # Lighter gray on hover
            'button_text': '#ffffff',  # White button text
        }

        # Configure root window
        self.root.configure(bg=self.colors['bg'])

        # Variables
        self.abc_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.shot_name = tk.StringVar(value="Shot001")
        self.fps = tk.IntVar(value=24)
        self.frame_count = tk.IntVar(value=120)  # Default to 120 frames (5 seconds at 24fps)

        # Format selection (all checked by default)
        self.export_ae = tk.BooleanVar(value=True)
        self.export_usd = tk.BooleanVar(value=True)
        self.export_maya = tk.BooleanVar(value=True)

        self.setup_theme()
        self.setup_ui()

    def setup_theme(self):
        """Configure dark theme for ttk widgets"""
        style = ttk.Style()

        # Configure TFrame
        style.configure('Dark.TFrame', background=self.colors['bg'])
        style.configure('Accent.TFrame', background=self.colors['accent'])

        # Configure TLabel
        style.configure('Dark.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 9))
        style.configure('Title.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['highlight'],
                       font=('Segoe UI', 18, 'bold'))
        style.configure('Subtitle.TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['text_dim'],
                       font=('Segoe UI', 10))

        # Configure TEntry
        style.configure('Dark.TEntry',
                       fieldbackground=self.colors['entry_bg'],
                       foreground=self.colors['entry_text'],
                       insertcolor=self.colors['entry_text'],
                       borderwidth=1,
                       relief='flat')
        style.map('Dark.TEntry',
                 fieldbackground=[('readonly', self.colors['entry_bg'])],
                 foreground=[('readonly', self.colors['entry_text'])])

        # Configure TButton
        style.configure('Dark.TButton',
                       background=self.colors['accent'],
                       foreground=self.colors['button_text'],
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10))
        style.map('Dark.TButton',
                 background=[('active', self.colors['bg_light'])],
                 foreground=[('active', self.colors['button_text'])])

        # Configure Convert button (larger and highlighted)
        style.configure('Convert.TButton',
                       background=self.colors['button_bg'],
                       foreground=self.colors['button_text'],
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 12, 'bold'),
                       padding=(20, 10))
        style.map('Convert.TButton',
                 background=[('active', self.colors['button_hover'])],
                 foreground=[('active', self.colors['button_text'])])

        # Configure TLabelframe
        style.configure('Dark.TLabelframe',
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       borderwidth=1,
                       relief='solid')
        style.configure('Dark.TLabelframe.Label',
                       background=self.colors['bg'],
                       foreground=self.colors['highlight'],
                       font=('Segoe UI', 10, 'bold'))

        # Configure Progressbar
        style.configure('Dark.Horizontal.TProgressbar',
                       background=self.colors['highlight'],
                       troughcolor=self.colors['accent'],
                       borderwidth=0,
                       thickness=8)

    def setup_ui(self):
        """Create the user interface"""
        # Title
        title = ttk.Label(self.root, text="abcConverter",
                         style='Title.TLabel')
        title.pack(pady=(25, 5))

        version = ttk.Label(self.root, text="v2.1.0",
                           style='Subtitle.TLabel')
        version.pack(pady=(0, 5))

        subtitle = ttk.Label(self.root, text="Multi-Format Alembic Converter (AE, USD, Maya)",
                            style='Subtitle.TLabel')
        subtitle.pack(pady=(0, 15))

        # Main frame
        main_frame = ttk.Frame(self.root, padding="20", style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=False)

        # Input file
        ttk.Label(main_frame, text="Input Alembic File (.abc):", style='Dark.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)
        abc_entry = tk.Entry(main_frame, textvariable=self.abc_file, width=45,
                            bg=self.colors['entry_bg'], fg=self.colors['entry_text'],
                            insertbackground=self.colors['entry_text'], relief='flat', borderwidth=2)
        abc_entry.grid(row=1, column=0, pady=5, ipady=3)
        browse_abc_btn = tk.Button(main_frame, text="Browse...", command=self.browse_abc,
                                   bg=self.colors['accent'], fg=self.colors['button_text'],
                                   activebackground=self.colors['bg_light'], activeforeground=self.colors['button_text'],
                                   relief='flat', borderwidth=0, padx=15, pady=5, cursor='hand2')
        browse_abc_btn.grid(row=1, column=1, padx=5)

        # Output directory
        ttk.Label(main_frame, text="Output Directory:", style='Dark.TLabel').grid(row=2, column=0, sticky=tk.W, pady=5)
        output_entry = tk.Entry(main_frame, textvariable=self.output_dir, width=45,
                               bg=self.colors['entry_bg'], fg=self.colors['entry_text'],
                               insertbackground=self.colors['entry_text'], relief='flat', borderwidth=2)
        output_entry.grid(row=3, column=0, pady=5, ipady=3)
        browse_output_btn = tk.Button(main_frame, text="Browse...", command=self.browse_output,
                                      bg=self.colors['accent'], fg=self.colors['button_text'],
                                      activebackground=self.colors['bg_light'], activeforeground=self.colors['button_text'],
                                      relief='flat', borderwidth=0, padx=15, pady=5, cursor='hand2')
        browse_output_btn.grid(row=3, column=1, padx=5)

        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Export Settings", padding="10", style='Dark.TLabelframe')
        settings_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)

        ttk.Label(settings_frame, text="Shot Name:", style='Dark.TLabel').grid(row=0, column=0, sticky=tk.W, pady=3)
        shot_name_entry = tk.Entry(settings_frame, textvariable=self.shot_name, width=30,
                                   bg=self.colors['entry_bg'], fg=self.colors['entry_text'],
                                   insertbackground=self.colors['entry_text'], relief='flat', borderwidth=1)
        shot_name_entry.grid(row=0, column=1, pady=3, padx=5, ipady=2)

        ttk.Label(settings_frame, text="Frame Rate (fps):", style='Dark.TLabel').grid(row=1, column=0, sticky=tk.W, pady=3)
        fps_entry = tk.Entry(settings_frame, textvariable=self.fps, width=15,
                            bg=self.colors['entry_bg'], fg=self.colors['entry_text'],
                            insertbackground=self.colors['entry_text'], relief='flat', borderwidth=1)
        fps_entry.grid(row=1, column=1, sticky=tk.W, pady=3, padx=5, ipady=2)

        ttk.Label(settings_frame, text="Duration (frames):", style='Dark.TLabel').grid(row=2, column=0, sticky=tk.W, pady=3)
        frame_entry = tk.Entry(settings_frame, textvariable=self.frame_count, width=15,
                              bg=self.colors['entry_bg'], fg=self.colors['entry_text'],
                              insertbackground=self.colors['entry_text'], relief='flat', borderwidth=1)
        frame_entry.grid(row=2, column=1, sticky=tk.W, pady=3, padx=5, ipady=2)

        # Note: Width and Height are now auto-extracted from Alembic camera metadata

        # Format selection checkboxes
        format_frame = ttk.LabelFrame(main_frame, text="Export Formats", padding="10", style='Dark.TLabelframe')
        format_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        ae_check = tk.Checkbutton(format_frame, text="☑ After Effects JSX + OBJ",
                                 variable=self.export_ae,
                                 bg=self.colors['bg'], fg=self.colors['text'],
                                 selectcolor=self.colors['entry_bg'],
                                 activebackground=self.colors['bg'], activeforeground=self.colors['text'],
                                 font=('Segoe UI', 10), cursor='hand2')
        ae_check.grid(row=0, column=0, sticky=tk.W, pady=3)

        usd_check = tk.Checkbutton(format_frame, text="☑ USD (.usdc)",
                                  variable=self.export_usd,
                                  bg=self.colors['bg'], fg=self.colors['text'],
                                  selectcolor=self.colors['entry_bg'],
                                  activebackground=self.colors['bg'], activeforeground=self.colors['text'],
                                  font=('Segoe UI', 10), cursor='hand2')
        usd_check.grid(row=1, column=0, sticky=tk.W, pady=3)

        maya_check = tk.Checkbutton(format_frame, text="☑ Maya USD (.usdc)",
                                    variable=self.export_maya,
                                    bg=self.colors['bg'], fg=self.colors['text'],
                                    selectcolor=self.colors['entry_bg'],
                                    activebackground=self.colors['bg'], activeforeground=self.colors['text'],
                                    font=('Segoe UI', 10), cursor='hand2')
        maya_check.grid(row=2, column=0, sticky=tk.W, pady=3)

        # Convert button (larger and prominent)
        self.convert_btn = tk.Button(main_frame, text="⚡ Convert Multi-Format", command=self.start_conversion,
                                     bg=self.colors['button_bg'], fg=self.colors['button_text'],
                                     activebackground=self.colors['button_hover'], activeforeground=self.colors['button_text'],
                                     relief='flat', borderwidth=0, padx=30, pady=12,
                                     font=('Segoe UI', 12, 'bold'), cursor='hand2')
        self.convert_btn.grid(row=6, column=0, columnspan=2, pady=20)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate', style='Dark.Horizontal.TProgressbar')
        self.progress.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Log text area
        log_frame = ttk.LabelFrame(main_frame, text="Progress Log", padding="5", style='Dark.TLabelframe')
        log_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        self.log_text = tk.Text(log_frame, height=12, width=63, wrap=tk.WORD,
                                bg=self.colors['entry_bg'],
                                fg=self.colors['entry_text'],
                                insertbackground=self.colors['entry_text'],
                                font=('Consolas', 9),
                                relief='flat',
                                borderwidth=0)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def browse_abc(self):
        """Browse for input Alembic file"""
        filename = filedialog.askopenfilename(
            title="Select Alembic File",
            filetypes=[("Alembic Files", "*.abc"), ("All Files", "*.*")]
        )
        if filename:
            self.abc_file.set(filename)
            # Auto-suggest output directory
            if not self.output_dir.get():
                output_path = Path(filename).parent
                self.output_dir.set(str(output_path))
            # Auto-set shot name to ABC filename (without extension)
            abc_name = Path(filename).stem
            self.shot_name.set(abc_name)
            # Auto-detect frame count from ABC file
            try:
                converter = AlembicToJSXConverter()
                detected_frames = converter.detect_frame_count(filename, self.fps.get())
                self.frame_count.set(detected_frames)
                self.log(f"Detected {detected_frames} frames from Alembic file")
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

    def start_conversion(self):
        """Start the conversion process in a separate thread"""
        # Validate inputs
        if not self.abc_file.get():
            messagebox.showerror("Error", "Please select an input Alembic file")
            return

        if not self.output_dir.get():
            messagebox.showerror("Error", "Please specify an output directory")
            return

        if not Path(self.abc_file.get()).exists():
            messagebox.showerror("Error", "Input file does not exist")
            return

        # Check if at least one format is selected
        if not (self.export_ae.get() or self.export_usd.get() or self.export_maya.get()):
            messagebox.showerror("Error", "Please select at least one export format")
            return

        # Clear log
        self.log_text.delete(1.0, tk.END)

        # Disable button and start progress
        self.convert_btn.config(state='disabled', bg=self.colors['accent'])
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
                abc_file=self.abc_file.get(),
                output_dir=self.output_dir.get(),
                shot_name=self.shot_name.get(),
                fps=self.fps.get(),
                frame_count=self.frame_count.get(),
                export_ae=self.export_ae.get(),
                export_usd=self.export_usd.get(),
                export_maya=self.export_maya.get()
            )

            if results.get('success'):
                # Build success message
                message_lines = ["Conversion complete!\n\n"]

                if 'ae' in results and results['ae'].get('success'):
                    ae_dir = Path(results['ae']['jsx_file']).parent
                    message_lines.append(f"✓ After Effects: {ae_dir}")

                if 'usd' in results and results['usd'].get('success'):
                    usd_file = results['usd']['usd_file']
                    message_lines.append(f"✓ USD: {usd_file}")

                if 'maya' in results and results['maya'].get('success'):
                    maya_file = results['maya']['usd_file']
                    message_lines.append(f"✓ Maya: {maya_file}")

                message_lines.append("\nSee Progress Log for details.")

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
        self.convert_btn.config(state='normal', bg=self.colors['button_bg'])


def main():
    root = tk.Tk()
    app = AlembicToJSXGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
