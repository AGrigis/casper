#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import re
import os
import sys
import inspect
import timeit
try:
    import importlib
except:
    pass

# Casper import
from casper.lib.controls import controls
from .utils import ControlObject
from .utils import title_for
from .utils import parse_docstring


class Bbox(object):
    """ A building box that may be used to define a processing pipeline.
    """
    xml_tag = "unit"

    def __init__(self, funcdesc):
        """ Initialize the Bbox class.

        Parameters
        ----------
        funcdesc: string (mandatory)
            a python function path relative to the module we want to decorate
            in a building box.
        """
        # Load the function we want to decorate in a bbox
        func = self._load(funcdesc)

        # Define class parameters
        self._func = func
        self.inputs = ControlObject()
        self.outputs = ControlObject()
        self.active = True

        # Create the bbox name
        self.id = self._func.__module__ + "." + title_for(self._func.__name__)

        # Get the function to decorate prototype
        self.proto = parse_docstring(self._func.__doc__)

        # Update the bbox documentation
        docstring = self._func.__doc__
        # COMPATIBILITY: option not defined in python 2.6
        python_version = sys.version_info
        if python_version[:2] <= (2, 6):
            res = re.search(r"<{0}>.*</{0}>".format(self.xml_tag), docstring,
                            flags=re.DOTALL)
            if res:
                docstring = docstring.replace(
                    docstring[res.start():res.end()], "")
        else:
            docstring = re.sub(r"<{0}>.*</{0}>".format(self.xml_tag), "",
                               docstring, flags=re.DOTALL)
        self.__doc__ += docstring

        # Create the input and output controls
        self._set_controls()

    def __call__(self, box_name=None):
        """ Execute the Bbox class.

        Parameters
        ----------
        box_name: str (optional, default None)
            the name of the key used to store the execution code.

        Returns
        -------
        returncode: dict
            the 'inputs', 'outputs', 'stdout', stderr', 'environ' and 'time'
            results obtained after the bbox execution.
        """
        # Build expression and namespace
        namespace, expression = self._build_expression()

        # Execute the function
        tic = timeit.default_timer()
        exec(expression, namespace)
        toc = timeit.default_timer()

        # Create a returncode
        box_name = box_name or self.id
        # COMPATIBILITY: dict in python 2 becomes structure in pyton 3
        python_version = sys.version_info
        if python_version[0] < 3:
            environ = os.environ
        else:
            environ = os.environ._data
        returncode = dict([
            (box_name, dict([
                ("inputs", {}), ("outputs", {}), ("stdout", None),
                ("stderr", None), ("environ", environ),
                ("time", toc - tic)]))])
        inputs = returncode[box_name]["inputs"]
        for control_name in self.inputs.controls:
            inputs[control_name] = namespace[control_name]

        # Update the output control values
        outputs = returncode[box_name]["outputs"]
        for control_name in self.outputs.controls:
            outputs[control_name] = namespace[control_name]
            setattr(self.outputs, control_name, namespace[control_name])

        return returncode

    ###########################################################################
    # Public Members
    ###########################################################################

    def update_control_names(self, prefix):
        """ Update the control names.

        Parameters
        ----------
        prefix: string
            a prefix that will be added to all the input and output control
            names.
        """
        for name in self.inputs.controls:
            self.inputs[name].name = (
                "{0}->".format(prefix) + self.inputs[name].name)
        for name in self.outputs.controls:
            if self.outputs[name].type != "reference":
                self.outputs[name].name = (
                    "{0}->".format(prefix) + self.outputs[name].name)

    ###########################################################################
    # Private Members
    ###########################################################################

    def _build_expression(self):
        """ Build an expression and namespace in order to execute the function
        attached to this bbox.
        """
        # Get the function parameters and retunred values
        inputs = inspect.getargspec(self._func).args
        code = inspect.getsourcelines(self._func)
        return_pattern = r"return\s*(.*)\n*$"
        outputs = re.findall(return_pattern, code[0][-1])

        # Build the expression namespace
        namespace = {"function": self._func}

        # Deal with all function input parameters
        kwargs = []
        for control_name in inputs:

            # Check input function parameter has been declared on the bbox
            if control_name not in self.inputs.controls:
                raise Exception(
                    "Impossible to execute Bbox '{0}': function input "
                    "parameter '{1}' has not been defined in function '<{2}>' "
                    "description.".format(self.id, control_name, self.xml_tag))
            # Update namespace
            namespace[control_name] = getattr(self.inputs, control_name).value
            # Create kwargs
            kwargs.append("{0}={0}".format(control_name))

        # Deal with all function returned parameters
        for control_name in outputs:

            # Check returned function parameter has been declared on the bbox
            if control_name not in self.outputs.controls:
                raise Exception(
                    "Impossible to execute Bbox '{0}': function returned "
                    "parameter '{1}' has not been defined in function '<{2}>' "
                    "description.".format(self.id, control_name, self.xml_tag))
            # Update namespace
            namespace[control_name] = None

        # Build the function expression
        expression = "function({0})".format(", ".join(kwargs))

        # If we have some returned values, update the expression
        if outputs:
            return_expression = ", ".join(outputs)
            expression = "{0} = {1}".format(return_expression, expression)

        return namespace, expression

    def _load(self, funcdesc):
        """ Load the function from its description.

        Parameters
        ----------
        funcdesc: string (mandatory)
            a python function path relative to the module we want to decorate
            in a building box.

        Returns
        -------
        func: callable
            a python function we want to decorate in a building box.
        """
        # Get the module and function names
        funcdesc_elts = funcdesc.split(".")
        module_name = ".".join(funcdesc_elts[:-1])
        func_name = funcdesc_elts[-1]

        # Get the absolute path the the xml file description
        # COMPATIBILITY: module not defined in python 2.6
        python_version = sys.version_info
        if python_version[:2] <= (2, 6):
            __import__(module_name)
        else:
            importlib.import_module(module_name)
        module = sys.modules[module_name]

        return getattr(module, func_name)

    def _set_controls(self):
        """ Define the bbox input and output parameters. Each parameter is
        a control defined in 'casper.lib.controls'.

        Expected control attibutes are: 'type', 'name', 'description', 'from',
        'role'.
        """
        # Get the function default values
        args = inspect.getargspec(self._func)
        defaults = dict(zip(reversed(args.args or []),
                            reversed(args.defaults or [])))

        # Go through all controls defined in the function prototype
        shared_output_controls = []
        for desc in self.proto:

            # Detect shared output controls
            if "from" in desc and desc["role"] == "output":
                shared_output_controls.append(desc["from"])
                continue

            # Get the control type and description
            control_type = desc.get("type", None)
            if control_type is None:
                raise Exception("Impossible to warp Bbox '{0}': control type "
                                "undefined.".format(self.id))
            control_desc = desc.get("description", "")
            control_name = desc.get("name", None)
            if control_name is None:
                raise Exception("Impossible to warp Bbox '{0}': control name "
                                "undefined.".format(self.id))
            control_content = desc.get("content", None)

            # Check if the control type is valid
            if control_type in controls:

                # Create the control
                control = controls[control_type](
                    desc=control_desc, content=control_content)
                control.name = control_name
                if control_name in defaults:
                    control.optional = True
                    control.value = defaults[control_name]

                # Split output controls
                if desc["role"] == "output":
                    control.type = "output"
                    setattr(self.outputs, control_name, control)

                # And input controls
                else:
                    control.type = "input"
                    setattr(self.inputs, control_name, control)

            # Raise an exception otherwise
            else:
                raise Exception(
                    "Impossible to warp Bbox '{0}': unknown control type "
                    "'{1}', expect one in {2}.".format(self.id, control_type,
                                                       controls.keys()))

        # Deal with shared output controls
        for input_control_name in shared_output_controls:
            if input_control_name in self.inputs.controls:
                control = self.inputs[input_control_name]
                control.type = "reference"
                setattr(self.outputs, input_control_name, control)
            else:
                raise Exception(
                    "Impossible to warp Bbox '{0}': unknown input control "
                    "'{1}' detected in shared output creation.".format(
                        self.id, input_control_name))
