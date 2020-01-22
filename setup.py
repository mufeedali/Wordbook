#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages
from reo import utils
from m2r import parse_from_file

readme = parse_from_file('README.md')

history = parse_from_file('CHANGELOG')

requirements = []

setup_requirements = []

extra_requirements = {
    'GTK': ['pygobject'],
    'Qt': ['PyQt5'],
}

setup(
    author="Mufeed Ali",
    author_email='lastweakness@tuta.io',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Reo is a dictionary application using dictd and espeak.",
    entry_points={
        'gui_scripts': [
            'reo-gtk=reo.gtk:main [GTK]',
            'reo-qt=reo.qt:main [Qt]',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='reo',
    name='reo',
    packages=find_packages(include=['reo', 'reo.*']),
    setup_requires=setup_requirements,
    extras_require=extra_requirements,
    url='https://github.com/lastweakness/reo',
    version=utils.VERSION,
    zip_safe=False,
)
