#!/usr/bin/env python3

import setuptools

setuptools.setup(
    name='VxWireguard-Generator',
    version='1.0',
    description='Utility to generate VXLAN over Wireguard mesh configuration',
    author='Star Brilliant',
    author_email='coder@poorlab.com',
    url='https://github.com/m13253/VxWireguard-Generator',
    install_requires=[
        'toml',
        'PyNaCl',
    ],
    packages=['vwgen'],
    entry_points={
        'console_scripts': ['vwgen=vwgen.__main__:__main__'],
    },
)
