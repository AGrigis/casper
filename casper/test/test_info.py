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
import os

# Casper import
import casper


class TestModuleInfo(unittest.TestCase):
    """ Test if all information are specified.
    """

    def setUp(self):
        """ Initialize the TestModuleInfo class.
        """
        self.release_info = {}
        fname = os.path.join(os.path.dirname(casper.__file__), "info.py")
        with open(fname) as ofile:
            exec(ofile.read(), self.release_info)

    def test_info(self):
        """ Method to test if the module meta information are specified.
        """
        for name in ["NAME", "DESCRIPTION", "LONG_DESCRIPTION", "LICENSE",
                     "CLASSIFIERS", "AUTHOR", "AUTHOR_EMAIL", "VERSION",
                     "URL", "PLATFORMS", "EXTRA_REQUIRES", "REQUIRES",
                     "__version__"]:
            self.assertTrue(name in self.release_info)


def test():
    """ Function to execute unitests.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestModuleInfo)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
