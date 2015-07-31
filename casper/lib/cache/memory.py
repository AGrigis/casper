#! /usr/bin/env python
##########################################################################
# CASPER - Copyright (C) AGrigis, 2013
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
#
# Based on the nipype memory code: http://nipy.sourceforge.net/nipype/
##########################################################################

# System import
from __future__ import with_statement
import os
import hashlib
import time
import shutil
import json
import numpy
import logging

# Define the logger
logger = logging.getLogger(__name__)


###########################################################################
# Proxy box objects
###########################################################################

class UnMemorizedBox(object):
    """ This class replaces MemorizedBox when there is no cache.
    It provides an identical API but does not write anything on disk.
    """
    def __init__(self, box, verbose=1):
        """ Initialize the UnMemorizedBox class.

        Parameters
        ----------
        box: a box
            the box instance to wrap.
        verbose: int
            if different from zero, print console messages.
        """
        self.box = box
        self.verbose = verbose

    def __call__(self, *args, **kwargs):
        """ Call the box.

        Parameters
        ----------
        kwargs: dict (optional)
            should correspond to the declared box parameters.
        """
        # Set the box inputs early to get some argument checking
        for name, value in kwargs.items():
            if name in self.box.inputs.controls:
                setattr(self.box.inputs, name, value)
        input_parameters = self._get_box_arguments()

        # Information message
        if self.verbose != 0:
            print("{0}\n[NoMemory] Calling {1}...\n{2}".format(
                80 * "_", self.box.id,
                get_box_signature(self.box, input_parameters)))

        # Start a timer
        start_time = time.time()

        # Execute the box
        result = self.box(*args, **kwargs)
        duration = time.time() - start_time

        # Information message
        if self.verbose != 0:
            msg = "{0:.1f}s, {1:.1f}min".format(duration, duration / 60.)
            print(max(0, (80 - len(msg))) * '_' + msg)

        return result

    def _get_box_arguments(self):
        """ Get the box arguments.

        Returns
        -------
        input_parameters: dict
            the box input parameters.
        """
        # Store for input parameters
        input_parameters = {}

        # Go through all the controls
        for control_name in self.box.inputs.controls:

            # Get the control
            control = getattr(self.box.inputs, control_name)

            # Store the input control value
            input_parameters[control_name] = control.value

        return input_parameters

    def __getattr__(self, name):
        """ Define behavior for when a user attempts to access an attribute
        of a UnMemorizedBox instance.

        __getattr__ is only invoked if the attribute wasn't found the usual
        ways, so we first check the UnMemorizedBox object and then the box
        object.

        Parameters
        ----------
        name: string
            the name of the parameter we want to access.
        """
        if hasattr(self.box, name):
            return getattr(self.box, name)
        else:
            raise AttributeError(
                "'UnMemorizedBox' and associated box objects have no "
                "attribute '{0}'".format(name))

    def __repr__(self):
        """ UnMemorizedBox class representation.
        """
        return "{0}({1})".format(self.__class__.__name__, self.box.id)


class MemorizedBox(object):
    """ Callable object decorating a box for caching its returned
    values each time it is called.

    All values are cached on the filesystem, in a deep directory
    structure. Methods are provided to inspect the cache or clean it.
    """
    def __init__(self, box, cachedir, timestamp=None, verbose=1):
        """ Initialize the MemorizedBox class.

        Parameters
        ----------
        box: a box
            the box instance to wrap.
        cachedir: string
            the directory in which the computation will be stored.
        timestamp: float (optional)
            The reference time from which times in tracing messages
            are reported.
        callback: callable (optional)
            an optional callable called each time after the function
            is called.
        verbose: int
            if different from zero, print console messages.
        """
        self.box = box
        self.verbose = verbose

        # Check the memory directory
        if isinstance(cachedir, str):
            if not os.path.isdir(cachedir):
                raise ValueError(
                    "'{0}' is not a valid cache directory.".format(cachedir))
            self.cachedir = cachedir
        else:
            raise ValueError("'cachedir' should be a string.")

        # Define the cache time
        if timestamp is None:
            timestamp = time.time()
        self.timestamp = timestamp

        # Set the documentation of the class
        self.__doc__ = self.box.__doc__

    def __call__(self, *args, **kwargs):
        """ Call wrapped box and cache result, or read cache if available.

        This function returns the wrapped function output and some metadata.
        The file parameters are copied if the associated controls have a 'copy'
        option set to True.

        Parameters
        ----------
        kwargs: dict (optional)
            should correspond to the declared box parameters.
        """
        # Set the box inputs early to get some argument checking
        for name, value in kwargs.items():
            if name in self.box.inputs.controls:
                setattr(self.box.inputs, name, value)

        # Create the destination folder and a unique id for the current
        # box
        box_dir, box_hash, input_parameters = self._get_box_id()

        # Execute the box
        if not os.path.isdir(box_dir):

            # Create the destination memory folder
            os.makedirs(box_dir)

            # Try to execute the box and if an error occured remove the
            # cache folder
            try:
                # Run and update the box output controls
                result = self._call_box(box_dir, input_parameters,
                                        *args, **kwargs)

                # Save the result files in the memory with the corresponding
                # mapping
                output_parameters = {}
                for control_name in self.box.outputs.controls:
                    # Get the control value
                    control = getattr(self.box.outputs, control_name)
                    if control.copy:
                        output_parameters[control_name] = control.value
                file_mapping = []
                self._copy_files_to_memory(output_parameters, box_dir,
                                           file_mapping)
                map_fname = os.path.join(box_dir, "file_mapping.json")
                with open(map_fname, "w") as open_file:
                    open_file.write(json.dumps(file_mapping))

            except:
                shutil.rmtree(box_dir)
                raise

        # Restore the box results from the cache folder
        else:
            # Restore the memorized files
            map_fname = os.path.join(box_dir, "file_mapping.json")
            with open(map_fname) as json_data:
                file_mapping = json.load(json_data)

            # Go through all mapping files
            for workspace_file, memory_file in file_mapping:

                # Determine if the workspace directory is writeable
                if os.access(os.path.dirname(workspace_file), os.W_OK):
                    shutil.copy2(memory_file, workspace_file)
                else:
                    raise Exception(
                        "Can't restore file '{0}', access rights are "
                        "not sufficients.".format(workspace_file))

            # Update the box output traits
            result = self._load_box_result(box_dir, input_parameters)

        return result

    def _copy_files_to_memory(self, python_object, box_dir, file_mapping):
        """ Copy file items inside the memory.

        Parameters
        ----------
        python_object: object
            a generic python object.
        box_dir: str
            the box memory path.
        file_mapping: list of 2-uplet
            store in this structure the mapping between the workspace and the
            memory (workspace_file, memory_file).
        """
        # Deal with dictionary
        if isinstance(python_object, dict):
            for val in python_object.values():
                if val is not None:
                    self._copy_files_to_memory(val, box_dir, file_mapping)

        # Deal with tuple and list
        elif isinstance(python_object, (list, tuple)):
            for val in python_object:
                if val is not None:
                    self._copy_files_to_memory(val, box_dir, file_mapping)

        # Otherwise start the copy if the object is a file
        else:
            if (python_object is not None and
                    isinstance(python_object, str) and
                    os.path.isfile(python_object)):
                fname = os.path.basename(python_object)
                out = os.path.join(box_dir, fname)
                shutil.copy2(python_object, out)
                file_mapping.append((python_object, out))

    def _call_box(self, box_dir, input_parameters, *args, **kwargs):
        """ Call a box.

        Parameters
        ----------
        box_dir: string
            the directory where the cache has been written.
        input_parameters: dict
            the box input parameters.

        Returns
        -------
        result: dict
            the box results.
        """
        # Information message
        if self.verbose != 0:
            print("{0}\n[Memory] Calling {1}...\n{2}".format(
                80 * "_", self.box.id,
                get_box_signature(self.box, input_parameters)))

        # Start a timer
        start_time = time.time()

        # Execute the box
        result = self.box(*args, **kwargs)
        duration = time.time() - start_time

        # Save the result in json format
        json_data = json.dumps(result, sort_keys=True,
                               check_circular=True, indent=4,
                               cls=MemoryResultEncoder)
        result_fname = os.path.join(box_dir, "result.json")
        with open(result_fname, "w") as open_file:
            open_file.write(json_data)

        # Information message
        if self.verbose != 0:
            msg = "{0:.1f}s, {1:.1f}min".format(duration, duration / 60.)
            print(max(0, (80 - len(msg))) * '_' + msg)

        return result

    def _load_box_result(self, box_dir, input_parameters):
        """ Load the result of a box.

        Parameters
        ----------
        box_dir: string
            the directory where the cache has been written.
        input_parameters: dict
            the box input parameters.

        Returns
        -------
        result: dict
            the box cached results.
        """
        # Display an information message
        if self.verbose != 0:
            print("[Memory]: Loading {0}...".format(
                get_box_signature(self.box, input_parameters)))

        # Load the box result
        result_fname = os.path.join(box_dir, "result.json")
        if not os.path.isfile(result_fname):
            raise KeyError(
                "Non-existing cache value (may have been cleared). "
                "File '{0}' does not exist.".format(result_fname))
        with open(result_fname) as json_data:
            result = json.load(json_data, cls=MemoryResultDecoder)

        # Update the box output traits
        for name, value in list(result.values())[0]["outputs"].items():
            setattr(self.box.outputs, name, value)

        return result

    def _get_box_id(self, **kwargs):
        """ Return the directory in which are persisted the result of the
        box called with the given arguments.

        Returns
        -------
        box_dir: string
            the directory where the cache should be write.
        box_hash: string
            the box md5 hash.
        input_parameters: dict
            the box input parameters.
        """
        # Get the box id
        box_hash, input_parameters = self._get_argument_hash()
        box_dir = os.path.join(self._get_box_dir(), box_hash)

        return box_dir, box_hash, input_parameters

    def _get_argument_hash(self):
        """ Get a hash of the box arguments.

        Some parameters are not considered during the hash computation:
            * if the parameter value is not defined
            * if the control has an attribute 'nohash'

        Add the tool versions to check roughly if the running codes have
        changed.

        Returns
        -------
        box_hash: string
            the box md5 hash.
        input_parameters: dict
            the box input parameters.
        """
        # Store for input parameters
        input_parameters = {}
        box_parameters = {}

        # Go through all the controls
        for control_name in self.box.inputs.controls:

            # Get the control value
            control = getattr(self.box.inputs, control_name)
            value = control.value

            # Check specific flags before hash
            if has_attribute(control, "nohash", True, recursive=True):
                input_parameters[control_name] = value
                continue

            # Store the input parameter
            box_parameters[control_name] = value
            input_parameters[control_name] = value

        # Add the tool versions to check roughly if the running codes have
        # changed and add file path fingerprints
        box_parameters = self._add_fingerprints(box_parameters)

        # Generate the box hash
        hasher = hashlib.new("md5")
        hasher.update(
            json.dumps(box_parameters, sort_keys=True).encode("utf-8"))
        box_hash = hasher.hexdigest()

        return box_hash, input_parameters

    def _add_fingerprints(self, python_object):
        """ Add file path fingerprints.

        Parameters
        ----------
        python_object: object
            a generic python object.

        Returns
        -------
        out: object
            the input object with fingerprint-file representation.
        """
        # Deal with dictionary
        out = {}
        if isinstance(python_object, dict):
            for key, val in python_object.items():
                if val is not None:
                    out[key] = self._add_fingerprints(val)

        # Deal with tuple and list
        elif isinstance(python_object, (list, tuple)):
            out = []
            for val in python_object:
                if val is not None:
                    out.append(self._add_fingerprints(val))
            if isinstance(python_object, tuple):
                out = tuple(out)

        # Otherwise start the deletion if the object is a file
        else:
            out = python_object
            if (python_object is not None and
                    isinstance(python_object, str) and
                    os.path.isfile(python_object)):
                out = file_fingerprint(python_object)

        return out

    def _get_box_dir(self):
        """ Get the directory corresponding to the cache for the current
        box.

        Returns
        -------
        box_dir: string
            the directory where the cache should be write.
        """
        # Build the memory path from the box id
        path = [self.cachedir]
        path.extend(self.box.id.split("."))
        box_dir = os.path.join(*path)

        # Guarantee the path exists on the disk
        if not os.path.exists(box_dir):
            os.makedirs(box_dir)

        return box_dir

    def __repr__(self):
        """ MemorizedBox class representation.
        """
        return "{0}({1}, base_dir={2})".format(
            self.__class__.__name__, self.box.id, self.cachedir)

    def __getattr__(self, name):
        """ Define behavior for when a user attempts to access an attribute
        of a MemorizedBox instance.

        __getattr__ is only invoked if the attribute wasn't found the usual
        ways, so we first check the MemorizedBox object and then the box
        object.

        Parameters
        ----------
        name: string
            the name of the parameter we want to access.
        """
        if hasattr(self.box, name):
            return getattr(self.box, name)
        else:
            raise AttributeError(
                "'MemorizedBox' and associated box objects have no attribute "
                "'{0}'".format(name))


def get_box_signature(box, input_parameters):
    """ Generate the box signature.

    Parameters
    ----------
    box: a box
        a casper box object
    input_parameters: dict
        the box input parameters.

    Returns
    -------
    signature: string
        the box signature.
    """
    kwargs = ["{0}={1}".format(name, value)
              for name, value in input_parameters.items()]
    return "{0}({1})".format(box.id, ", ".join(kwargs))


def has_attribute(control, attribute_name, attribute_value=None,
                  recursive=True):
    """ Checks if a given control has an attribute and optionally if it
    is set to a particular value.

    Parameters
    ----------
    control: a control
        the input control object.
    attribute_name: string
        the control attribute name that will be checked.
    attribute_value: object (optional)
        the control attribute axpected value.
    recursive: bool (optional, default True)
        check for the attribute in the inner controls.

    Returns
    -------
    res: bool
        True if input given control has an attribute and optionally if it
        is set to a particular value.
    """
    # Check the current control
    if control.nohash:
        return True

    # Check the inner traits
    if recursive and control.iterable:
        return has_attribute(control.inner_control, attribute_name,
                             attribute_value, recursive)

    return False


def file_fingerprint(afile):
    """ Computes the file fingerprint.

    Do not consider the file content, just the fingerprint (ie. the mtime,
    the size and the file location).

    Parameters
    ----------
    afile: string
        the file to process.

    Returns
    -------
    fingerprint: tuple
        the file location, mtime and size.
    """
    fingerprint = {
        "name": afile,
        "mtime": None,
        "size": None
    }
    if os.path.isfile(afile):
        stat = os.stat(afile)
        fingerprint["size"] = str(stat.st_size)
        fingerprint["mtime"] = str(stat.st_mtime)
    return fingerprint


class MemoryResultEncoder(json.JSONEncoder):
    """ Deal with special elements in json.
    """
    def default(self, obj):
        # Array special case
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        # Default
        return tuple_json_encoder(obj)


def tuple_json_encoder(obj):
    """ Encode a tuple in order to save it in json format.

    Parameters
    ----------
    obj: object
        a python object to encode.

    Returns
    -------
    encobj: object
        the encoded object.
    """
    if isinstance(obj, tuple):
        return {
            "__tuple__": True,
            "items": [tuple_json_encoder(item) for item in obj]
        }
    elif isinstance(obj, list):
        return [tuple_json_encoder(item) for item in obj]
    elif isinstance(obj, dict):
        return dict((tuple_json_encoder(key), tuple_json_encoder(value))
                    for key, value in obj.items())
    else:
        return obj


class MemoryResultDecoder(json.JSONDecoder):
    """ Deal with special elements in json.
    """
    def __init__(self, *args, **kargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_object, *args,
                                  **kargs)

    def object_object(self, obj):
        # Tuple special case
        if "__tuple__" in obj:
            return tuple(obj["items"])
        # Default
        else:
            return obj


############################################################################
# Memory manager: provide some tracking about what is computed when, to
# be able to flush the disk
############################################################################

class Memory(object):
    """ Memory context to provide caching for boxes.

    Attributes
    ----------
    `cachedir`: string
        the location for the caching. If None is given, no caching is done.

    Methods
    -------
    cache
    clear
    """

    def __init__(self, cachedir):
        """ Initialize the Memory class.

        Parameters
        ----------
        base_dir: string
            the directory name of the location for the caching.
        """
        # Build the capsul memory folder
        if cachedir is not None:
            cachedir = os.path.join(
                os.path.abspath(cachedir), "casper_memory")
            if not os.path.exists(cachedir):
                os.makedirs(cachedir)
            elif not os.path.isdir(cachedir):
                raise ValueError("'base_dir' should be a valid directory.")

        # Define class parameters
        self.cachedir = cachedir
        self.timestamp = time.time()

    def cache(self, box, verbose=1):
        """ Create a proxy of the given bbox in order to only execute
        the bbox for input parameters not cached on disk.

        Parameters
        ----------
        box: a box
            the casper box to be wrapped and cached.
        verbose: int
            if different from zero, print console messages.

        Returns
        -------
        proxy_box: MemorizedBox object
            the returned object is a MemorizedBox object, that behaves
            as a box object, but offers extra methods for cache lookup
            and management.
        """
        # If a proxy box is found get the encapsulated box
        if (isinstance(box, MemorizedBox) or isinstance(box, UnMemorizedBox)):
            box = box.box

        # If the cachedir is None no caching is done
        if self.cachedir is None:
            return UnMemorizedBox(box, verbose)
        # Otherwise a proxy box is created
        else:
            return MemorizedBox(box, self.cachedir, self.timestamp, verbose)

    def clear(self, skips=None):
        """ Remove all the cache appart from those given to the method
        input.

        Parameters
        ----------
        skips: list
            a list of path to keep during the cache deletion.
        """
        # Get all memory directories to remove
        to_remove_folders = []
        skips = skips or []
        for root, dirs, files in os.walk(self.cachedir):
            if "result.json" and files and dirs == [] and root not in skips:
                to_remove_folders.append(root)

        # Delete memory directories
        for folder in to_remove_folders:
            shutil.rmtree(folder)

    def __repr__(self):
        """ Memory class representation.
        """
        return "{0}(cachedir={1})".format(self.__class__.__name__,
                                          self.cachedir)
