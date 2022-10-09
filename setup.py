"""Package installer."""
import codecs
import os

from setuptools import find_packages, setup


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version(rel_path):
    for line in read(rel_path).splitlines():
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


LONG_DESCRIPTION = ""
if os.path.exists("README.md"):
    with open("README.md") as fp:
        LONG_DESCRIPTION = fp.read()


setup(
    name="gpxfix",
    version=get_version("gpxfix/__init__.py"),
    description="gpxfix: GUI to fix .gpx tracks with missing sections",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="Jannis Born",
    author_email="jannis.born@gmx.de",
    url="https://github.com/jannisborn/gpxfix",
    license="MIT",
    install_requires=["numpy", "gpxpy>=1.3.5", "matplotlib"],
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages("."),
    scripts=["bin/gpxfix"],
    keywords=["GPX", "Tracking", "Sports", "Running", "Cycling", "Strava"],
)
