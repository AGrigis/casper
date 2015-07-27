#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import warnings
from .info import __version__


def warning_message(message, category, filename, lineno, file=None, line=None):
    """ Define the format of a warning message.
    """
    return ">>> {0}:{1}: {2}\n    {3}\n".format(
        filename, lineno, category.__name__, message)


warnings.formatwarning = warning_message
