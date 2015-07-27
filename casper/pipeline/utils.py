#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import os

# Xml import
import xml.dom.minidom
from casper.lib.base.xmltodict import xmltodict

# Casper import
from casper.lib.controls import Base


class ControlObject(object):
    """ Dummy class for controls.
    """
    def __init__(self):
        """ Initilaize the ControlObject class.
        """
        self.controls = []

    def __getitem__(self, name):
        """ Return a control when an item is asked.

        Parameters
        ----------
        name: string (mandatory)
            the name of the control we want to acess.
        """
        if name in self.controls:
            return getattr(self, name)
        else:
            raise ValueError(
                "'{0}' is not a valid control name. Controls available are "
                "{1}.".format(name, self.controls))

    def __setattr__(self, name, value):
        """ When a new attribute is set, store the attribute name in the
        'controls'.
        When the attribute is a control set the new value to the control value
        attribute.

        Parameters
        ----------
        name: string (mandatory)
            the name of the attribute to set.
        value: object (mandatory)
            the value of the attribute to set.
        """
        # Store attribute names
        if hasattr(self, "controls") and name not in self.controls:
            self.controls.append(name)
        elif isinstance(value, Base):
            raise ValueError(
                "A control named '{0}' is already registered.".format(name))

        # Control special case
        if hasattr(self, name):
            self.__getattribute__(name).value = value

        # Default case
        else:
            super(ControlObject, self).__setattr__(name, value)


def title_for(title):
    """ Create a title from an underscore-separated string.

    Parameters
    ----------
    title: str (mandatory)
        the string to format.

    Returns
    -------
    out: str
        the formated string.
    """
    return title.replace("_", " ").title().replace(" ", "")


def parse_docstring(docstring):
    """ Parse the given docstring to get the <unit> xml-like structure.

    Parameters
    ----------
    docstring: str (mandatory)
        a string where we will try to found the <process> xml-like structure.

    Returns
    -------
    parameters: dict
        the process trait descriptions.
    """
    # Find the <process> xml-like structure in the docstring
    capsul_start = docstring.rfind("<unit>")
    capsul_end = docstring.rfind("</unit>")
    capsul_description = docstring[
        capsul_start: capsul_end + len("</unit>")]

    # Parse the xml structure and put each xml dictionnary formated item in a
    # list
    parameters = []

    # If no description has been found in the doctring, return an empty
    # parameter list
    if not capsul_description:
        return parameters

    # Find all the xml 'input', 'output' and 'return' tag elements
    document = xml.dom.minidom.parseString(capsul_description)
    for node in document.childNodes[0].childNodes:

        # Assert we have an 'item' node
        if (node.nodeType != node.ELEMENT_NODE or
                node.tagName not in ["input", "output"]):
            continue

        # Set each xml 'item' tag element in the parameter list
        parameters.append(
            dict(node.attributes.items() + [("role", node.tagName)]))

    return parameters


def load_xml_description(xmlfile):
    """ Load the given xml description.

    Parameters
    ----------
    xmlfile: string (mandatory)
        a file containing a xml formated description.

    Returns
    -------
    desc: dict
        the loaded xml structure description.
    """
    # Check that a valid description file has been specified
    if not os.path.isfile(xmlfile):
        raise IOError("The input xml description '{0}' is not a valid "
                      "file.".format(xmlfile))

    # Parse the xml file
    with open(xmlfile) as open_description:
        desc = xmltodict(open_description.read())

    return desc
