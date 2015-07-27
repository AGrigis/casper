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
from casper.lib.base import Observable
from casper.lib.base import ObservableList


class TestObservable(unittest.TestCase):
    """ Test observable pattern.
    """

    def setUp(self):
        """ Initialize the TestObservable class.
        """
        self.signals = ["update"]
        self.obs = Observable(self.signals)
        self.obslist = ObservableList([1, 2, 3])

    def test_properties(self):
        """ Method to test if object properties are retunred properly.
        """
        self.assertEqual(self.signals, self.obs.allowed_signals)

    def test_update(self):
        """ Method to test if we can notify observers.
        """
        # Return to new line
        print

        # Define observers
        def observer1(signal):
            print("observer1: {0} -> {1}".format(
                signal.signal, signal.message))

        def observer2(signal):
            print("observer2: {0} -> {1}".format(
                signal.signal, signal.message))

        # Add observers
        self.obs.add_observer("update", observer1)
        self.obs.add_observer("update", observer2)

        # Notify observers
        self.assertTrue(self.obs.notify_observers("update", message="test"))
        self.obs._locked = True
        self.assertFalse(self.obs.notify_observers("update", message="test"))

        # Remove observers
        self.obs.remove_observer("update", observer1)
        self.obs.remove_observer("update", observer2)

        # Check raises
        self.assertRaises(Exception, self.obs._is_allowed_signal, "bad")

    def test_list(self):
        """ Method to test if we can notify a list observers.
        """
        # Return to new line
        print

        # Define observers
        def observer_append(signal):
            print("observer: {0} -> {1}".format(
                signal.signal, signal.value))

        def observer_pop(signal):
            print("observer: {0} -> {1}".format(
                signal.signal, signal.value))

        def observer_insert(signal):
            print("observer: {0} -> {1}-{2}".format(
                signal.signal, signal.index, signal.value))

        def observer_remove(signal):
            print("observer: {0} -> {1}".format(signal.signal, signal.value))

        # Add observers
        self.obslist.add_observer("append", observer_append)
        self.obslist.add_observer("pop", observer_pop)
        self.obslist.add_observer("insert", observer_insert)
        self.obslist.add_observer("remove", observer_remove)

        # Update list
        self.obslist.append(4)
        self.assertEqual(self.obslist, [1, 2, 3, 4])
        self.obslist.insert(0, 0)
        self.assertEqual(self.obslist, [0, 1, 2, 3, 4])
        self.obslist.pop(1)
        self.assertEqual(self.obslist, [0, 2, 3, 4])
        self.obslist.pop()
        self.assertEqual(self.obslist, [0, 2, 3])
        self.obslist.remove(2)
        self.assertEqual(self.obslist, [0, 3])


def test():
    """ Function to execute unitests.
    """
    suite = unittest.TestLoader().loadTestsFromTestCase(TestObservable)
    runtime = unittest.TextTestRunner(verbosity=2).run(suite)
    return runtime.wasSuccessful()


if __name__ == "__main__":
    test()
