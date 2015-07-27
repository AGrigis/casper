#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# Casper import
from .observable import Observable


class ObservableList(list, Observable):
    """ Generate an observable list.

    Acting as a python list object.

    The 'append', 'pop', 'insert' and 'remove' methods have been overloaded in
    order to notify some observers. The associated signals have the name of
    the methods.
    """

    def __init__(self, sequence=None):
        """ Initialize the ObservableList class.
        """
        # Initialize the list object
        list.__init__(self, sequence)

        # Make the object an observable object
        Observable.__init__(self, ["append", "pop", "insert", "remove"])

    def append(self, value):
        """ Overload the list 'append' method.
        """
        list.append(self, value)
        self.notify_observers("append", value=value)

    def pop(self, *args):
        """ Overload the list 'pop' method.
        """
        value = list.pop(self, *args)
        self.notify_observers("pop", value=value)
        return value

    def insert(self, index, value):
        """ Overload the list 'insert' method.
        """
        list.insert(self, index, value)
        self.notify_observers("insert", value=value, index=index)

    def remove(self, value):
        """ Overload the list 'remove' method.
        """
        list.remove(self, value)
        self.notify_observers("remove", value=value)
