# GEO-INQUIRE-tools
Tools develop to use ocean sound as useful seismic data
<p align="center">
  <img src="Geo-INQUIRE_logo_2_crop.jpg" alt="Geo-INQUIRE Logo" width="400" style="vertical-align: middle"/> 
</p>

# Audio Processing Tool for WAV Files – EMSO & EIDA Compliance
**Author:** Silvana Neves <img src="logo-sin-leyenda-color.jpg"
     alt="PLOCAN Logo"
     width="200"
     style="vertical-align: middle; margin-left: 1px; margin-right: 6px;"  /> 
### Overview

This tool processes WAV audio files to ensure compliance with EMSO (European Multidisciplinary Seafloor and Water Column Observatory) and EIDA (European Integrated Data Archive) standards. It performs downsampling, format conversion, and metadata embedding, thereby standardizing seismic and acoustic data for efficient storage, interoperability, and sharing. The tool has been developed in alignment with the requirements of the GEO-INQUIRE project and complies with the Marine Strategy Framework Directive (MSFD).

### Key Features

- **File Selection and Batch Processing:**  
  The tool allows selection of individual WAV files or entire directories, enabling batch processing of multiple files.

- **Automated Date Extraction:**  
  The recording start time is automatically derived from the WAV filename using robust date parsing techniques. The end time is computed by adding the file's duration to the start time.

- **UTC Offset Adjustment:**  
  A user-specified UTC offset is applied to all metadata timestamps. Both FLAC and XML metadata fields (such as `time_coverage_start` and `time_coverage_end`) are adjusted by subtracting the provided UTC offset.

- **Downsampling and Low-Pass Filtering:**  
  Audio data is normalized and downsampled to 300 Hz. This target sample rate is chosen to balance the need for adequate frequency resolution for seismic events with the objective of reducing data size, thereby satisfying MSFD requirements. A low-pass FIR filter and interpolation are used to ensure accurate resampling without introducing artifacts.

- **Conversion to FLAC with Embedded Metadata:**  
  The downsampled audio is converted to FLAC format, providing lossless compression. EMSO-compliant metadata—including automatically computed timestamps (adjusted for the UTC offset) and instrument parameters—is embedded within the FLAC files. For further details on EMSO metadata specifications, please refer to the [EMSO Metadata Specifications](https://github.com/emso-eric/emso-metadata-specifications/blob/develop/EMSO_metadata.md).

- **Conversion to MiniSEED:**  
  The FLAC files are converted to MiniSEED format, ensuring compatibility with seismic data repositories and analysis tools.

- **Generation of EIDA-Compliant XML:**  
  An XML metadata file is generated for each WAV file. This XML adheres to the EIDA standard as defined in the [FDSN StationXML Overview](https://docs.fdsn.org/projects/stationxml/en/latest/overview.html) and includes:
  - Automatically derived start and end times (computed from the filename and duration, then adjusted by the UTC offset).
  - All required metadata fields provided via the GUI. 
  - Computation of related end dates (for channel, station, and network) by adding the duration to the start time.

- **Metadata Editors:**  
  Following processing, two metadata viewers are provided:
  - **FLAC Metadata Viewer:** For examining and modifying the embedded metadata in the FLAC files.
  - **XML Metadata Viewer:** For inspecting and editing the generated XML metadata.
  
  These editors facilitate reviewing and updating metadata fields as necessary.

- **Compliance with GEO-INQUIRE and MSFD:**  
  The tool meets the GEO-INQUIRE project requirements and is designed to process acoustic data in compliance with both EMSO and EIDA standards. Downsampling to 300 Hz is based on balancing the need for sufficient frequency resolution for seismic events and the reduction of file size, in line with MSFD specifications.

- **Graphical User Interface (GUI) and Workflow:**  
  A Tkinter-based interface guides operators through:
  - Selection of files or directories.
  - Input or import of EMSO and EIDA metadata.
  - Specification of the UTC offset.
  - Visualization of the original versus downsampled signal.
 

### Detailed Workflow

1. **File Selection:**  
   The operator selects one or more WAV files (or a folder) via the interface; the selected files are then displayed for confirmation.

2. **Metadata Input:**  
   - **EMSO Metadata:** Input may be provided manually or imported from a preformatted text file.  
   - **EIDA Metadata:** Input may be provided manually or imported from a preformatted text file. 

3. **Signal Processing:**  
   The audio is normalized, low-pass filtered, and resampled to 300 Hz. This ensures that the essential characteristics of the signal are maintained while reducing data size.

4. **Format Conversion and Metadata Embedding:**  
   The processed signal is converted to FLAC with embedded EMSO metadata and then to MiniSEED. XML metadata is generated based on the computed start and end times, with all timestamps adjusted by the UTC offset.

5. **Execution:**  
   Processing is initiated via the GUI, which then launches the task in a background thread and closes immediately.

6. **Metadata Editors:**  
   Post-processing, metadata viewers are available for both FLAC and XML outputs, allowing the operator to inspect, add, and modify metadata fields.

 
### Methodology for GEO-INQUIRE Project

The tool aligns with the GEO-INQUIRE project’s requirements (task 2.4), ensuring that processed acoustic data is compliant with both EMSO and EIDA standards. The methodology involves downsampling data, converting it to FLAC for storage, embedding necessary metadata, and generating MiniSEED and XML files for standardization and sharing.

