#!/usr/bin/env python
from setuptools import setup

setup(
    name='Chitin',
    description='Template/data static website framework',
    long_description=open('license').read(),
    version='0.0.1',
    py_modules=['chitin'],
    scripts=['chitin.py'],
    install_requires=['jinja2'],
    author='Phil Schleihauf',
    author_email='uniphil@gmail.com',
    data_files=[('', ['readme.md'])],
    license='MIT',
    classifiers=['License :: OSI Approved :: MIT License'],
)
