#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) CEA, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from ez_setup import use_setuptools
use_setuptools()
import os
from setuptools import find_packages, setup

# Capsul import
import casper


# Select appropriate modules
modules = find_packages()

# Set selected package options
scripts = []
pkgdata = {
    "capser.pipeline.test": ["*.xml"],
}
release_info = {}
with open(os.path.join(os.path.dirname(casper.__file__), "info.py")) as ofile:
    exec(ofile.read(), release_info)

# Build the setup
setup(
    name=release_info["NAME"],
    description=release_info["DESCRIPTION"],
    long_description=release_info["LONG_DESCRIPTION"],
    license=release_info["LICENSE"],
    classifiers=release_info["CLASSIFIERS"],
    author=release_info["AUTHOR"],
    author_email=release_info["AUTHOR_EMAIL"],
    version=release_info["VERSION"],
    url=release_info["URL"],
    packages=modules,
    package_data=pkgdata,
    platforms=release_info["PLATFORMS"],
    extras_require=release_info["EXTRA_REQUIRES"],
    install_requires=release_info["REQUIRES"],
    scripts=scripts
)
