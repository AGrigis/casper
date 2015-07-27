#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################


class SignalObject(object):
    """ Dummy class for signals.
    """
    pass


class Observable(object):
    """ Base class for observable classes.

    This class defines a simple interface to add or remove observers
    on an object.

    Attributes
    ----------
    `allowed_signals`: list
        a list with all the allowed signals.

    Methods
    -------
    add_observer
    remove_observer
    notify_observers
    """

    def __init__(self, signals):
        """ Initilaize the Observable class.

        Parameters
        ----------
        signals: list of string (mandatory)
            the default signals.
        """
        # Define private attributes to store signals and associated observers
        self._allowed_signals = []
        self._observers = {}

        # Inititialize the allowed signals
        for signal in signals:
            self._allowed_signals.append(signal)
            self._observers[signal] = []

        # A locked option to avoid multiple observer notifications
        self._locked = False

    def add_observer(self, signal, observer):
        """ Add an observer to the object.

        If the signal do not exist an axception is raised.
        An observer has a 'signal' attribute.

        Parameters
        ----------
        signal: string (mandatory)
            a signal to which we want to add an observer.
        observer: callable (madatory)
            a function that will be call.
        """
        self._is_allowed_signal(signal)
        self._add_observer(signal, observer)

    def remove_observer(self, signal, observer):
        """ Remove an observer from the object.

        If the signal do not exist an axception is raised.

        Parameters
        ----------
        signal: string (mandatory)
            a signal to which we want to add an observer.
        observer: callable (madatory)
            a function that will be call.
        """
        self._is_allowed_signal(signal)
        self._remove_observer(signal, observer)

    def notify_observers(self, signal, *args, **kwargs):
        """ Notify observers of a given signal.

        Extra arguments must be passed in kwargs.

        Parameters
        ----------
        signal: string (mandatory)
            a signal.

        Returns
        -------
        is_locked: bool
            return False if we already proccess a signal
            otherwise return True.
        """
        # We are already processing a signal
        if self._locked:
            return False

        # Lock the signal
        self._locked = True

        # Create the signal with associated kwargs
        signal_info = SignalObject()
        setattr(signal_info, "object", self)
        setattr(signal_info, "signal", signal)
        for name, value in kwargs.items():
            setattr(signal_info, name, value)

        # Notify observers
        for observer in self._observers[signal]:
            observer(signal_info)

        # Unlock the signal
        self._locked = False

        return True

    #########################################################################
    # Private interface
    #########################################################################

    def _is_allowed_signal(self, signal):
        if signal not in self._allowed_signals:
            raise Exception(
                "Signal '{0}' is not allowed for type {1}.".format(
                    signal, str(type(self))))

    def _add_observer(self, signal, observer):
        if observer not in self._observers[signal]:
            self._observers[signal].append(observer)

    def _remove_observer(self, signal, observer):
        if observer in self._observers[signal]:
            index = self._observers[signal].index(observer)
            del self._observers[signal][index]

    def _get_allowed_signals(self):
        return self._allowed_signals

    allowed_signals = property(_get_allowed_signals)
