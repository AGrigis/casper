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
from casper.pipeline import Pbox


class TestPBox(unittest.TestCase):
    """ Test the pipeline box creation.
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
        self.mylinks = ["fname->p1.fname", "pdirectory->p1.directory",
                        "p2.string->outstring", "p1.string->p2.fname",
                        "pdirectory->p2.directory"]

    def test_pbox(self):
        """ Method to test if a pbox is properly created.
        """
        # Return to new line
        print

        # Create the box
        self.mypbox = Pbox(self.mypipedesc)

        # Test class parameters
        self.assertEqual(self.mypbox.id, "casper.demo.Pipeline")
        self.assertEqual(self.mypbox.inputs.fname.value, None)
        self.assertTrue(set(self.mypbox._links).issubset(self.mylinks))
        self.assertTrue(len(self.mypbox._links) == len(self.mylinks))
        self.assertTrue(self.mypbox._boxes["p1"].inputs.fname.optional)
        self.assertFalse(self.mypbox._boxes["p2"].inputs.fname.optional)

        # Update file parameter
        self.mypbox._boxes["p1"].outputs.string = self.myfile
        self.assertEqual(self.mypbox._boxes["p1"].outputs.string.value,
                         self.mypbox._boxes["p2"].inputs.fname.value)

        # Update directory parameter
        self.mypbox.inputs.pdirectory = self.mydir
        self.assertEqual(self.mypbox.inputs.pdirectory.value,
                         self.mypbox._boxes["p1"].inputs.directory.value)

    def test_pbox_execution(self):
        """ Method to test if a pbox can be properly executed.
        """
        # Return to new line
        print()

        # Create the box
        self.mypbox = Pbox(self.myclothingdesc)

        # Test class parameters
        self.mypbox.inputs.inp1 = "my_value_1"
        self.mypbox.inputs.inp2 = "my_value_2"
        self.mypbox.inputs.inp3 = "my_value_1"
        self.assertEqual(self.mypbox.inputs.inp1.value, "my_value_1")
        self.assertEqual(self.mypbox.inputs.inp2.value, "my_value_2")
        self.assertEqual(self.mypbox.inputs.inp3.value, "my_value_1")

        # Test execution
        self.mypbox()
        self.assertEqual(self.mypbox.outputs.outp1.value, "my_value_2")
        self.assertEqual(self.mypbox.outputs.outp2.value, "my_value_2")
        self.assertEqual(self.mypbox.outputs.outp3.value, "my_value_1")

    def test_xml_pbox(self):
        """ Method to test if a pbox can contain a pbox.
        """
        # Return to new line
        print

        # Create the box
        self.mypbox = Pbox(self.mypipexmldesc)

        # Test class parameters
        self.assertEqual(self.mypbox.id, "casper.demo.XmlPipeline")
        self.assertEqual(self.mypbox.inputs.fname.value, None)
        # self.assertTrue(set(self.mypbox._links).issubset(self.mylinks))
        # self.assertTrue(len(self.mypbox._links) == len(self.mylinks))

        # Update file parameter
        self.mypbox._boxes["p1"].outputs.string = self.myfile
        self.assertEqual(self.mypbox._boxes["p1"].outputs.string.value,
                         self.mypbox._boxes["p2"].inputs.fname.value)

        # Update directory parameter
        self.mypbox.inputs.pdirectory = self.mydir
        self.assertEqual(self.mypbox.inputs.pdirectory.value,
                         self.mypbox._boxes["p1"].inputs.directory.value)

    def test_xml_pbox_execution(self):
        """ Method to test if a pbox containing a pbox can be properly
        executed.
        """
        # Return to new line
        print

        # Create the box
        self.mypbox = Pbox(self.mypyramiddesc)

        # Test class parameters
        self.mypbox.inputs.inp = "toto"
        self.assertEqual(self.mypbox.inputs.inp.value, "toto")

        # Test execution
        self.mypbox()
        self.assertEqual(self.mypbox.outputs.outp.value, "toto")

    def test_xml_pbox_switch(self):
        """ Method to test if a pbox can contained a selector.
        """
        # Return to new line
        print

        # Create the box
        self.mypbox = Pbox(self.myswitchdesc)

        # Test parametrization
        self.mypbox.inputs.inp = "toto"
        self.mypbox.inputs.haut = "ete"
        self.assertFalse(self.mypbox._boxes["cravate"].active)
        self.assertFalse(self.mypbox._boxes["chemise"].active)
        self.assertTrue(self.mypbox._boxes["tshirt"].active)
        self.mypbox.inputs.bas = "hiver"
        self.assertTrue(self.mypbox._boxes["pantalon"].active)
        self.assertTrue(self.mypbox._boxes["ceinture"].active)
        self.assertFalse(self.mypbox._boxes["short"].active)

        # Test execution
        self.mypbox()
        self.assertEqual(
            self.mypbox._boxes["cravate"].outputs.outp.value, None)
        self.assertEqual(
            self.mypbox._boxes["chemise"].outputs.outp.value, None)
        self.assertEqual(
            self.mypbox._boxes["short"].outputs.outp.value, None)
        self.assertEqual(
            self.mypbox._boxes["tshirt"].outputs.outp.value, "toto")
        self.assertEqual(
            self.mypbox._boxes["pantalon"].outputs.outp.value, "toto")
        self.assertEqual(
            self.mypbox._boxes["ceinture"].outputs.outp.value, "toto")


def test():
    """ Function to execute unitests.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPBox)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
