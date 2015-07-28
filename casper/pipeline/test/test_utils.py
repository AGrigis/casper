#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import unittest

# Casper import
from casper.pipeline.utils import ControlObject
from casper.pipeline.utils import load_xml_description
from casper.pipeline.utils import parse_docstring


class TestUtils(unittest.TestCase):
    """ Test the boxe utilities.
    """
    def test_load_xml(self):
        """ Method to test the loading of xml description.
        """
        # Return to new line
        print

        # Test raise case
        self.assertRaises(IOError, load_xml_description, "")

    def test_parse_docstring(self):
        """ Method to test the parsing of docstring.
        """
        # Return to new line
        print

        # Test default case
        self.assertEqual(parse_docstring(""), [])

    def test_controlobject(self):
        """ Method to test the control object.
        """
        # Return to new line
        print

        # Test raise cases
        controller = ControlObject()
        self.assertRaises(ValueError, controller.__getitem__, "bad")


def test():
    """ Function to execute unitests.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUtils)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
