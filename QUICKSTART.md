# Quick Start Guide

## Installation

1. **Install Python 3.8+** (if not already installed)

2. **Install FFmpeg**:
   - Download from https://ffmpeg.org/download.html
   - Add to system PATH, or set environment variables:
     ```bash
     set FFMPEG_BIN=C:\ffmpeg\bin  # Windows
     export FFMPEG_BIN=/usr/local/bin  # Linux/Mac
     ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Tool

### Option 1: GUI Application (Recommended)
```bash
python main.py
```

### Option 2: Direct Module Execution
```bash
python -m geo_inquire_processor.gui
```

## Basic Workflow

1. **Launch the application** - The GUI window will open

2. **Select WAV files**:
   - Click "Select Files" for individual files, or
   - Click "Select Folder" to process all WAV files in a directory

3. **Set time zone offset**:
   - Enter the UTC offset of your files (e.g., `UTC+8`, `UTC-05`)
   - Format: `UTC±HH` where HH is 0-23

4. **Enter metadata**:
   - **EMSO Metadata**: Fill required fields (marked with `*`) or load from file
   - **EIDA Metadata**: Fill all required fields for StationXML
   - Hover over fields for tooltips with guidance

5. **Validate metadata**:
   - Click "Validate StationXML Metadata" button
   - Fix any missing or invalid fields

6. **Process files**:
   - Optionally check "Plot original vs filtered vs downsampled signal"
   - Click "Start Processing"
   - The GUI will close and processing runs in the background
   - Check console output for progress and results

## Output Files

For each input `file.wav`, you'll get:
- `file.flac` - FLAC file with embedded EMSO metadata
- `file.mseed` - MiniSEED file for seismic analysis
- `file.station.xml` - EIDA-compliant StationXML metadata

## Example Metadata Files

### EMSO Metadata (metadata.txt)
```
institution_edmo_code=1234
institution_edmo_uri=https://www.seadatanet.org/urnurl/1234
geospatial_lat_min=28.0
geospatial_lat_max=28.5
geospatial_lon_min=-16.0
geospatial_lon_max=-15.5
geospatial_vertical_min=-20
geospatial_vertical_max=-10
update_interval=P1D
site_code=PLOCAN
title=Ocean Bottom Seismometer Data
summary=Acoustic data from OBS deployment
principal_investigator=Dr. Jane Doe
principal_investigator_email=jane.doe@example.com
license=CC-BY-4.0
license_uri=https://creativecommons.org/licenses/by/4.0/
```

### EIDA StationXML Metadata (stationxml.txt)
```
sender=GEO-INQUIRE Tool, PLOCAN
network_code=X9
network_identifier=urn:network:example:2024
station_code=OBSA1
latitude=28.12345
longitude=-15.67890
elevation=-17
site_name=Plocan OBS Site A
channel_code=CDH
location_code=00
channel_latitude=28.12345
channel_longitude=-15.67890
channel_elevation=-17
channel_depth=17
azimuth=0
dip=-90
sensitivity_value=6.31e-9
sensitivity_frequency=20000
input_units_name=Pa
output_units_name=V
```

## Troubleshooting

### "FFmpeg not found" error
- Ensure FFmpeg is installed and in your PATH
- Or set environment variables (see Installation step 2)

### "No files selected" error
- Make sure you've selected WAV files or a folder containing WAV files
- Check that files have `.wav` or `.WAV` extension

### "Validation failed" error
- Check that all required fields (marked with `*`) are filled
- Verify network code is 1-2 uppercase letters
- Check that numeric fields (lat/lon/elevation) are valid numbers

### Processing errors
- Check console output for detailed error messages
- Ensure WAV files are not corrupted
- Verify file permissions (read access for input, write access for output directory)

## Getting Help

- Check the full [README.md](README.md) for detailed documentation
- Review metadata standards:
  - [EMSO Metadata](https://github.com/emso-eric/emso-metadata-specifications)
  - [FDSN StationXML](https://docs.fdsn.org/projects/stationxml/en/latest/)
- Open an issue on the project repository for bugs or questions

