# GEO-INQUIRE Audio Processing Tool

A professional tool for converting WAV audio files to FLAC and MiniSEED formats with EMSO and EIDA-compliant metadata. Designed for scientific data processing in marine acoustics and seismology.

## Overview

This tool processes WAV audio files to ensure compliance with:
- **EMSO** (European Multidisciplinary Seafloor and Water Column Observatory) standards
- **EIDA** (European Integrated Data Archive) standards
- **FDSN** (International Federation of Digital Seismograph Networks) StationXML format

The tool has been developed in alignment with the requirements of the **GEO-INQUIRE project** and complies with the **Marine Strategy Framework Directive (MSFD)**.

## Features

### Core Functionality

- **Automated Date Extraction**: Intelligently extracts recording start time from WAV filenames using multiple pattern recognition techniques
- **Downsampling**: Normalizes and downsamples audio to 300 Hz (configurable) with proper low-pass filtering to preserve seismic characteristics
- **Format Conversion**: 
  - WAV → FLAC (lossless compression with embedded metadata)
  - FLAC → MiniSEED (standard seismic data format)
- **Metadata Management**:
  - EMSO-compliant metadata embedded in FLAC files
  - EIDA-compliant StationXML files generated automatically
  - UTC offset adjustment for all timestamps
- **Batch Processing**: Process individual files or entire directories
- **Graphical User Interface**: Intuitive GUI with validation and tooltips

### Key Capabilities

- **Smart Date Parsing**: Handles multiple date formats in filenames:
  - `2024-05-17_09-25-33` (explicit separators)
  - `20180726_141241` (compact format)
  - Fuzzy parsing for other formats
- **Signal Processing**: 
  - Normalization
  - FIR low-pass filtering (prevents aliasing)
  - Chunked resampling (handles large files efficiently)
- **Metadata Validation**: 
  - Validates StationXML fields before processing
  - Checks FDSN network code format
  - Provides helpful tooltips and guidance
- **Standards Compliance**:
  - Generates EIDA-compliant StationXML
  - Embeds EMSO metadata in FLAC files
  - Follows FDSN channel code conventions

## Installation

### Prerequisites

1. **Python 3.8 or higher**
2. **FFmpeg** (required for audio conversion)
   - Download from: https://ffmpeg.org/download.html
   - Add to system PATH or set environment variables (see Configuration)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install the package in development mode:

```bash
pip install -e .
```

## Configuration

### FFmpeg Setup

The tool requires FFmpeg for audio format conversion. You can configure it in several ways:

1. **System PATH** (recommended): Install FFmpeg and ensure it's in your system PATH
2. **Environment Variables**:
   ```bash
   # Windows
   set FFMPEG_BIN=C:\ffmpeg\bin
   set FFMPEG_EXE=C:\ffmpeg\bin\ffmpeg.exe
   set FFPROBE_EXE=C:\ffmpeg\bin\ffprobe.exe
   
   # Linux/Mac
   export FFMPEG_BIN=/usr/local/bin
   export FFMPEG_EXE=/usr/local/bin/ffmpeg
   export FFPROBE_EXE=/usr/local/bin/ffprobe
   ```

3. **Auto-detection**: The tool will attempt to find FFmpeg in common installation locations

## Usage

### Graphical Interface

Launch the GUI application:

```bash
python -m geo_inquire_processor.gui
```

Or use the main entry point:

```bash
python -m geo_inquire_processor
```

### Workflow

1. **Select Files**: Choose individual WAV files or a folder containing WAV files
2. **Set Time Zone Offset**: Enter the UTC offset of your files (e.g., `UTC+8`, `UTC-05`)
3. **Enter Metadata**:
   - **EMSO Metadata**: Required fields for FLAC files (can be loaded from file or entered manually)
   - **EIDA Metadata**: Required fields for StationXML (must be validated before processing)
4. **Validate**: Click "Validate StationXML Metadata" to ensure all required fields are present
5. **Process**: Click "Start Processing" to begin conversion

### Command Line Usage (Programmatic)

```python
from geo_inquire_processor import AudioProcessor

processor = AudioProcessor()

# Process files
processor.process_files(
    file_paths=['file1.wav', 'file2.wav'],
    metadata={
        'institution_edmo_code': '1234',
        'site_code': 'PLOCAN',
        # ... other EMSO metadata
    },
    stationxml_data={
        'network_code': 'X9',
        'station_code': 'OBSA1',
        'channel_code': 'CDH',
        # ... other EIDA metadata
    },
    tz_offset=0,
    plot_preference=False
)
```

## Output Files

For each input WAV file, the tool generates:

1. **`.flac`**: FLAC file with embedded EMSO metadata
   - Contains: `time_coverage_start`, `time_coverage_end`, `initial_sampling_rate`, and all EMSO fields
   
2. **`.mseed`**: MiniSEED file for seismic data analysis
   - Compatible with ObsPy, SeisComP, and other seismic software
   
3. **`.station.xml`**: EIDA-compliant StationXML metadata file
   - Contains: Network, Station, Channel information
   - Follows FDSN StationXML 1.1 standard

## Metadata Standards

### EMSO Metadata

The tool embeds EMSO-compliant metadata in FLAC files. Required fields include:
- Institution codes (EDMO)
- Geospatial bounds (latitude, longitude, depth)
- Sensor information (model, manufacturer, sensitivity)
- Data provenance (PI, license, DOI)

See: [EMSO Metadata Specifications](https://github.com/emso-eric/emso-metadata-specifications/blob/develop/EMSO_metadata.md)

### EIDA StationXML

The generated StationXML files follow the FDSN StationXML standard:
- Network, Station, Channel hierarchy
- Instrument response information
- Geographic coordinates
- Time coverage (auto-calculated from filename)

See: [FDSN StationXML Overview](https://docs.fdsn.org/projects/stationxml/en/latest/overview.html)

## Technical Details

### Signal Processing

- **Target Sample Rate**: 300 Hz (configurable via `FINAL_SAMPLING_RATE` in `config.py`)
- **Filtering**: FIR low-pass filter with cutoff at 150 Hz (Nyquist/2)
- **Normalization**: Signal normalized before filtering to prevent clipping
- **Resampling**: Chunked processing for large files (1M samples per chunk)

### Date Extraction

The tool uses a multi-step approach to extract dates from filenames:

1. Pattern matching for explicit formats (`YYYY-MM-DD_HH-MM-SS`)
2. Pattern matching for compact formats (`YYYYMMDD_HHMMSS`)
3. Fuzzy parsing using `dateutil` for other formats
4. Fallback to current UTC time if no date found

### Time Zone Handling

All timestamps are adjusted by the user-specified UTC offset:
- Local time in filename → UTC time in metadata
- Both FLAC and XML metadata use UTC timestamps
- Offset format: `UTC±HH` (e.g., `UTC+8`, `UTC-05`)

## Project Structure

```
geo_inquire_processor/
├── __init__.py          # Package initialization
├── config.py            # Configuration settings
├── processor.py         # Core processing functions
└── gui.py              # Graphical user interface
```

## Dependencies

- **numpy**: Numerical operations
- **scipy**: Signal processing (filtering, resampling)
- **soundfile**: WAV file I/O
- **pydub**: Audio format conversion (requires FFmpeg)
- **mutagen**: FLAC metadata handling
- **obspy**: Seismic data processing and MiniSEED generation
- **lxml**: XML processing and validation
- **plotly**: Signal visualization
- **python-dateutil**: Date parsing

## Troubleshooting

### FFmpeg Not Found

If you see an error about FFmpeg not being found:
1. Install FFmpeg from https://ffmpeg.org/download.html
2. Add to system PATH, or
3. Set environment variables (see Configuration section)

### File Processing Errors

- **Unrealistic sample rate**: Check that your WAV files have valid sample rates (8-400 kHz)
- **File too long**: Files longer than 24 hours are rejected (sanity check)
- **Memory issues**: Large files are processed in chunks, but very large files may require more RAM

### Metadata Validation Errors

- Ensure all required fields (marked with `*`) are filled
- Check that network codes follow FDSN format (1-2 uppercase letters)
- Verify numeric fields (latitudes, longitudes, elevations) are valid numbers

## Contributing

This tool is part of the GEO-INQUIRE project. For contributions or issues, please contact the project maintainers.

## License

[Specify your license here]

## Acknowledgments

- **GEO-INQUIRE Project**: European research infrastructure project
- **EMSO ERIC**: European Multidisciplinary Seafloor and Water Column Observatory
- **EIDA**: European Integrated Data Archive
- **FDSN**: International Federation of Digital Seismograph Networks
- **PLOCAN**: Plataforma Oceánica de Canarias

## References

- [EMSO Metadata Specifications](https://github.com/emso-eric/emso-metadata-specifications)
- [FDSN StationXML Standard](https://docs.fdsn.org/projects/stationxml/en/latest/)
- [ObsPy Documentation](https://docs.obspy.org/)
- [GEO-INQUIRE Project](https://geo-inquire.eu/)

## Author

**Silvana Neves**  
Plataforma Oceánica de Canarias (PLOCAN)

---

For questions or support, please open an issue on the project repository.

