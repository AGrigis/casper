#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import sys
import os
import json
try:
    import importlib
except:
    pass
import time
import multiprocessing
import logging

# Casper import
import casper
from casper.lib.base import Graph
from casper.lib.base import GraphNode
from casper.lib.controls import controls
from .bbox import Bbox
from .ibox import Ibox
from .utils import ControlObject
from .utils import load_xml_description
from .utils import title_for
from .link_parser import is_io_control
from .link_parser import parse_link


# Define the logger
logging.basicConfig(format="%(message)s", level=logging.INFO)
multiprocessing.log_to_stderr(logging.CRITICAL)
logger = logging.getLogger(__name__)


class Pbox(object):
    """ A pipeline box that defines organized processing steps.
    """
    xml_tag = "pipeline"
    box_tag = "units"
    box_names = ["unit", "switch"]
    unit_attributes = ["name", "module", "set", "iterinput", "iteroutput"]
    unit_set = ["name", "value"]
    unit_iter = ["name"]
    switch_attributes = ["name", "path"]
    switch_path = ["name", "unit"]
    link_tag = "links"
    link_attributes = ["source", "destination"]

    def __init__(self, xmldesc):
        """ Initilaize the Pbox class.

        Parameters
        ----------
        xmldesc: string (mandatory)
            the path to a xml pipeline description. The path is relative
            to the module.
        """
        # Define class parameters
        self._xmlfile, module_name, xmlfile_name = self._load(xmldesc)
        self._boxes = {}
        self._links = []
        self._switches = {}
        self.inputs = ControlObject()
        self.outputs = ControlObject()
        self.active = True

        # Create the bbox name
        self.id = module_name + "." + title_for(xmlfile_name.split(".")[0])

        # Get the function to decorate prototype
        self.proto = load_xml_description(self._xmlfile)

        # Create the input and output controls
        self._create_pipeline()

    def __call__(self, cpus=1, timer=1):
        """ Execute the AutoProcess class.
        """
        # Information
        logger.info("Using 'casper' version '{0}'.".format(casper.__version__))
        exit_rules = [
            "For exitcode values:",
            "    = 0 - no error was produced.",
            "    > 0 - the process had an error, and exited with that code.",
            "    < 0 - the process was killed with a signal of -1 * exitcode."]
        logger.info("\n".join(exit_rules))
        logger.info("-" * 10)

        # Create an execution graph
        exec_graph, _, _ = self._create_graph(self, filter_inactive=True)

        # Get the machine available cpus
        nb_cpus = multiprocessing.cpu_count() - 1
        nb_cpus = nb_cpus or 1
        if max(cpus, nb_cpus) == cpus:
            cpus = nb_cpus

        # The worker function of a bbox, invoked in a Process.
        def bbox_worker(bbox, workers_returncode):
            box_name = multiprocessing.current_process().name
            bbox_returncode = bbox(box_name)
            workers_returncode.put(bbox_returncode)
            workers_returncode

        # Execute the boxes respecting the graph order
        # Use a FIFO strategy to deal with multiple boxes
        iter_map = {}
        self._update_graph(exec_graph, iter_map)
        toexec_box_names = self._available_boxes(exec_graph)
        exec_queue = []
        global_counter = 1
        workers_returncode = multiprocessing.Queue()
        wave_boxes = {}
        returncode = {}
        while toexec_box_names != [] or exec_queue != []:

            # Check which deamons are still alive and clean others
            # Update also the iterative mapping queue
            to_remove_indices = []
            process_exitcodes = {}
            for index, process in enumerate(exec_queue):
                if not process.is_alive():
                    (identifier, box_name, box_exec_name,
                     box_iter_name, iteration) = Pbox.split_name(process.name)
                    if box_iter_name in iter_map:
                        position = iter_map[box_iter_name].index(box_name)
                        iter_map[box_iter_name].pop(position)
                    to_remove_indices.append(index)
                    process.join()
                    process_exitcodes[process.name] = process.exitcode

            for index in reversed(to_remove_indices):
                process = exec_queue.pop(index)

            # Update execution list
            if len(to_remove_indices) > 0:

                # Collect the boxes returncodes
                wave_returncode = {}
                for index in range(workers_returncode.qsize()):
                    wave_returncode.update(workers_returncode.get_nowait())
                for process_name, exitcode in process_exitcodes.items():
                    wave_returncode[process_name]["exitcode"] = exitcode
                returncode.update(wave_returncode)

                # Update the called boxes outputs and the graph
                for process_item in sorted(wave_returncode.items()):
                    process_name, process_returncode = process_item
                    (identifier, box_name, box_exec_name,
                     box_iter_name, iteration) = Pbox.split_name(process_name)
                    if box_iter_name is not None:
                        ibox = exec_graph.find_node(box_iter_name).meta
                    box = wave_boxes.pop(box_name)
                    exec_graph.remove_node(box_name)
                    for name, value in process_returncode["outputs"].items():
                        if box_iter_name is not None:
                            ibox.update_iteroutputs(name, value, iteration)
                        setattr(box.outputs, name, value)

                    # Information
                    for key, value in process_returncode.items():
                        logger.info("{0}.{1} = {2}".format(
                            process_name, key, value))
                    logger.info("-" * 10)

                # Destroy executed iterative boxes
                for box_name, item in iter_map.items():
                    if item == []:
                        iter_map.pop(box_name)
                        exec_graph.remove_node(box_name)

                # Update nnil boxes list
                self._update_graph(exec_graph, iter_map)
                new_toexec_box_names = set(self._available_boxes(exec_graph))
                toexec_box_names.extend(
                    new_toexec_box_names.difference(toexec_box_names))

            # Execute deamon processes
            for index in range(cpus):

                # Check if we have reached the maximum capacitites
                if len(exec_queue) == cpus or toexec_box_names == []:
                    break

                # Get a box to be processed
                box_name = toexec_box_names.pop(0)

                # Execute the box as a deamon process
                process_name = "{0}-{1}".format(global_counter, box_name)
                box = exec_graph.find_node(box_name).meta
                wave_boxes[box_name] = box
                process = multiprocessing.Process(
                    name=process_name, target=bbox_worker,
                    args=(box, workers_returncode))
                process.deamon = True
                process.start()
                exec_queue.append(process)
                global_counter += 1

            # Use a delay
            time.sleep(timer)

    ###########################################################################
    # Public Members
    ###########################################################################

    @staticmethod
    def split_name(process_name):
        """ Split a process name.

        Parameters
        ----------
        identifier: int
            the execution identifier.
        box_name: str
            the box name.
        box_exec_name: str
            if an iterative box is detected returned his execution id,
            None otherwise.
        box_iter_name: str
            if an iterative box is detected returned his id, None otherwise.
        iteration: int
            if an iterative box is detected returned his iteration number,
            None otherwise.
        """
        identifier, box_name = process_name.split("-")
        identifier = int(identifier)
        if Ibox.itersep in box_name:
            box_exec_name = box_name.split(".")[0]
            box_iter_name, iteration = box_exec_name.split(Ibox.itersep)
            iteration = int(iteration)
        else:
            box_exec_name = None
            box_iter_name = None
            iteration = None
        return identifier, box_name, box_exec_name, box_iter_name, iteration

    ###########################################################################
    # Private Members
    ###########################################################################

    def _available_boxes(self, graph):
        """ List the boxes that have no incoming link.

        Parameters
        ----------
        graph: Graph
            a graph.

        Returns
        -------
        avalible_boxes: list of str
            a list of boxes ready for execution.
        """
        return sorted([node.name for node in graph.available_nodes()
                      if not isinstance(node.meta, Ibox)])

    def _update_graph(self, graph, iter_map, prefix=""):
        """ Dynamically update the graph representtion of the pipeline.

        Update the 'iter_map' dictionary with the built iterative
        processings.
        An iterative processing is added as an independant graph in the main
        graph.

        Parameters
        ----------
        graph: Graph
            the updated graph representation.
        iter_map: dict
            the dictionary containing a mapping between all the ibox names
            and executed box names and associated ibox.
        prefix: str (optional, default '')
            a prefix for the box names.
        """
        # Go through nnil nodes
        for node in graph.available_nodes():

            # Deal with ibox only
            box_name = node.name
            if isinstance(node.meta, Ibox) and box_name not in iter_map:

                # Construct the itarative graphs
                itergraphs = node.meta.itergraphs(box_name)
                if itergraphs == {}:
                    raise ValueError("IBox '{0}' can't be executed.".format(
                        box_name))

                # Update the input graph and the execution list
                iter_map[box_name] = []
                for itername, itergraph in itergraphs.items():
                    graph.add_graph(itergraph)
                    iter_map[box_name].extend(
                        [node.name for node in itergraph._nodes.values()])

    def _create_graph(self, box, prefix="", flatten=True, add_io=False,
                      filter_inactive=False):
        """ Create a graph repesentation of a box.

        Parameters
        ----------
        box: Pbox or Bbox (mandatory)
            a box from which we want to extract the graph representation.
        prefix: str (optional, default '')
            a prefix for the box names.
        flatten: bool (optional, default True)
            If True iterate through the sub-graph structures.
        add_io: bool (optional, default False)
            If True add the 'inputs' and 'outputs' nodes.
        filter_inactive: bool (optional, default False)
            If True filter inactive boxes.

        Returns
        -------
        graph: Graph
            a graph representation of the input box.
        """
        # Add the graph nodes
        graph = Graph()
        pboxes = {}
        for box_name in list(box._boxes.keys()):
            inner_box = box._boxes[box_name]
            if filter_inactive and not inner_box.active:
                continue
            if isinstance(inner_box, Pbox):
                if flatten:
                    inner_prefix = prefix + "{0}.".format(box_name)
                    sub_graph, inlinkreps, outlinkreps = self._create_graph(
                        inner_box, inner_prefix,
                        filter_inactive=filter_inactive)
                    graph.add_graph(sub_graph)
                    pboxes[box_name] = (sub_graph, inlinkreps, outlinkreps)
                else:
                    graph.add_node(GraphNode(prefix + box_name, inner_box))
            elif isinstance(inner_box, Bbox) or isinstance(inner_box, Ibox):
                graph.add_node(GraphNode(prefix + box_name, inner_box))
            else:
                raise ValueError(
                    "'{0}' is not a valid box type. Allowed types are '{1}', "
                    "'{2}' or '{3}'.".format(type(inner_box), Bbox, Pbox,
                                             Ibox))

        # Add io nodes if requested
        if add_io:
            graph.add_node(GraphNode(prefix + "inputs", None))
            graph.add_node(GraphNode(prefix + "outputs", None))

        # Add the graph links
        input_linkreps = {}
        output_linkreps = {}
        for linkrep in box._links:

            # Parse link
            src_box_name, src_ctrl, dest_box_name, dest_ctrl = parse_link(
                linkrep)

            # Pbox special case: flatening
            if src_box_name in pboxes:
                src_box_name = "{0}.{1}".format(
                    src_box_name, pboxes[src_box_name][2][src_ctrl][0])
            if dest_box_name in pboxes:
                dest_box_name = "{0}.{1}".format(
                    dest_box_name, pboxes[dest_box_name][1][dest_ctrl][0])

            # Add an inner link, skip inpout/output links, check that no
            # inactive box is involved in this link
            if src_box_name == "":
                input_linkreps[src_ctrl] = (dest_box_name, dest_ctrl)
                if add_io:
                    graph.add_link(prefix + "inputs", prefix + dest_box_name)
            elif dest_box_name == "":
                output_linkreps[dest_ctrl] = (src_box_name, src_ctrl)
                if add_io:
                    graph.add_link(prefix + src_box_name, prefix + "outputs")
            elif (filter_inactive and (
                    prefix + src_box_name not in graph._nodes or
                    prefix + dest_box_name not in graph._nodes)):
                continue
            else:
                graph.add_link(prefix + src_box_name, prefix + dest_box_name)
        return graph, input_linkreps, output_linkreps

    def _load(self, xmldesc):
        """ Load the function from its description.

        Parameters
        ----------
        xmldesc: string (mandatory)
            the path to a xml pipeline description. The path is relative
            to the module.

        Returns
        -------
        xmlfile: string
           the absolute path to the xml pipeline description.
        """
        # Check the description extension
        if not xmldesc.endswith(".xml"):
            raise IOError(
                "A pipeline box is created from an 'xml' file. File "
                "'{0}' has not the proper extension.".format(xmldesc))

        # Get the module and xml description file names
        xmldesc_elts = xmldesc.split(".")
        module_name = ".".join(xmldesc_elts[:-2])
        xmlfile_name = ".".join(xmldesc_elts[-2:])

        # Get the absolute path the the xml file description
        # COMPATIBILITY: module not defined in python 2.6
        python_version = sys.version_info
        if python_version[:2] <= (2, 6):
            __import__(module_name)
        else:
            importlib.import_module(module_name)
        module = sys.modules[module_name]
        xmlfile = os.path.join(os.path.dirname(module.__file__), xmlfile_name)

        return xmlfile, module_name, xmlfile_name

    def _create_pipeline(self):
        """ Create a pipeline from its description.
        """
        # Add boxes to the pipeline
        if self.box_tag not in self.proto:
            raise Exception(
                "Box defined in '{0}' has no '<{1}>' declared.".format(
                    self._xmlfile, self.box_tag))
        switch_descs = []
        for box_item in self.proto[self.box_tag]:
            for box_type in box_item.keys():

                # Create processing boxes (can be iterative)
                if box_type == self.box_names[0]:
                    for boxdesc in box_item[box_type]:
                        self._add_box(boxdesc)
                # Create switch boxes
                elif box_type == self.box_names[1]:
                    for switchdesc in box_item[box_type]:
                        switch_descs.append(switchdesc)
                # Unrecognize box type
                else:
                    raise ValueError(
                        "Box structure: '{0}' defined in '{1}' is not "
                        "supported. Supported boxes are '{2}'.".format(
                            json.dumps(box_item, indent=2), self._xmlfile,
                            self.box_names))

        # Add switch to the pipeline
        for switchdesc in switch_descs:
            self._add_switch(switchdesc)

        # Add links between boxes
        if self.link_tag not in self.proto:
            raise Exception(
                "Box defined in '{0}' has no '<{1}>' declared.".format(
                    self._xmlfile, self.link_tag))
        for link_item in self.proto[self.link_tag]:
            inner_tag = self.link_tag[:-1]
            for linkdesc in link_item[inner_tag]:
                if is_io_control(linkdesc[self.link_attributes[0]]):
                    linktype = "input"
                elif is_io_control(linkdesc[self.link_attributes[1]]):
                    linktype = "output"
                else:
                    linktype = "link"
                self._add_link(linkdesc, linktype)

    def _add_switch(self, switchdesc):
        """ Add a switch in the pipeline from its description.

        Parameters
        ----------
        switchdesc: dict
            the description of the switch we want to insert in the pipeline.
        """
        # Check switch definition parameters
        switch_attributes = list(switchdesc.keys())
        if not set(switch_attributes).issubset(self.switch_attributes):
            raise ValueError(
                "Switch definition: '{0}' defined in '{1}' is not supported. "
                "Supported switch parameters are '{2}'.".format(
                    json.dumps(switchdesc, indent=2), self._xmlfile,
                    self.switch_attributes))
        for mandatory_parameter in self.switch_attributes[:2]:
            if mandatory_parameter not in switch_attributes:
                raise ValueError(
                    "A '{0}' parameter is required in switch definition: "
                    "'{1}' defined in '{2}'.".format(
                        mandatory_parameter, json.dumps(switchdesc, indent=2),
                        self._xmlfile))

        # Check the name of the switch is not already reserved
        switch_name = switchdesc[self.switch_attributes[0]][0]
        if switch_name in self._switches:
            raise ValueError(
                "The switch name '{0}' defined in '{1}' is "
                "already used.".format(switch_name, self._xmlfile))

        # Create the switch control
        switch_paths = {}
        for pathdesc in switchdesc[self.switch_attributes[1]]:
            path_name = pathdesc[self.switch_path[0]][0]
            path_boxes = [box[self.unit_attributes[0]]
                          for box in pathdesc[self.switch_path[1]]]
            switch_paths[path_name] = path_boxes
        switch_keys = list(switch_paths.keys())
        control = controls["Enum"](
            choices=tuple(switch_keys),
            switch_name=switch_name,
            desc=("Switch between paths '{0}:{1}' defined in pipeline '{2}'"
                  ".".format(switch_name, "-".join(switch_keys), self.id)))
        setattr(self.inputs, switch_name, control)
        self._switches[switch_name] = switch_paths
        control.add_observer("value", self._update_activation)
        control.value = switch_keys[0]

    def _update_activation(self, signal):
        """ Define an observer method that will update the selected switch
        associated box activations.

        Parameters
        ----------
        signal: SignalObject (mandatory)
            a signal object with a 'value' and 'switch_name' attributes.
        """
        # Desactivate the selected switch boxes and activate only the selected
        # path associated boxes
        if hasattr(signal, "value") and hasattr(signal, "switch_name"):
            switch_paths = self._switches[signal.switch_name]
            for path_name, box_names in switch_paths.items():
                for box_name in box_names:
                    self._boxes[box_name].active = (path_name == signal.value)
        else:
            raise ValueError(
                "Updating pipeline activation '{0}'. Activation error: "
                "observer signal has no attribute 'value'.".format(self.name))

    def _add_box(self, boxdesc):
        """ Add a box in the pipeline from its description.

        Parameters
        ----------
        boxdesc: dict
            the description of the box we want to insert in the pipeline.
        """
        # Check box definition parameters
        box_attributes = list(boxdesc.keys())
        if not set(box_attributes).issubset(self.unit_attributes):
            raise ValueError(
                "Box definition: '{0}' defined in '{1}' is not supported. "
                "Supported box parameters are '{2}'.".format(
                    json.dumps(boxdesc, indent=2), self._xmlfile,
                    self.unit_attributes))
        for mandatory_parameter in self.unit_attributes[:2]:
            if mandatory_parameter not in box_attributes:
                raise ValueError(
                    "A '{0}' parameter is required in box definition: '{1}' "
                    "defined in '{2}'.".format(
                        mandatory_parameter, json.dumps(boxdesc, indent=2),
                        self._xmlfile))

        # Check the name of the new box is not already reserved
        box_name = boxdesc[self.unit_attributes[0]][0]
        if box_name in self._boxes:
            raise ValueError("The box name '{0}' defined in '{1}' is already "
                             "used.".format(box_name, self._xmlfile))

        # Instanciate the new box
        box_module = boxdesc[self.unit_attributes[1]][0]
        iterinputs = boxdesc.get(self.unit_attributes[3], [])
        iteroutputs = boxdesc.get(self.unit_attributes[4], [])
        if iterinputs != [] or iteroutputs != []:
            iterinputs = [item["name"] for item in iterinputs]
            iteroutputs = [item["name"] for item in iteroutputs]
            box = Ibox(box_module, iterinputs, iteroutputs)
        elif box_module.endswith(".xml"):
            box = Pbox(box_module)
        else:
            box = Bbox(box_module)
            box.update_control_names(box_name)
        self._boxes[box_name] = box

        # Set the new box default parameters
        set_tag = self.unit_attributes[2]
        if set_tag in box_attributes:
            for box_defaults in boxdesc[set_tag]:

                # Check the proper lexic has been specified
                if not set(box_defaults.keys()).issubset(self.unit_set):
                    raise ValueError(
                        "Box attribute definition: '{0}' defined in '{1}' is "
                        "not supported. Supported attributes are "
                        "'{2}'.".format(
                            list(box_defaults.keys()), self._xmlfile,
                            self.unit_set))

                # Set the input or output default paramters
                box_pname = box_defaults[self.unit_set[0]]
                box_pvalue = eval(box_defaults[self.unit_set[1]])
                if box_pname in self._boxes[box_name].inputs.controls:
                    control = getattr(self._boxes[box_name].inputs, box_pname)
                elif box_pname in self._boxes[box_name].outputs.controls:
                    control = getattr(self._boxes[box_name].outputs, box_pname)
                else:
                    raise ValueError(
                        "The parameter '{0}' is not defined in the box "
                        "'{1}' input or output parameters.".format(
                            box_pname, box_name))
                control.optional = True
                control.value = box_pvalue

    def _add_link(self, linkdesc, linktype="link"):
        """ Link box parameters.

        A link is always defined from a source control to a destination
        control.

        Parameters
        ----------
        linkdesc: dict
            the description of the link we want to insert in the pipeline.
        linktype: string
            the link type: 'link', 'input' or 'output'.
        """
        # Check the proper lexic has been specified
        link_keys = list(linkdesc.keys())
        issubset = set(link_keys).issubset(self.link_attributes)
        if len(link_keys) != 2 or not issubset:
            raise ValueError(
                "Box attribute definition: '{0}' defined in '{1}' is "
                "not supported. Supported attributes are "
                "'{2}'.".format(
                    json.dumps(list(linkdesc.keys())), self._xmlfile,
                    self.link_attributes))

        # Deal with input/output pipeline link
        # In this case the inner box control is registered as an input/output
        # control of the pipeline
        source = linkdesc[self.link_attributes[0]]
        destination = linkdesc[self.link_attributes[1]]
        linkrep = "{0}->{1}".format(source, destination)
        if linktype == "output":
            setattr(
                self.outputs, destination, self._get_control(source, False))
        elif linktype == "input":
            if source not in self.inputs.controls:
                setattr(
                    self.inputs, source, self._get_control(destination, True))
            else:
                src_control = self._get_control(source, False)
                dest_control = self._get_control(destination, True)
                src_control.add_observer("value", dest_control._update_value)
        # Deal with inner pipeline link
        # In this case an observer is registered on the source control that
        # updates the output control when some changes occured.
        elif linktype == "link":
            src_control = self._get_control(source, False)
            dest_control = self._get_control(destination, True)
            src_control.add_observer("value", dest_control._update_value)
        else:
            raise ValueError("Unrecognized link type '{0}'.".format(linktype))

        # Save the link description
        self._links.append(linkrep)

    def _get_control(self, linkdesc, is_input):
        """ Get a control in the pipeline from its description.

        Parameters
        ----------
        linkdesc: string (mandatory)
            a control desription of the form '<box_name>.<control_name>' or
            '<control_name>' for the current pipeline controls
        is_input: bool (mandatory)
            varible telling us if we are searching for an input or an output
            control. In the case of a pipeline control, the meaning of this
            variable is inverted.

        Returns
        -------
        control: capser.lib.controls
            the desired pipeline control.
        """
        # Get the control description
        controldesc = linkdesc.split(".")

        # Check the control description is valid
        if len(controldesc) not in [1, 2]:
            raise ValueError(
                "Box source/destination link '{0}' defined in '{2}' has an "
                "undefined format. Supported format is "
                "'<box_name>.<control_name>' or '<control_name>' for the "
                "current pipeline parameters.".format(
                    controldesc, self._xmlfile))

        # Get the box that contains the control of interest
        if len(controldesc) == 1:
            is_input = not is_input
            control_name = controldesc[0]
            box = self
        else:
            box_name, control_name = controldesc
            box = self._boxes[box_name]

        # Get the control of interest
        if is_input:
            control = box.inputs[control_name]
        else:
            control = box.outputs[control_name]

        return control
