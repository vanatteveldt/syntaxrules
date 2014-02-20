#!/usr/bin/env python

from distutils.core import setup

# sudo apt-get install libgraphviz-dev

setup(
    name="syntaxrules",
    description="Tools for manipulating syntax trees",
    author="Wouter van Atteveldt",
    author_email="wouter@vanatteveldt.com",
    packages=["syntaxrules"],
    classifiers=[
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering",
        "Topic :: Text Processing",
    ],
    install_requires=[
        "unidecode",
        "rdflib",
    ],
)
