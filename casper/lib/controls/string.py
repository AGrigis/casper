#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import sys

# Casper import
from .base import Base


class String(Base):
    """ Define a string parameter.
    """
    def _is_valid(self, value):
        """ A method used to check if the value is a string.

        Parameters
        ----------
        value: str (mandatory)
            a string.

        Returns
        -------
        is_valid: bool
            return True if the value is a string,
            False otherwise.
        """
        # COMPATIBILITY: unicode not defined in python 3
        python_version = sys.version_info
        if python_version[0] == 3:
            if value is None or isinstance(value, (str, bytes)):
                return True
        elif value is None or isinstance(value, (str, unicode)):
            return True
        else:
            return False
