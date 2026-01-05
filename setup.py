"""
Setup script for GEO-INQUIRE Audio Processing Tool
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="geo-inquire-processor",
    version="1.0.0",
    author="Silvana Neves",
    author_email="",  # Add email if available
    description="Audio processing tool for WAV to FLAC/MiniSEED conversion with EMSO and EIDA metadata",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",  # Add GitHub URL when available
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Multimedia :: Sound/Audio",
        "License :: OSI Approved :: ",  # Add license
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20.0",
        "scipy>=1.7.0",
        "soundfile>=0.10.0",
        "pydub>=0.25.0",
        "mutagen>=1.45.0",
        "obspy>=1.4.0",
        "lxml>=4.6.0",
        "python-dateutil>=2.8.0",
        "plotly>=5.0.0",
        "matplotlib>=3.4.0",
        "Pillow>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "geo-inquire-processor=geo_inquire_processor.gui:Application",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)

