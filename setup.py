#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages
from wordbook import utils

with open("README.md", "r") as file:
    readme = file.read()

with open("CHANGELOG.md", "r") as file:
    history = file.read()

requirements = []

setup_requirements = []

extra_requirements = {
    "GTK": ["PyGObject"],
    "Qt": ["PyQt5"],
}

setup(
    author="Mufeed Ali",
    author_email="fushinari@protonmail.com",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Wordbook is a dictionary application using python-wn and espeak.",
    entry_points={
        "gui_scripts": [
            "wordbook=wordbook.gtk:main [GTK]",
            "wordbook-qt=wordbook.qt:main [Qt]",
        ],
    },
    install_requires=requirements,
    license="GPL-3",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="wordbook",
    name="wordbook",
    packages=find_packages(include=["wordbook", "wordbook.*", "gtk/ui/*"]),
    package_data={"wordbook": ["gtk/ui/*", "qt/ui/*"]},
    setup_requires=setup_requirements,
    extras_require=extra_requirements,
    url="https://github.com/fushinari/wordbook",
    version=utils.VERSION,
    zip_safe=False,
)
