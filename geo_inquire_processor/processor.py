"""
Core audio processing functions for WAV to FLAC/MiniSEED conversion.
"""

import os
import re
import tempfile
from datetime import datetime, timedelta

import numpy as np
import soundfile as sf
from scipy.signal import firwin, lfilter, resample
from pydub import AudioSegment
from mutagen.flac import FLAC
import obspy
from obspy.core import UTCDateTime
from obspy.core.inventory import (
    Inventory, Network, Station, Channel, Response, InstrumentSensitivity, Site
)
import plotly.graph_objects as go
from dateutil import parser
from lxml import etree

from .config import FINAL_SAMPLING_RATE, setup_ffmpeg


def extract_datetime_from_filename(filename):
    """
    Automatically extracts a datetime from the filename.
    
    1. First, tries to match a full datetime with explicit separators, e.g.:
       "2024-05-17_09-25-33" → returns a datetime with date and time.
    2. If that fails, it tries to match a compact format like "20180726_141241".
    3. Otherwise, it falls back to fuzzy parsing of the entire filename.
    
    The returned datetime is naive (tzinfo removed).
    """
    # Remove file extension
    name = re.sub(r'\.\w+$', '', filename)
    
    # 1. Try full datetime with explicit separators: e.g. "2024-05-17_09-25-33"
    pattern_full = r'(\d{4}[-]\d{2}[-]\d{2})[ _](\d{2}[-]\d{2}[-]\d{2})'
    match = re.search(pattern_full, name)
    if match:
        try:
            date_part = match.group(1)
            time_part = match.group(2).replace('-', ':')
            dt_str = f"{date_part} {time_part}"
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            return dt
        except Exception:
            pass

    # 2. Try compact datetime: e.g. "20180726_141241"
    pattern_compact = r'(\d{8})[ _](\d{6})'
    match = re.search(pattern_compact, name)
    if match:
        try:
            date_part = match.group(1)
            time_part = match.group(2)
            dt_str = f"{date_part} {time_part}"
            dt = datetime.strptime(dt_str, "%Y%m%d %H%M%S")
            return dt
        except Exception:
            pass

    # 3. Fallback: fuzzy parse entire filename
    try:
        dt = parser.parse(name, fuzzy=True)
        return dt.replace(tzinfo=None)
    except Exception:
        return datetime.utcnow()


def generate_start_end_time(wav_file_name, duration_seconds):
    """
    Extracts the start time from the WAV filename using the AI-powered extraction.
    If no valid timestamp is found, uses the current UTC time.
    Computes the end time as start time plus the file's duration.
    Returns start and end times in ISO format.
    """
    dt = extract_datetime_from_filename(wav_file_name)
    start_time = UTCDateTime(dt.isoformat())
    end_time = start_time + duration_seconds
    return start_time.isoformat(), end_time.isoformat()


def plot_signals(original_signal, filtered_signal, downsampled_signal, original_rate, target_rate):
    """Plot comparison of original, filtered, and downsampled signals."""
    original_samples_to_plot = original_rate
    downsampled_samples_to_plot = target_rate

    original_signal_norm = (original_signal / np.max(np.abs(original_signal))
                              if np.max(np.abs(original_signal)) != 0 else original_signal)
    filtered_signal_norm = (filtered_signal / np.max(np.abs(filtered_signal))
                            if np.max(np.abs(filtered_signal)) != 0 else filtered_signal)
    downsampled_signal_norm = (downsampled_signal / np.max(np.abs(downsampled_signal))
                               if np.max(np.abs(downsampled_signal)) != 0 else downsampled_signal)

    t_original = np.linspace(0, 1, original_samples_to_plot, endpoint=False)
    t_filtered = np.linspace(0, 1, original_samples_to_plot, endpoint=False)
    t_downsampled = np.linspace(0, 1, downsampled_samples_to_plot, endpoint=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t_original, y=original_signal_norm[:original_samples_to_plot],
                             mode='lines', name='Original Signal'))
    fig.add_trace(go.Scatter(x=t_filtered, y=filtered_signal_norm[:original_samples_to_plot],
                             mode='lines', name='Filtered Signal'))
    fig.add_trace(go.Scatter(x=t_downsampled, y=downsampled_signal_norm[:downsampled_samples_to_plot],
                             mode='lines+markers', name=f'Downsampled Signal ({FINAL_SAMPLING_RATE} Hz)',
                             marker=dict(color='gold')))
    for i in range(downsampled_samples_to_plot):
        filtered_index = int(i * (original_rate / target_rate))
        fig.add_trace(go.Scatter(x=[t_downsampled[i], t_filtered[filtered_index]],
                                 y=[downsampled_signal_norm[i], filtered_signal_norm[filtered_index]],
                                 mode='lines', line=dict(color='green', dash='dash'),
                                 showlegend=False))
    fig.update_layout(
        title='First Second of the first file: Signal Downsampling and Interpolation',
        xaxis_title='Time [s]',
        yaxis_title='Amplitude',
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        template="plotly_white"
    )
    fig.show()


def convert_wav_to_flac(wav_file_path, flac_file_path):
    """Convert WAV file to FLAC format."""
    audio = AudioSegment.from_file(wav_file_path, format="wav")
    audio.export(flac_file_path, format="flac")


def add_metadata_to_flac(flac_file_path, metadata):
    """
    Adds metadata to the FLAC file.
    Includes per-file timestamps (time_coverage_start, time_coverage_end)
    and the initial sampling rate.
    """
    audio = FLAC(flac_file_path)
    metadata["date_created"] = datetime.utcnow().isoformat()  # Always in UTC
    for key, value in metadata.items():
        audio[key] = str(value)
    audio.save()


def get_wav_info(file_path):
    """Read WAV file and return sample rate and data."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    data, rate = sf.read(file_path)
    if not (8000 <= rate <= 400000):
        raise ValueError(f"Unrealistic sample rate {rate} detected in file {file_path}.")
    return rate, data


def downsample_wav(data, original_rate, target_rate=FINAL_SAMPLING_RATE):
    """
    Downsample audio data with low-pass filtering.
    Returns (downsampled_data, filtered_data).
    """
    if original_rate == target_rate:
        return data, data
    
    # Normalize
    max_val = np.max(np.abs(data))
    if max_val == 0:
        max_val = 1
    data = data / max_val
    
    # Design low-pass FIR filter
    cutoff = min(150, 0.5 * target_rate)
    numtaps = 101
    fir_filter = firwin(numtaps, cutoff / (0.5 * original_rate))
    filtered_data = lfilter(fir_filter, 1.0, data)
    
    # Downsample in chunks to avoid memory issues
    chunk_size = 1000000
    chunks = []
    for i in range(0, len(filtered_data), chunk_size):
        chunk = filtered_data[i:i + chunk_size]
        chunk_downsampled = resample(chunk, int(len(chunk) * (target_rate / original_rate)))
        chunks.append(chunk_downsampled)
    
    downsampled_data = np.concatenate(chunks)
    downsampled_data = downsampled_data * np.iinfo(np.int16).max
    downsampled_data = downsampled_data.astype(np.int16)
    return downsampled_data, filtered_data


def convert_data_format(data):
    """Convert data to int16 format."""
    if data.dtype != np.int16:
        data = (data * np.iinfo(np.int16).max).astype(np.int16)
    return data


def extract_times_from_wav(file_path):
    """
    Extract start and end times from WAV filename.
    Returns (start_time, end_time) as UTCDateTime objects.
    """
    base_name = os.path.basename(file_path)
    rate, data = get_wav_info(file_path)
    duration = len(data) / rate
    if duration > 86400:
        raise ValueError(f"File {file_path} has an implausibly long duration ({duration} seconds).")
    start_iso, end_iso = generate_start_end_time(base_name, duration)
    start_time = UTCDateTime(start_iso)
    end_time = UTCDateTime(end_iso)
    return start_time, end_time


def flac_to_miniseed(flac_file_path, output_path):
    """Convert FLAC file to MiniSEED format."""
    try:
        flac_meta = FLAC(flac_file_path)
        if 'time_coverage_start' in flac_meta:
            start_time = UTCDateTime(flac_meta['time_coverage_start'][0])
        elif 'date_created' in flac_meta:
            start_time = UTCDateTime(flac_meta['date_created'][0])
        else:
            start_time = UTCDateTime()
    except Exception:
        start_time = UTCDateTime()
    
    flac_audio = AudioSegment.from_file(flac_file_path, format="flac")
    samples = np.array(flac_audio.get_array_of_samples())
    stream = obspy.Stream()
    trace = obspy.Trace(data=samples)
    trace.stats.sampling_rate = flac_audio.frame_rate
    trace.stats.starttime = start_time
    stream.append(trace)
    stream.write(output_path, format='MSEED')


def generate_stationxml_obspy(wav_file_name, stationxml_data, duration_seconds, tz_offset):
    """
    Generate EIDA-compliant StationXML file.
    Returns the path to the generated XML file.
    """
    # Compute start/end with offset
    start_iso, end_iso = generate_start_end_time(wav_file_name, duration_seconds)
    start_time = UTCDateTime(start_iso) - timedelta(hours=tz_offset)
    end_time = UTCDateTime(end_iso) - timedelta(hours=tz_offset)

    # Gather GUI fields
    sender = stationxml_data.get("sender", "")
    source = stationxml_data.get("source", "")
    net_id = stationxml_data.get("network_identifier", "")
    network_identifier = (
        net_id if net_id.startswith(("http://", "https://"))
        else f"urn:network_identifier:{net_id}"
    )

    # Build Channel, Station, Network via ObsPy
    channel = Channel(
        code=stationxml_data.get("channel_code", ""),
        location_code=stationxml_data.get("location_code", ""),
        latitude=float(stationxml_data.get("channel_latitude", "0")),
        longitude=float(stationxml_data.get("channel_longitude", "0")),
        elevation=float(stationxml_data.get("channel_elevation", "0")),
        depth=float(stationxml_data.get("channel_depth", "0")),
        azimuth=float(stationxml_data.get("azimuth", "0")),
        dip=float(stationxml_data.get("dip", "0")),
        sample_rate=FINAL_SAMPLING_RATE,
        start_date=start_time,
        end_date=end_time,
        response=Response(instrument_sensitivity=InstrumentSensitivity(
            value=float(stationxml_data.get("sensitivity_value", "0")),
            frequency=float(stationxml_data.get("sensitivity_frequency", "0")),
            input_units=stationxml_data.get("input_units_name", ""),
            output_units=stationxml_data.get("output_units_name", "")
        ))
    )
    if stationxml_data.get("sensor_description"):
        channel.description = stationxml_data["sensor_description"]

    site = Site(name=stationxml_data.get("site_name", ""))
    station = Station(
        code=stationxml_data.get("station_code", ""),
        latitude=float(stationxml_data.get("latitude", "0")),
        longitude=float(stationxml_data.get("longitude", "0")),
        elevation=float(stationxml_data.get("elevation", "0")),
        start_date=start_time,
        end_date=end_time,
        site=site,
        channels=[channel]
    )
    if stationxml_data.get("station_description"):
        station.description = stationxml_data["station_description"]

    net_desc = stationxml_data.get("network_description", "")
    net_desc += f" | Identifier: {network_identifier}"
    network = Network(
        code=stationxml_data.get("network_code", ""),
        description=net_desc,
        start_date=start_time,
        end_date=end_time,
        stations=[station]
    )

    inventory = Inventory(networks=[network], source=sender)
    xml_filename = f"{os.path.splitext(wav_file_name)[0]}.station.xml"
    inventory.write(xml_filename, format="STATIONXML")

    # Post-process with lxml to ensure compliance
    xml_parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(xml_filename, xml_parser)
    root = tree.getroot()
    ns_pref = f"{{{root.nsmap[None]}}}" if None in root.nsmap else ""

    # Ensure <Source> before <Sender>
    sender_el = root.find(f"{ns_pref}Sender")
    if source:
        src_el = root.find(f"{ns_pref}Source") or etree.Element(f"{ns_pref}Source")
        src_el.text = source
        if src_el.getparent() is None and sender_el is not None:
            idx = list(root).index(sender_el)
            root.insert(idx, src_el)

    # Ensure <Sender> text
    if sender_el is None:
        sender_el = etree.Element(f"{ns_pref}Sender")
        root.insert(0, sender_el)
    sender_el.text = sender

    # Remove all <EndDate> children (EIDA standard requirement)
    for ed in root.xpath(f".//{ns_pref}EndDate"):
        ed.getparent().remove(ed)

    # Under each <Network>, force <Identifier> first, <Station> last
    for net in root.findall(f"{ns_pref}Network"):
        ident = net.find(f"{ns_pref}Identifier")
        if ident is None:
            ident = etree.Element(f"{ns_pref}Identifier")
            net.insert(0, ident)
        ident.text = network_identifier
        net.remove(ident)
        net.insert(0, ident)
        st = net.find(f"{ns_pref}Station")
        if st is not None:
            net.remove(st)
            net.append(st)

    tree.write(xml_filename, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    return xml_filename


class AudioProcessor:
    """Main processor class for converting WAV files to FLAC and MiniSEED."""
    
    def __init__(self):
        """Initialize the processor and setup FFmpeg."""
        ffmpeg_exe, ffprobe_exe = setup_ffmpeg()
        if ffmpeg_exe and ffprobe_exe:
            AudioSegment.converter = ffmpeg_exe
            AudioSegment.ffprobe = ffprobe_exe
            os.environ["FFMPEG_BINARY"] = ffmpeg_exe
        else:
            raise RuntimeError(
                "FFmpeg not found. Please install FFmpeg and set FFMPEG_BIN environment variable, "
                "or ensure ffmpeg is in your system PATH."
            )
    
    def process_wav_file(self, file_path, metadata, plot_first=False, tz_offset=0):
        """
        Process a single WAV file: downsample, convert to FLAC, add metadata.
        Returns the path to the created FLAC file.
        """
        rate, data = get_wav_info(file_path)
        duration_seconds = len(data) / rate
        if duration_seconds > 86400:
            raise ValueError(f"File {file_path} has an implausibly long duration ({duration_seconds} seconds).")
        
        # Extract file-specific start/end times and initial sampling rate
        file_start_time, file_end_time = extract_times_from_wav(file_path)
        # Adjust times by the UTC offset so FLAC metadata reflects UTC time
        adjusted_start_time = file_start_time - timedelta(hours=tz_offset)
        adjusted_end_time = file_end_time - timedelta(hours=tz_offset)
        file_metadata = metadata.copy()
        file_metadata["time_coverage_start"] = adjusted_start_time.isoformat()
        file_metadata["time_coverage_end"] = adjusted_end_time.isoformat()
        file_metadata["initial_sampling_rate"] = rate

        if rate > FINAL_SAMPLING_RATE:
            downsampled_data, filtered_data = downsample_wav(data, rate, FINAL_SAMPLING_RATE)
            if plot_first:
                plot_signals(data, filtered_data, downsampled_data, rate, FINAL_SAMPLING_RATE)
        else:
            downsampled_data = data
        
        downsampled_data = convert_data_format(downsampled_data)
        
        # Create a temporary WAV file
        temp_wav_path = tempfile.mktemp(suffix=".wav")
        sf.write(temp_wav_path, downsampled_data, FINAL_SAMPLING_RATE)
        if not os.path.exists(temp_wav_path):
            raise FileNotFoundError(f"Temporary file {temp_wav_path} was not created.")
        
        flac_output_path = file_path.replace('.wav', '.flac').replace('.WAV', '.flac')
        convert_wav_to_flac(temp_wav_path, flac_output_path)
        add_metadata_to_flac(flac_output_path, file_metadata)
        
        # Clean up temporary file
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
        
        return flac_output_path
    
    def process_files(self, file_paths, metadata, stationxml_data, tz_offset, plot_preference=False):
        """
        Process multiple WAV files.
        Creates FLAC, MiniSEED, and StationXML files for each input.
        """
        total_files = len(file_paths)
        successful_files = 0
        import time
        start_processing_time = time.time()

        for index, file_path in enumerate(file_paths):
            try:
                print(f"🔍 Analyzing file {index + 1} of {total_files} — {os.path.basename(file_path)}")
                
                # Process to FLAC
                flac_output_path = self.process_wav_file(
                    file_path,
                    metadata,
                    plot_first=(index == 0 and plot_preference),
                    tz_offset=tz_offset
                )

                # Convert to MiniSEED
                miniseed_output_path = file_path.replace('.wav', '.mseed').replace('.WAV', '.mseed')
                flac_to_miniseed(flac_output_path, miniseed_output_path)

                # Generate StationXML
                rate, data = get_wav_info(file_path)
                duration_seconds = len(data) / rate
                xml_output_path = generate_stationxml_obspy(
                    wav_file_name=os.path.basename(file_path),
                    stationxml_data=stationxml_data,
                    duration_seconds=duration_seconds,
                    tz_offset=tz_offset
                )

                print(f"✅ Created files for {file_path}:\n"
                      f"   • FLAC: {flac_output_path}\n"
                      f"   • MiniSEED: {miniseed_output_path}\n"
                      f"   • StationXML (.station.xml): {os.path.abspath(xml_output_path)}")
                successful_files += 1

            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")

        total_elapsed = time.time() - start_processing_time
        elapsed_str = time.strftime('%H:%M:%S', time.gmtime(total_elapsed))
        print(f"\n🎯 Processed {successful_files} out of {total_files} files successfully.")
        print(f"⏱️ Total processing time: {elapsed_str}")

