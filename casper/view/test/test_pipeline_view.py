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
import sys

# Qt import
from PySide import QtGui
from PySide.QtTest import QTest

# Casper import
from casper.pipeline import Pbox
from casper.view import PipelineView


class TestPipelineView(unittest.TestCase):
    """ Test observable pattern.
    """

    def setUp(self):
        """ Initialize the TestObservable class.
        """
        self.myclothingdesc = "casper.demo.clothing_pipeline.xml"
        self.mypyramiddesc = "casper.demo.pyramid_pipeline.xml"

        # Create a qt applicaction
        self.app = QtGui.QApplication.instance()
        if self.app is None:
            self.app = QtGui.QApplication(sys.argv)

    def test_pbox(self):
        """ Method to test if a pbox can be displayed properly.
        """
        # Create the box
        self.mypbox = Pbox(self.mypyramiddesc)
        self.mypbox._boxes["c2"].active = False
        self.mypbox._boxes["c7"].active = False
        getattr(self.mypbox._boxes["c7"].inputs, "inp").optional = True

        # Test view
        pview = PipelineView(self.mypbox)
        pview.show()

        # Start the qt loop
        self.app.exec_()

        # Test events
        pview.zoom_in()
        pview.zoom_out()
        QTest.keyClicks(pview, "p")
        # QTest.mouseClick(
        #     pview.scene.glinks.values()[0], QtCore.Qt.LeftButton)


def test():
    """ Function to execute unitests.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPipelineView)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
