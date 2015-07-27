#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import numpy
import copy
import sys

# Casper import
from casper.lib.controls import controls
from .bbox import Bbox
from .utils import ControlObject
from casper.lib.base import Graph
from casper.lib.base import GraphNode


class Ibox(object):
    """ An iterative box that may be used to iterate over a building box.
    """
    iterprefix = "iter"
    itersep = "&"

    def __init__(self, desc, iterinputs=None, iteroutputs=None):
        """ Initialize the Ibox class.

        Parameters
        ----------
        desc: string (mandatory)
            a python function path relative to the module we want to decorate
            in a building box or the path to a xml pipeline description
            (relative to the module).
        """
        # Avoid cycling import
        from .pbox import Pbox

        # Define class parameters
        self.iterinputs = iterinputs or []
        self.iteroutputs = iteroutputs or []
        self.ispbox = False
        self.desc = desc
        if self.desc.endswith(".xml"):
            self.ispbox = True
            self.iterbox = Pbox(self.desc)
        else:
            self.iterbox = Bbox(self.desc)
        self.inputs = ControlObject()
        self.outputs = ControlObject()
        self.active = True

        # Create the bbox name
        self.id = self.iterbox.id

        # Create the input and output controls
        self._set_controls()

    def __call__(self, iterindex, box_name, *args, **kwargs):
        """ Execute the Ibox class.

        Parameters
        ----------
        iterindex: int (mandatory)
            the index of iterative elements used to parametrize the bbox.
        box_name: str (mandatory)
            the name of the key used to store the execution code.

        Returns
        -------
        returncode: dict
            the 'inputs', 'outputs', 'stdout', stderr', 'environ' and 'time'
            results obtained after the bbox execution.
        """
        # Parametrize the iterative bbox input parameters
        for control_name in self.iterinputs:
            itercontrol_name = "iter{0}".format(control_name)
            control_value = getattr(self.inputs, itercontrol_name).value
            setattr(
                self.iterbox.inputs, control_name, control_value[iterindex])

        # Execute the bbox
        box_name += str(iterindex)
        if self.ispbox:
            return self.iterbox(*args, **kwargs)
        else:
            return self.iterbox(box_name=box_name)

    ###########################################################################
    # Public Members
    ###########################################################################

    def update_iteroutputs(self, control_name, value, iteration):
        """ Update the ibox iterative output control values.

        Parameters
        ----------
        control_name: str
        value: object
        iteration: int
        """
        if control_name in self.iteroutputs:
            control_name = self.iterprefix + control_name
            itercontrol = getattr(self.outputs, control_name)
            if itercontrol.value is None:
                control_value = [None] * (iteration + 1)
            elif len(itercontrol.value) <= iteration:
                control_value = (
                    itercontrol.value + [None] * (
                        iteration + 1 - len(itercontrol.value)))
            else:
                control_value = itercontrol.value
            control_value[iteration] = value
        else:
            control_value = value
        setattr(self.outputs, control_name, control_value)

    def itergraphs(self, prefix=""):
        """ Create a list of iterative pipeline's graph representations.

        Parameters
        ----------
        prefix: str (optional, default '')
            a prefix for the box names.

        Returns
        -------
        itergraphs: dictionary
            the iterative pipeline's graph representations.
        """
        # Update the iterative pipeline only if all the input terative
        # controls have the same number of elements
        nb_of_elements = []
        for control_name in self.iterinputs:
            itercontrol_name = self.iterprefix + control_name
            itervalue = getattr(self.inputs, itercontrol_name).value
            if itervalue is None:
                return {}
            nb_of_elements.append(len(itervalue))
        nb_of_elements = numpy.asarray(nb_of_elements)
        nb_of_inputs = nb_of_elements.max()
        is_valid = (nb_of_elements == nb_of_inputs).all()

        # Update the iterative graphs
        itergraphs = {}
        if is_valid:

            # Create the requested number of graphs
            for iteritem in range(nb_of_inputs):

                # Copy and parametrize the iterative box
                # COMPATIBILITY: correctly copy bound instance methods after
                # python 2.7
                python_version = sys.version_info
                if python_version[:2] <= (2, 6):
                    from .pbox import Pbox
                    if self.desc.endswith(".xml"):
                        iterbox = Pbox(self.desc)
                    else:
                        iterbox = Bbox(self.desc)
                else:
                    iterbox = copy.deepcopy(self.iterbox)
                for control_name in self.iterinputs:
                    itercontrol_name = self.iterprefix + control_name
                    itercontrol = getattr(self.inputs, itercontrol_name)
                    setattr(iterbox.inputs, control_name,
                            itercontrol.value[iteritem])

                node_name = "{0}{1}{2}".format(prefix, self.itersep, iteritem)
                # Iterate on a bbox
                if isinstance(self.iterbox, Bbox):
                    itergraph = Graph()
                    itergraph.add_node(GraphNode(node_name, iterbox))
                # Iterate on a pbox
                else:
                    itergraph, _, _ = self.iterbox._create_graph(
                        iterbox, prefix=node_name + ".", filter_inactive=True)
                itergraphs[node_name] = itergraph

        return itergraphs

    ###########################################################################
    # Private Members
    ###########################################################################

    def _set_controls(self):
        """ Define the ibox input and output parameters.

        These parameters are defined in the list of iterative controls and
        built from the building box controls: add a 'List' extra level to
        create an iterative parameter.
        """
        # Build input iterative controls
        for control_name in self.iterinputs:

            # Check that the iterative control is defined in the building box
            if control_name not in self.iterbox.inputs.controls:
                raise ValueError(
                    "Impossible to build Ibox '{0}': '{1}' input iterative "
                    "control type is not defined in iterative building box. "
                    "Allowed inputs are {2}.".format(
                        self.id, control_name, self.iterbox.inputs.controls))

            # Create the iterative control
            control = getattr(self.iterbox.inputs, control_name)
            itercontent = control.__class__.__name__
            if hasattr(control, "content") and control.iterable:
                itercontent += "_{0}".format(control.content)
            itercontrol = controls["List"](content=itercontent)
            setattr(self.inputs, "iter{0}".format(control_name), itercontrol)

        # Build output iterative controls
        for control_name in self.iteroutputs:

            # Check that the iterative control is defined in the building box
            if control_name not in self.iterbox.outputs.controls:
                raise ValueError(
                    "Impossible to build Ibox '{0}': '{1}' outputs iterative "
                    "control type is not defined in iterative building box. "
                    "Allowed outputs are {2}.".format(
                        self.id, control_name, self.iterbox.outputs.controls))

            # Create the iterative control
            control = getattr(self.iterbox.outputs, control_name)
            itercontent = control.__class__.__name__
            if hasattr(control, "content") and control.iterable:
                itercontent += "_{0}".format(control.content)
            itercontrol = controls["List"](content=itercontent)
            setattr(self.outputs, "iter{0}".format(control_name), itercontrol)

        # Copy the input/output controls to the iterative box interface
        for control_name in self.iterbox.inputs.controls:
            if control_name not in self.iterinputs:
                control = getattr(self.iterbox.inputs, control_name)
                setattr(self.inputs, control_name, control)
        for control_name in self.iterbox.outputs.controls:
            if control_name not in self.iteroutputs:
                control = getattr(self.iterbox.outputs, control_name)
                setattr(self.outputs, control_name, control)
