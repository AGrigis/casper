#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################


def a_function_to_wrap(fname, directory="dsfds"):
    """ A dummy function that just print all its parameters.

    <unit>
        <output name="string" type="Str" description="test" />
        <output from="fname" />
        <input name="fname" type="File" description="test" />
        <input name="directory" type="Directory" description="test" />
    </unit>
    """
    string = "-".join([repr(fname), repr(directory)])
    fname = "toto"
    return string


def clothing(inp):
    """ A dummy function the just copy the input to the output.

    <unit>
        <output name="outp" type="Str" description="test" />
        <input name="inp" type="Str" description="test" />
    </unit>
    """
    outp = inp
    return outp


def clothing_inputs(listinp):
    """ A dummy function the just concatenate the list inputs to the output.

    <unit>
        <output name="outp" type="Str" description="test" />
        <input name="listinp" type="List" content="Str" description="test" />
    </unit>
    """
    outp = "".join(listinp)
    return outp


def clothing_outputs(inp):
    """ A dummy function the just duplicate the input to the output.

    <unit>
        <output name="listoutp" type="List" content="Str" description="test" />
        <input name="inp" type="Str" description="test" />
    </unit>
    """
    if inp is None:
        return None
    listoutp = [inp + "0", inp + "1"]
    return listoutp
