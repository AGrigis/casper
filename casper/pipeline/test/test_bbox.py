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
from casper.pipeline import Bbox


class TestBBox(unittest.TestCase):
    """ Test the boxes creation.
    """

    def setUp(self):
        """ Initialize the TestObservable class.
        """
        self.myfuncdesc = "casper.demo.module.a_function_to_wrap"
        self.mycloth = "casper.demo.module.clothing"
        self.mypipedesc = "casper.demo.pipeline.xml"
        self.myclothingdesc = "casper.demo.clothing_pipeline.xml"
        self.mypipexmldesc = "casper.demo.xml_pipeline.xml"
        self.mypyramiddesc = "casper.demo.pyramid_pipeline.xml"
        self.myswitchdesc = "casper.demo.switch_pipeline.xml"
        self.myiterativedesc = "casper.demo.iterative_pipeline.xml"
        self.myfile = os.path.abspath(__file__)
        self.mydir = os.path.dirname(self.myfile)

    def test_bbox(self):
        """ Method to test if a bbox is properly created.
        """
        # Return to new line
        print

        # Create the box
        self.mybbox = Bbox(self.myfuncdesc)

        # Test class parameters
        self.assertEqual(self.mybbox.id, "casper.demo.module.AFunctionToWrap")
        self.assertEqual(self.mybbox.inputs.controls, ["fname", "directory"])
        self.assertEqual(self.mybbox.outputs.controls, ["string", "fname"])
        self.assertEqual(self.mybbox.inputs.fname.value, None)
        self.assertEqual(self.mybbox.inputs.directory.value, None)
        self.assertEqual(self.mybbox.outputs.string.value, None)
        self.assertFalse(self.mybbox.inputs.fname.optional)
        self.assertTrue(self.mybbox.inputs.directory.optional)

        # Update file parameter
        self.mybbox.inputs.fname = self.myfile
        self.assertEqual(self.mybbox.inputs.fname.value, self.myfile)

    def test_bbox_execution(self):
        """ Method to test if a bbox can be properly executed.
        """
        # Return to new line
        print

        # Create the box
        self.mybbox = Bbox(self.myfuncdesc)
        self.mybbox.inputs.fname = self.myfile
        self.mybbox.inputs.directory = self.mydir
        self.assertEqual(self.mybbox.inputs.fname.value, self.myfile)
        self.assertEqual(self.mybbox.inputs.directory.value, self.mydir)
        self.mybbox()
        self.assertEqual(self.mybbox.outputs.string.value,
                         "-".join([repr(self.myfile), repr(self.mydir)]))


def test():
    """ Function to execute unitests.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBBox)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
