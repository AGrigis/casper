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
import numpy

# Casper import
from casper.pipeline import Bbox
from casper.pipeline import Pbox
from casper.pipeline import Ibox
from casper.lib.controls import List


class TestIBox(unittest.TestCase):
    """ Test the iterative box creation.
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

    def test_ibox(self):
        """ Method to test if an ibox is properly created.
        """
        # Return to new line
        print

        # Create a bbox
        box = Bbox(self.myfuncdesc)

        # Test raises
        self.assertRaises(ValueError, Ibox, box, iterinputs=["bad"])
        self.assertRaises(ValueError, Ibox, box, iteroutputs=["bad"])

        # Create the box
        self.myibox = Ibox(box, iterinputs=["fname"], iteroutputs=["string"])
        iterprefix = self.myibox.iterprefix

        # Test parameters
        self.assertEqual(
            self.myibox.inputs.controls, [
                iterprefix + name
                for name in self.myibox.iterbox.inputs.controls
                if name in self.myibox.iterinputs] + [
                name for name in self.myibox.iterbox.inputs.controls
                if name not in self.myibox.iterinputs])
        self.assertEqual(
            self.myibox.outputs.controls, [
                iterprefix + name
                for name in self.myibox.iterbox.outputs.controls
                if name in self.myibox.iteroutputs] + [
                name for name in self.myibox.iterbox.outputs.controls
                if name not in self.myibox.iteroutputs])
        self.assertTrue(
            numpy.asarray([
                isinstance(getattr(self.myibox.inputs, name), List)
                for name in self.myibox.inputs.controls
                if name in self.myibox.iterinputs]).all())
        self.assertTrue(
            numpy.asarray([
                isinstance(getattr(self.myibox.outputs, name), List)
                for name in self.myibox.outputs.controls
                if name in self.myibox.iteroutputs]).all())
        self.myibox.inputs.directory = self.mydir
        self.assertEqual(self.myibox.inputs.directory.value, self.mydir)
        self.assertEqual(
            self.myibox.iterbox.inputs.directory.value, self.mydir)
        self.myibox.inputs.iterfname = [self.myfile, self.myfile]
        self.assertEqual(self.myibox.inputs.iterfname.value,
                         [self.myfile, self.myfile])
        self.assertEqual(self.myibox.iterbox.inputs.fname.value, None)

        # Test execution
        returncode = self.myibox(0, "myibox")
        self.assertEqual(returncode["myibox0"]["outputs"]["string"],
                         "-".join([repr(self.myfile), repr(self.mydir)]))

    def test_xml_ibox(self):
        """ Method to test if a pbox can contain an ibox.
        """
        # Return to new line
        print

        # Create the box
        self.mypbox = Pbox(self.myiterativedesc)

        # Test raises
        self.assertRaises(ValueError, self.mypbox)

        # Test execution
        self.mypbox.inputs.inp = "str"
        self.mypbox()
        self.assertEqual(self.mypbox.outputs.outp.value, "str0str1")

        if 0:
            from PySide import QtGui
            import sys
            from casper.view import PipelineView
            app = QtGui.QApplication.instance()
            if app is None:
                app = QtGui.QApplication(sys.argv)
            pview = PipelineView(self.mypbox)
            pview.show()
            app.exec_()


def test():
    """ Function to execute unitests.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestIBox)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
