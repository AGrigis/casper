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
import tempfile
import shutil

# Capsul import
from casper.pipeline import Bbox
from casper.lib.cache import Memory
from casper.lib.cache.memory import MemorizedBox
from casper.lib.cache.memory import has_attribute
from casper.lib.cache.memory import tuple_json_encoder
from casper.lib.controls import List


class TestMemory(unittest.TestCase):
    """ Execute a bbox using smart-caching functionalities.
    """
    def setUp(self):
        """ Initialize the TestMemory class.
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
        self.cachedir = tempfile.mkdtemp()
        self.mem = Memory(self.cachedir)

    def tearDown(self):
        """ Destroy the temporary directory.
        """
        if self.cachedir is not None:
            shutil.rmtree(self.cachedir)

    def test_proxy_box_with_copy(self):
        """ Test the proxy box behaviours with cache and copy.
        """
        # Return to new line
        print

        # Create the box
        mybbox = Bbox(self.myfuncdesc)

        # Call the box in the cache
        self.mem.clear()
        cached_box = self.mem.cache(mybbox)
        returncode = cached_box()
        self.assertEqual(cached_box.outputs.fname.value, None)
        self.assertEqual(returncode[mybbox.id]["outputs"]["fname"], None)
        self.assertEqual(cached_box.outputs.string.value, "None-None")
        self.assertEqual(
            returncode[mybbox.id]["outputs"]["string"], "None-None")
        returncode = cached_box()

        # Test the copy in the cache
        cached_box.inputs.fname = self.myfile
        cached_box.inputs.directory = self.mydir
        returncode = cached_box()
        self.assertEqual(cached_box.outputs.fname.value, self.myfile)
        self.assertEqual(
            returncode[mybbox.id]["outputs"]["fname"], self.myfile)
        self.assertEqual(cached_box.outputs.string.value,
                         "-".join([repr(self.myfile), repr(self.mydir)]))
        self.assertEqual(returncode[mybbox.id]["outputs"]["string"],
                         "-".join([repr(self.myfile), repr(self.mydir)]))
        cache_dir, _, _ = cached_box._get_box_id()
        self.assertFalse(os.path.isfile(
            os.path.join(cache_dir, os.path.basename(self.myfile))))
        self.mem.clear()
        cached_box.outputs.fname.copy = True
        returncode = cached_box()
        self.assertTrue(os.path.isfile(
            os.path.join(cache_dir, os.path.basename(self.myfile))))

    def test_proxy_box_without_cache(self):
        """ Test the proxy box behaviours without cache.
        """
        # Return to new line
        print

        # Create the empty cache
        self.cachedir = None
        self.mem = Memory(self.cachedir)

        # Create the box
        mybbox = Bbox(self.mycloth)
        cached_box = self.mem.cache(mybbox)

        # Test parameters
        self.assertEqual(id(mybbox), id(cached_box.box))
        self.assertTrue(isinstance(repr(cached_box), str))

        # Test creation with memorized object
        cached_box_2 = self.mem.cache(cached_box)
        self.assertEqual(id(mybbox), id(cached_box_2.box))

        # Call the box in the cache
        returncode = cached_box()
        self.assertEqual(cached_box.outputs.outp.value, None)
        self.assertEqual(returncode[cached_box.id]["outputs"]["outp"], None)
        cached_box.inputs.inp = "slip"
        returncode = cached_box()
        self.assertEqual(cached_box.outputs.outp.value, "slip")
        self.assertEqual(returncode[mybbox.id]["outputs"]["outp"], "slip")
        returncode = cached_box(inp="pantalon")
        self.assertEqual(cached_box.outputs.outp.value, "pantalon")
        self.assertEqual(returncode[mybbox.id]["outputs"]["outp"], "pantalon")

    def test_proxy_box_with_cache(self):
        """ Test the proxy box behaviours with cache.
        """
        # Return to new line
        print

        # Create the box
        mybbox = Bbox(self.mycloth)
        cached_box = self.mem.cache(mybbox)

        # Test parameters
        self.assertEqual(id(mybbox), id(cached_box.box))
        self.assertTrue(isinstance(repr(cached_box), str))

        # Call the box in the cache
        returncode = cached_box()
        self.assertEqual(cached_box.outputs.outp.value, None)
        self.assertEqual(returncode[mybbox.id]["outputs"]["outp"], None)
        returncode = cached_box()
        cached_box.inputs.inp = "slip"
        returncode = cached_box()
        self.assertEqual(cached_box.outputs.outp.value, "slip")
        self.assertEqual(returncode[mybbox.id]["outputs"]["outp"], "slip")
        returncode = cached_box()
        returncode = cached_box(inp="pantalon")
        self.assertEqual(cached_box.outputs.outp.value, "pantalon")
        self.assertEqual(returncode[mybbox.id]["outputs"]["outp"], "pantalon")

    def test_memorized_box(self):
        """ Test the memorized box creation.
        """
        # Create the box
        mybbox = Bbox(self.mycloth)

        # Test raises
        self.assertRaises(ValueError, MemorizedBox, mybbox, None)
        self.assertRaises(ValueError, MemorizedBox, mybbox, "")

        # Test parameters
        mbox = MemorizedBox(mybbox, self.cachedir)
        self.assertTrue(mbox.timestamp is not None)

        # Test copy
        file_mapping = []
        python_object = {
            "1": [self.myfile, 156],
            "2": (self.mydir, )
        }
        mbox._copy_files_to_memory(python_object, self.cachedir, file_mapping)
        self.assertTrue(os.path.isfile(
            os.path.join(self.cachedir, os.path.basename(self.myfile))))

        # Test hash
        hash1, _ = mbox._get_argument_hash()
        mbox.inputs.inp.nohash = True
        hash2, _ = mbox._get_argument_hash()
        self.assertEqual(hash1, hash2)
        mbox.inputs.inp = self.myfile
        hash3, _ = mbox._get_argument_hash()
        self.assertEqual(hash2, hash3)
        mbox.inputs.inp.nohash = False
        hash4, _ = mbox._get_argument_hash()
        self.assertTrue(hash3 != hash4)

        # Test fingerprint
        updated_object = mbox._add_fingerprints(python_object)
        self.assertTrue(isinstance(updated_object["1"][0], dict))

        # Test nohash search
        control = List(content="Int", nohash=False)
        has_nohash = has_attribute(control, "noshash", True, recursive=True)
        self.assertFalse(has_nohash)
        control.inner_control.nohash = True
        has_nohash = has_attribute(control, "noshash", True, recursive=True)
        self.assertTrue(has_nohash)

        # Test encoder
        updated_object = tuple_json_encoder(python_object)
        self.assertTrue(isinstance(updated_object["2"], dict))


def test():
    """ Function to execute unitest.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMemory)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
