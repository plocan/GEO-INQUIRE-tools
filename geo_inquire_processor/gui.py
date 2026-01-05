"""
Graphical User Interface for the GEO-INQUIRE Audio Processing Tool.
"""

import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Toplevel, Label
from datetime import timedelta
import webbrowser

from .processor import AudioProcessor, extract_times_from_wav, FINAL_SAMPLING_RATE


# StationXML field tooltips
STATIONXML_TOOLTIPS = {
    "sender": "Name of the person or organization creating this metadata (e.g., 'Geo-INQUIRE Tool, PLOCAN').",
    "source": "Project or data source description (e.g., 'OBS campaign 2024').",
    "module": "Optional. Software module or script used to create this metadata.",
    "network_code": "2-character FDSN code. Must be registered (e.g., 'X9').",
    "network_description": "Description of the network's purpose or setup.",
    "network_identifier": "Globally unique identifier for this network. Use DOI or URL.",
    "station_code": "Station code (up to 5 characters, e.g., 'OBSA1'). Unique within network.",
    "station_description": "Description of station location and deployment.",
    "latitude": "Station latitude in decimal degrees (e.g., 28.12345).",
    "longitude": "Station longitude in decimal degrees (e.g., -15.67890).",
    "elevation": "Meters above sea level. Use negative for seafloor (e.g., -17).",
    "site_name": "Name of the site (e.g., 'Plocan Node A').",
    "channel_code": "FDSN 3-char code (e.g., CDH). Band + Instrument + Orientation.",
    "location_code": "Usually '00'. Use if you have multiple sensors.",
    "channel_latitude": "Sensor latitude. Often same as station latitude.",
    "channel_longitude": "Sensor longitude. Often same as station longitude.",
    "channel_elevation": "Sensor elevation (above sea level). Often same as station.",
    "channel_depth": "Depth from surface to sensor in meters. Positive value (e.g., 17 = 17m below sea).",
    "azimuth": "Azimuth in degrees from North (0 = N, 90 = E). Use 0 for omnidirectional sensors.",
    "dip": "Inclination angle. -90 = downward (hydrophone), +90 = upward.",
    "sensor_description": "Free text. Include model, mounting, orientation.",
    "sensitivity_value": "Linear value in V/Pa (not in dB).",
    "sensitivity_frequency": "Frequency (Hz) where sensitivity was measured (e.g., 20000).",
    "input_units_name": "Use 'Pa' for hydrophones (SI unit).",
    "output_units_name": "Use 'V' (Volts) or 'count'. Avoid non-SI."
}


def create_tooltip(widget, text):
    """Create a tooltip for a widget."""
    def on_enter(event):
        top = Toplevel(widget)
        top.wm_overrideredirect(True)
        top.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
        label = Label(top, text=text, background="light yellow", relief="solid", borderwidth=1,
                      wraplength=400, justify="left")
        label.pack(ipadx=1)
        widget.tooltip = top

    def on_leave(event):
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
            del widget.tooltip

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)


class Application(tk.Tk):
    """Main application window for the GEO-INQUIRE Audio Processing Tool."""
    
    def __init__(self):
        super().__init__()
        self.processor = AudioProcessor()
        self.file_paths = []
        self.stationxml_validated = False
        
        self.geometry("1800x800")
        self.title("GEO-INQUIRE Audio Processing Tool - WAV to FLAC/MiniSEED Converter")
        self.attributes('-topmost', True)
        
        # Main frame with scrolling
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True)
        main_canvas = tk.Canvas(main_frame)
        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar_y = ttk.Scrollbar(main_frame, orient="vertical", command=main_canvas.yview)
        main_scrollbar_y.pack(side="right", fill="y")
        main_scrollbar_x = ttk.Scrollbar(main_frame, orient="horizontal", command=main_canvas.xview)
        main_scrollbar_x.pack(side="bottom", fill="x")
        main_canvas.configure(yscrollcommand=main_scrollbar_y.set, xscrollcommand=main_scrollbar_x.set)
        main_canvas.bind('<Configure>', lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        
        def _on_mousewheel(event):
            main_canvas.yview_scroll(-1 * int(event.delta/120), "units")
        main_canvas.bind("<Enter>", lambda e: main_canvas.bind_all("<MouseWheel>", _on_mousewheel))
        main_canvas.bind("<Leave>", lambda e: main_canvas.unbind_all("<MouseWheel>"))
        
        self.scroll_frame = ttk.Frame(main_canvas)
        main_canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all GUI widgets."""
        # Description
        self.description_label = tk.Label(
            self.scroll_frame,
            text=(
                "This tool converts WAV audio files to FLAC and MiniSEED, using a 300 Hz downsampling rate to preserve seismic features.\n"
                "It extracts start/end times from filenames and adds EIDA-compliant XML metadata based on user input.\n"
                "EMSO and EIDA metadata editors are built in — start manually or load a metadata file.\n"
                "✔ Channel codes are auto-suggested for hydrophones.\n"
                "✔ Input validation ensures metadata is complete and standards-compliant.\n"
                "ℹ️ Click the 'Validate' button or hover over fields for guidance."
            ),
            font=("Arial", 12),
            fg="dark green",
            wraplength=1600,
            justify="left"
        )
        self.description_label.pack(pady=10)
        
        # File selection
        self.selection_label = ttk.Label(self.scroll_frame, text="Select files or a folder:")
        self.selection_label.pack(pady=5)
        
        self.file_button = ttk.Button(self.scroll_frame, text="Select Files", command=self.select_files)
        self.file_button.pack(pady=5)
        
        self.folder_button = ttk.Button(self.scroll_frame, text="Select Folder", command=self.select_folder)
        self.folder_button.pack(pady=5)
        
        self.path_label = ttk.Label(self.scroll_frame, text="", wraplength=1100)
        self.path_label.pack(pady=5)
        
        # Time zone offset
        self.tz_frame = ttk.Frame(self.scroll_frame)
        self.tz_frame.pack(pady=5, fill='x')
        
        tz_label = ttk.Label(self.tz_frame, text="Time Zone Offset of the Files:")
        tz_label.pack(side='left', padx=5)
        
        self.tz_offset_entry = ttk.Entry(self.tz_frame, width=20)
        self.tz_offset_entry.insert(0, "UTC+0")
        self.tz_offset_entry.pack(side='left', padx=5)
        
        tz_instruction = ttk.Label(
            self.tz_frame,
            text="Enter the time zone offset in hours (e.g., UTC+8, UTC-05, UTC+10). Must be between -24 and +24."
        )
        tz_instruction.pack(side='left', padx=5)
        
        # Metadata frame
        self.metadata_frame = ttk.Frame(self.scroll_frame)
        self.metadata_frame.pack(fill='x', pady=10)
        
        # EMSO Metadata Section
        self._create_emso_section()
        
        # EIDA Metadata Section
        self._create_eida_section()
        
        # Plotting checkbox
        self.plot_var = tk.BooleanVar()
        self.plot_check = ttk.Checkbutton(
            self.scroll_frame,
            text="Plot original vs filtered vs downsampled signal (only for the first file)",
            variable=self.plot_var
        )
        self.plot_check.pack(pady=5)
        
        # Start processing button
        self.start_button = ttk.Button(
            self.scroll_frame,
            text="Start Processing",
            command=self.start_processing
        )
        self.start_button.pack(pady=20)
        
        # Status label
        self.status_label = ttk.Label(
            self.scroll_frame,
            text="Status: Ready",
            foreground="green",
            font=("Arial", 10, "bold")
        )
        self.status_label.pack(pady=5)
    
    def _create_emso_section(self):
        """Create EMSO metadata input section."""
        self.emso_label_frame = ttk.LabelFrame(self.metadata_frame, text="EMSO FLAC Metadata")
        self.emso_label_frame.grid(row=0, column=0, padx=10, sticky="n")
        
        self.emso_metadata_choice = tk.StringVar(value="")
        
        self.emso_file_radio = ttk.Radiobutton(
            self.emso_label_frame, text="Load from file", variable=self.emso_metadata_choice,
            value="file", command=self.select_metadata_file
        )
        self.emso_file_radio.pack(side='top', padx=20)
        
        self.emso_manual_radio = ttk.Radiobutton(
            self.emso_label_frame, text="Enter manually", variable=self.emso_metadata_choice,
            value="manual", command=self.update_metadata_input
        )
        self.emso_manual_radio.pack(side='top', padx=20)
        
        emso_info_label = ttk.Label(
            self.emso_label_frame,
            text=("Metadata guidance available. Fields marked with * are mandatory.\n"
                  "Standard defined by EMSO: click here to view →"),
            foreground="blue",
            cursor="hand2",
            font=("Arial", 10, "italic")
        )
        emso_info_label.pack(pady=3)
        emso_info_label.bind("<Button-1>", lambda e: webbrowser.open(
            "https://github.com/emso-eric/emso-metadata-specifications/blob/develop/EMSO_metadata.md"
        ))
        
        emso_canvas = tk.Canvas(self.emso_label_frame, width=750, height=400)
        emso_canvas.pack(side="left", fill="both", expand=True)
        emso_scrollbar = ttk.Scrollbar(self.emso_label_frame, orient="vertical", command=emso_canvas.yview)
        emso_scrollbar.pack(side="right", fill="y")
        emso_canvas.configure(yscrollcommand=emso_scrollbar.set)
        emso_canvas.bind('<Configure>', lambda e: emso_canvas.configure(scrollregion=emso_canvas.bbox("all")))
        
        self.emso_scroll_frame = ttk.Frame(emso_canvas)
        emso_canvas.create_window((0, 0), window=self.emso_scroll_frame, anchor="nw")
        
        emso_fields = [
            "Conventions", "institution_edmo_code*", "institution_edmo_uri*",
            "geospatial_lat_min*", "geospatial_lat_max*", "geospatial_lon_min*", "geospatial_lon_max*",
            "geospatial_vertical_min*", "geospatial_vertical_max*",
            "update_interval*", "site_code*", "emso_facility", "source", "platform_code", "wmo_platform_code",
            "data_type", "format_version", "network*", "data_mode", "title*", "summary*", "keywords",
            "keywords_vocabulary", "project", "principal_investigator*", "principal_investigator_email*", "doi",
            "license*", "license_uri*", "$name*", "long_name*", "standard_name*", "units*", "comment",
            "coordinates", "ancillary_variables", "_FillValue", "sdn_parameter_name*",
            "sdn_parameter_urn*", "sdn_parameter_uri", "sdn_uom_name*", "sdn_uom_urn*", "sdn_uom_uri",
            "sensor_model*", "sensor_SeaVoX_L22_code*", "sensor_reference*", "sensor_manufacturer*",
            "sensor_manufacturer_uri*", "sensor_manufacturer_urn*", "sensor_serial_number*", "sensor_mount*",
            "sensor_orientation*", "hydrophone_sensitivity*", "nbits*"
        ]
        
        self.metadata_entries = {}
        for label in emso_fields:
            frame = ttk.Frame(self.emso_scroll_frame)
            frame.pack(fill='x', pady=1)
            label_clean = label.replace('*', '')
            display_label = f"{label_clean} *" if '*' in label else label_clean
            ttk.Label(frame, text=display_label, width=40, anchor='w').pack(side='left')
            entry = ttk.Entry(frame, width=80)
            entry.pack(side='left', pady=1)
            self.metadata_entries[label_clean] = entry
        
        auto_time_label_emso = ttk.Label(
            self.emso_scroll_frame,
            text="Note: Start/End Times and Initial Sampling Rate are extracted automatically.",
            foreground="blue",
            font=("Arial", 9, "italic")
        )
        auto_time_label_emso.pack(pady=4, anchor='w')
    
    def _create_eida_section(self):
        """Create EIDA StationXML metadata input section."""
        self.eida_label_frame = ttk.LabelFrame(self.metadata_frame, text="XML EIDA Metadata Requirements")
        self.eida_label_frame.grid(row=0, column=1, padx=10, sticky="n")
        
        # Reference buttons
        rules_button = ttk.Button(
            self.eida_label_frame,
            text="📘 View StationXML Field Rules",
            command=lambda: webbrowser.open("https://docs.fdsn.org/projects/stationxml/en/latest/reference.html")
        )
        rules_button.pack(pady=4)
        
        self.source_ids_button = ttk.Button(
            self.eida_label_frame,
            text="Open FDSN Source Identifiers Reference",
            command=lambda: webbrowser.open("https://docs.fdsn.org/projects/source-identifiers/en/v1.0/index.html")
        )
        self.source_ids_button.pack(pady=4)
        
        self.validate_xml_button = ttk.Button(
            self.eida_label_frame,
            text="Validate StationXML Metadata",
            command=self.validate_stationxml_metadata
        )
        self.validate_xml_button.pack(pady=4)
        
        # Radio buttons
        self.xml_metadata_choice = tk.StringVar(value="")
        
        self.xml_file_radio = ttk.Radiobutton(
            self.eida_label_frame, text="Load from file", variable=self.xml_metadata_choice,
            value="file", command=self.select_stationxml_file
        )
        self.xml_file_radio.pack(pady=2)
        
        self.xml_manual_radio = ttk.Radiobutton(
            self.eida_label_frame, text="Enter manually", variable=self.xml_metadata_choice,
            value="manual", command=self.update_stationxml_input
        )
        self.xml_manual_radio.pack(pady=2)
        
        # Canvas and scrollable frame
        eida_canvas = tk.Canvas(self.eida_label_frame, width=750, height=400)
        eida_canvas.pack(side="left", fill="both", expand=True)
        eida_scrollbar = ttk.Scrollbar(self.eida_label_frame, orient="vertical", command=eida_canvas.yview)
        eida_scrollbar.pack(side="right", fill="y")
        eida_canvas.configure(yscrollcommand=eida_scrollbar.set)
        eida_canvas.bind('<Configure>', lambda e: eida_canvas.configure(scrollregion=eida_canvas.bbox("all")))
        
        self.eida_scroll_frame = ttk.Frame(eida_canvas)
        eida_canvas.create_window((0, 0), window=self.eida_scroll_frame, anchor="nw")
        
        # Field definitions
        eida_fields = {
            "sender": "Sender*",
            "source": "Source",
            "module": "Module",
            "network_code": "Network Code*",
            "network_description": "Network Description",
            "network_identifier": "Network Identifier*",
            "station_code": "Station Code*",
            "station_description": "Station Description",
            "latitude": "Latitude (Degrees)*",
            "longitude": "Longitude (Degrees)*",
            "elevation": "Elevation (Meters)*",
            "site_name": "Site Name*",
            "channel_code": "Channel Code*",
            "location_code": "Location Code",
            "channel_latitude": "Channel Latitude (Degrees)*",
            "channel_longitude": "Channel Longitude (Degrees)*",
            "channel_elevation": "Channel Elevation (Meters)*",
            "channel_depth": "Channel Depth (Meters)*",
            "azimuth": "Azimuth*",
            "dip": "Dip*",
            "sensor_description": "Sensor Description",
            "sensitivity_value": "Instrument Sensitivity Value*",
            "sensitivity_frequency": "Instrument Sensitivity Frequency*",
            "input_units_name": "Input Units Name*",
            "output_units_name": "Output Units Name*"
        }
        
        self.stationxml_entries = {}
        for key, label in eida_fields.items():
            frame = ttk.Frame(self.eida_scroll_frame)
            frame.pack(fill='x', pady=2)
            
            ttk.Label(frame, text=label, width=40, anchor='w').pack(side='left')
            
            entry = ttk.Entry(frame, width=100)
            entry.pack(side='left', pady=2)
            self.stationxml_entries[key] = entry
            
            if key in STATIONXML_TOOLTIPS:
                create_tooltip(entry, STATIONXML_TOOLTIPS[key])
        
        auto_time_label_xml = ttk.Label(
            self.eida_scroll_frame,
            text=f"Note: Start/End Dates are auto-calculated. Final Sampling Rate = {FINAL_SAMPLING_RATE} Hz.",
            foreground="blue",
            font=("Arial", 9, "italic")
        )
        auto_time_label_xml.pack(pady=4, anchor='w')
    
    def select_files(self):
        """Select individual WAV files."""
        self.file_paths = filedialog.askopenfilenames(
            title="Select WAV files",
            filetypes=[("WAV files", "*.wav"), ("WAV files", "*.WAV")]
        )
        if self.file_paths:
            self.path_label.config(text=f"Selected files: {', '.join(self.file_paths)}")
    
    def select_folder(self):
        """Select a folder containing WAV files."""
        folder_path = filedialog.askdirectory(title="Select Folder of WAV files")
        if folder_path:
            self.file_paths = [
                os.path.join(folder_path, f) 
                for f in os.listdir(folder_path) 
                if f.lower().endswith('.wav')
            ]
            self.path_label.config(text=f"Selected folder: {folder_path} ({len(self.file_paths)} files)")
    
    def select_metadata_file(self):
        """Load EMSO metadata from a text file."""
        metadata_file = filedialog.askopenfilename(
            title="Select Metadata File", 
            filetypes=[("Text files", "*.txt")]
        )
        if metadata_file:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = {
                    line.strip().split('=', 1)[0].strip(): line.strip().split('=', 1)[1].strip()
                    for line in f if '=' in line
                }
            self.populate_metadata_fields(metadata)
    
    def select_stationxml_file(self):
        """Load StationXML metadata from a text file."""
        metadata_file = filedialog.askopenfilename(
            title="Select XML Metadata File", 
            filetypes=[("Text files", "*.txt")]
        )
        if metadata_file:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = {
                    line.strip().split('=', 1)[0].strip(): line.strip().split('=', 1)[1].strip()
                    for line in f if '=' in line
                }
            self.populate_stationxml_fields(metadata)
            self.validate_stationxml_metadata()
    
    def populate_metadata_fields(self, metadata):
        """Populate EMSO metadata fields from dictionary."""
        for key, entry in self.metadata_entries.items():
            if key in metadata:
                entry.delete(0, tk.END)
                entry.insert(0, metadata[key])
    
    def populate_stationxml_fields(self, metadata):
        """Populate StationXML metadata fields from dictionary."""
        for key, entry in self.stationxml_entries.items():
            if key in metadata:
                entry.delete(0, tk.END)
                entry.insert(0, metadata[key])
    
    def update_metadata_input(self):
        """Enable/disable EMSO metadata fields based on input method."""
        state = tk.NORMAL if self.emso_metadata_choice.get() == "manual" else tk.DISABLED
        for entry in self.metadata_entries.values():
            entry.config(state=state)
    
    def update_stationxml_input(self):
        """Enable/disable StationXML metadata fields based on input method."""
        state = tk.NORMAL if self.xml_metadata_choice.get() == "manual" else tk.DISABLED
        for entry in self.stationxml_entries.values():
            entry.config(state=state)
    
    def get_metadata(self):
        """Get EMSO metadata from GUI fields."""
        metadata = {}
        for key, entry in self.metadata_entries.items():
            value = entry.get().strip()
            if value:
                metadata[key] = value
        return metadata
    
    def get_stationxml_data(self):
        """Get StationXML metadata from GUI fields."""
        stationxml_data = {}
        for key, entry in self.stationxml_entries.items():
            stationxml_data[key] = entry.get().strip()
        return stationxml_data
    
    def validate_stationxml_metadata(self):
        """Validate StationXML metadata fields."""
        missing_fields = []
        for key, entry in self.stationxml_entries.items():
            if not entry.get().strip():
                missing_fields.append(key)
            
            if key == "network_code":
                entered_code = entry.get().strip()
                if len(entered_code) != 2:
                    messagebox.showwarning(
                        "Network Code Warning",
                        "Network code should be a 2-letter code officially registered in the FDSN registry.\n"
                        "See: https://www.fdsn.org/networks/"
                    )
        
        if missing_fields:
            messagebox.showerror(
                "Validation Error", 
                f"The following StationXML fields are missing: {', '.join(missing_fields)}"
            )
            self.status_label.config(text="Status: StationXML metadata validation failed.", foreground="red")
            self.stationxml_validated = False
        else:
            messagebox.showinfo("Validation Success", "StationXML metadata validated successfully.")
            self.status_label.config(text="Status: StationXML metadata validated successfully.", foreground="green")
            self.stationxml_validated = True
            
            # Check network code format
            network_code = self.stationxml_entries.get("network_code").get().strip()
            if not re.match(r'^[A-Z]{1,2}$', network_code):
                messagebox.showwarning(
                    "Non-Standard Network Code",
                    "⚠️ The 'network_code' you entered does not match the standard FDSN 1–2 character uppercase format.\n"
                    "If this is not an official FDSN code, validation with EIDA tools may fail.\n\n"
                    "🧭 You can check official codes here:\nhttps://www.fdsn.org/networks/"
                )
    
    def start_processing(self):
        """Start processing files."""
        if not hasattr(self, 'file_paths') or not self.file_paths:
            messagebox.showerror("Error", "No files or folder selected.")
            return
        
        if not self.stationxml_validated:
            messagebox.showerror("Error", "Please validate StationXML metadata before processing.")
            return
        
        try:
            # Parse time zone offset
            tz_str = self.tz_offset_entry.get().strip().upper()
            pattern = r'^UTC([+-])(\d{1,2})$'
            m = re.match(pattern, tz_str)
            if not m:
                raise ValueError("Time zone offset must be in the format: UTC±X or UTC±XX (e.g., UTC+8, UTC-05, UTC+10).")
            sign, digits = m.groups()
            tz_offset = int(digits) if sign == '+' else -int(digits)
            if abs(tz_offset) >= 24:
                raise ValueError("Time zone offset (in hours) must be between -24 and +24.")
            
            # Get metadata
            metadata = self.get_metadata()
            stationxml_data = self.get_stationxml_data()
            
            # Extract times from first file for preview
            local_start_time, local_end_time = extract_times_from_wav(self.file_paths[0])
            utc_start_time = local_start_time - timedelta(hours=tz_offset)
            utc_end_time = local_end_time - timedelta(hours=tz_offset)
            utc_start_str = utc_start_time.isoformat()
            utc_end_str = utc_end_time.isoformat()
            
            metadata['time_coverage_start'] = utc_start_str
            metadata['time_coverage_end'] = utc_end_str
            stationxml_data['time_coverage_start'] = utc_start_str
            stationxml_data['time_coverage_end'] = utc_end_str
            
            # Start processing in background thread
            threading.Thread(
                target=self.processor.process_files,
                args=(self.file_paths, metadata, stationxml_data, tz_offset, self.plot_var.get())
            ).start()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Processing Error", str(e))
            self.status_label.config(text=f"Status: Error during processing: {e}", foreground="red")

