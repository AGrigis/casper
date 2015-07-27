#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################


def is_io_control(controldesc):
    """ Check if the control description is attached to the pipeline
    inputs/outputs.

    A pbox input/output control is specified as '<pbox_control>' while a
    pbox inner box control is specified as '<box_name>.<box_control_name>'.

    Parameters
    ----------
    controldesc: string (mandatory)
        a control description.

    Returns
    -------
    is_pbox_control: bool
        True if a pbox input/output control is detected.
    """
    if "." not in controldesc:
        return True
    else:
        return False


def parse_link(linkrep):
    """ Parse a box link.

    Parameters
    ----------
    linkrep: str (mandatory)
        a link representation of the form
        'box_from.control_name->box_to.input_control_name' or
        'input_control_name->box_to.input_control_name' or
        'box_from.output_control_name->output_control_name'

    Returns
    -------
    output: 4-uplet
        tuple containing the source/destination box name and control.
        A pbox name is virtually represented by ''.


    """
    # Split source and destination descriptions
    src, dest = linkrep.split("->")

    # Parse the source and destination control descriptions
    src_box_name, src_control_name = parse_controldesc(src)
    dest_box_name, dest_control_name = parse_controldesc(dest)

    return src_box_name, src_control_name, dest_box_name, dest_control_name


def parse_controldesc(controldesc):
    """ Parse a control description.

    Parameters
    ----------
    controldesc: str (mandatory)
        the description plug we want to load 'node.plug'

    Returns
    -------
    box_name: string
        the box name.
    control_name: string
        the associated control name.
    """
    # Parse the plug description
    dot = controldesc.find(".")

    # Check if its a pbox input/output control
    if dot < 0:
        box_name = ""
        control_name = controldesc
    else:
        box_name = controldesc[:dot]
        control_name = controldesc[dot + 1:]

    return box_name, control_name
