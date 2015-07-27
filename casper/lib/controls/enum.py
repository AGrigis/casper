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


class Enum(Base):
    """ Define an enumerate parameter.
    """
    def _is_valid(self, value):
        """ A method used to check if the value is defined the possible
        choices.

        Parameters
        ----------
        value: str (mandatory)
            a string.

        Returns
        -------
        is_valid: bool
            return True if the value is defined the possible choices.
            False otherwise.
        """
        # Check the instance has a 'choices' attribute
        if not hasattr(self, "choices"):
            raise Exception("A 'choices' attribute is needed by an 'Enum' "
                            "control.")
        if not isinstance(self.choices, tuple):
            raise Exception("A tuple of 'choices' is needed by an 'Enum' "
                            "control.")

        # If the value is not defined the control is valid or
        # check if the new value is in the enumerate structure
        if value is None or value in self.choices:
            return True
        else:
            return False
