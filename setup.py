#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages
from reo import utils

with open('README.md', 'r') as file:
    readme = file.read()

with open('CHANGELOG.md', 'r') as file:
    history = file.read()

requirements = []

setup_requirements = []

extra_requirements = {
    'GTK': ['PyGObject'],
    'Qt': ['PyQt5'],
}

setup(
    author="Mufeed Ali",
    author_email='fushinari@protonmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Reo is a dictionary application using dictd and espeak.",
    entry_points={
        'gui_scripts': [
            'reo=reo.gtk:main [GTK]',
            'reo-qt=reo.qt:main [Qt]',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='reo',
    name='reo',
    packages=find_packages(include=['reo', 'reo.*', 'gtk/ui/*']),
    package_data={'reo': ['data/*', 'gtk/ui/*', 'qt/ui/*']},
    setup_requires=setup_requirements,
    extras_require=extra_requirements,
    url='https://github.com/fushinari/reo',
    version=utils.VERSION,
    zip_safe=False,
)
