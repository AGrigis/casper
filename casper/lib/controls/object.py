#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Casper import
from .base import Base


class Object(Base):
    """ Define a generic object parameter.
    """
    def _is_valid(self, value):
        """ A method used to check if the value is valid.

        Parameters
        ----------
        value: object (mandatory)
            a string.

        Returns
        -------
        is_valid: bool
            always True.
        """
        return True
