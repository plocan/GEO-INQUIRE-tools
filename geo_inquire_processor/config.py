"""
Configuration settings for the GEO-INQUIRE audio processor.
"""

import os
from pathlib import Path

# Final sampling rate for downsampling (Hz)
FINAL_SAMPLING_RATE = 300

# FFmpeg configuration - can be set via environment variable or auto-detected
FFMPEG_BIN = os.environ.get('FFMPEG_BIN', None)
FFMPEG_EXE = os.environ.get('FFMPEG_EXE', None)
FFPROBE_EXE = os.environ.get('FFPROBE_EXE', None)

def setup_ffmpeg():
    """
    Setup FFmpeg paths. Checks environment variables first,
    then common installation locations.
    """
    global FFMPEG_EXE, FFPROBE_EXE
    
    if FFMPEG_EXE and FFPROBE_EXE:
        return FFMPEG_EXE, FFPROBE_EXE
    
    # Common Windows locations
    common_paths = [
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin",
        r"C:\Program Files (x86)\ffmpeg\bin",
    ]
    
    # Check if ffmpeg is in PATH
    import shutil
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    
    if ffmpeg_path and ffprobe_path:
        FFMPEG_EXE = ffmpeg_path
        FFPROBE_EXE = ffprobe_path
        return FFMPEG_EXE, FFPROBE_EXE
    
    # Try common paths
    for path in common_paths:
        ffmpeg_exe = os.path.join(path, "ffmpeg.exe")
        ffprobe_exe = os.path.join(path, "ffprobe.exe")
        if os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe):
            FFMPEG_EXE = ffmpeg_exe
            FFPROBE_EXE = ffprobe_exe
            if path not in os.environ.get("PATH", ""):
                os.environ["PATH"] += os.pathsep + path
            return FFMPEG_EXE, FFPROBE_EXE
    
    # Return None if not found - will raise error when needed
    return None, None

