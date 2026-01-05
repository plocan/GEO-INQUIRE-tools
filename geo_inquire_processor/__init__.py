"""
GEO-INQUIRE Audio Processing Tool

A tool for converting WAV audio files to FLAC and MiniSEED formats
with EMSO and EIDA-compliant metadata for scientific data processing.
"""

__version__ = "1.0.0"
__author__ = "Silvana Neves"

from .processor import AudioProcessor
from .gui import Application

__all__ = ['AudioProcessor', 'Application']

