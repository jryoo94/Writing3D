# Copyright (C) 2016 William Hicks
#
# This file is part of Writing3D.
#
# Writing3D is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

"""Tools for working with W3D project features

This module contains tools to help store data related to nearly any feature of
a W3D project. Here, feature refers generically to any complex structure that
may appear in such a project. This may be as sophisticated as a "Timeline" or
as simple as a "Placement" for an object (since Placement features define
position, and potentially multiple kinds of rotation).
"""
from .errors import InvalidArgument, ConsistencyError, ValidationError


class W3DFeature(dict):
    """Base class for all W3D features

    By overriding argument_validators and default_arguments, subclasses can
    easily validate input and provide sensible default arguments.

    :cvar argument_validators: Dictionary mapping names of valid arguments to
        callable objects that return true if a given value is valid for that
        argument

    :cvar default_arguments: Dictionary mapping names of arguments to their
        default values

    :cvar blender_scaling: Scaling factor used to convert back and forth
        between Blender and legacy units
    """

    argument_validators = {}
    default_arguments = {}
    blender_scaling = 1

    def __repr__(self):
        return "< {}: {} >".format(type(self).__name__, super().__repr__())

    def __lt__(self, other):
        """Order based on __repr__ of self and other

        Defined to allow unambiguous ordering of features"""

        return repr(self) < repr(other)

    def __init__(self, *args, **kwargs):
        super(W3DFeature, self).__init__()
        self.update(args)
        self.update(kwargs.items())
        self._validation_hashes = {}
        try:
            self.ui_order
        except AttributeError:
            self.ui_order = sorted(self.argument_validators.keys())

    def __setitem__(self, key, value):
        if key not in self.argument_validators:
            raise InvalidArgument(
                "{} not a valid option for this W3D feature".format(key))
        if not self.argument_validators[key](value):
            try:
                value = self.argument_validators[key].coerce(value)
            except:
                raise InvalidArgument(
                    "{} is not a valid value for option {}".format(value, key))
        if not self.argument_validators[key](value):
            raise InvalidArgument(
                "{} is not a valid value for option {}\nAdditional Info: "
                "{}".format(
                    value, key, self.argument_validators[key].help_string))
        super(W3DFeature, self).__setitem__(key, value)

    def __missing__(self, key):
        try:
            return self.default_arguments[key]
        except:
            name = type(self).__name__
            try:
                name = " ".join((name, super().get("name")))
            except:
                pass
            raise ConsistencyError(
                "{} requires {} to be set for requested operation".format(
                    name, key
                )
            )

    def __eq__(self, other):
        # TODO: Not sure if this is best OOP
        if type(self) != type(other):
            return False
        all_keys = set(self.keys())
        all_keys.update(other.keys())
        for key in all_keys:
            try:
                if self[key] != other[key]:
                    return False
            except (KeyError, ConsistencyError):
                return False
        return True

    def update(self, other):
        for key, value in other:
            self.__setitem__(key, value)

    def validate(self, project=None):
        """Validate all values for this feature, coercing if necessary"""
        identifier = [type(self).__name__]
        if "name" in self:
            identifier.append(self["name"])
        identifier = " ".join(identifier)

        for key, validator in self.argument_validators.items():
            if project is not None:
                validator.set_project(project)
            if self.is_default(key):
                continue
            try:
                if not validator(self[key], fallback=False):
                    try:
                        self[key] = validator.coerce(self[key])
                    except Exception as initial_error:
                        raise ValidationError(
                            "\n\n{}\n\nValue {} is not valid for attribute {}"
                            " of {}".format(
                                "\n".join(
                                    str(arg) for arg in initial_error.args
                                ),
                                self[key], key, identifier,
                            )
                        )
                    if not validator(self[key], fallback=False):
                        raise ValidationError(
                            "\n\nValue {} for attribute {} of {} is not"
                            " consistent with rest of project".format(
                                self[key], key, identifier
                            )
                        )
            except ConsistencyError:
                raise ValidationError(
                    "\n\nAttribute {} must be set for {}".format(
                        key, identifier)
                )
        return True

    def toXML(self, parent_root):
        """Store data in W3D XML format within parent_root

        :param parent_root: The XML node in which to store data
        :type parent_root: :class:`xml.etree.ElementTree.Element`

        Since this differs for every W3D feature, subclasses MUST override
        this function.
        """
        raise NotImplementedError("toXML not defined for this feature")

    @classmethod
    def fromXML(feature_class, xml_root):
        """Create W3DFeature object from xml node for such a feature

        Since this differs for every W3D feature, subclasses MUST override
        this function.

        :param xml_root: The XML node from which to create class instance
        :type xml_root: :class:`xml.etree.ElementTree.Element`
        """
        raise NotImplementedError("fromXML not defined for this feature")

    def is_default(self, key):
        """Return true if value has not been set for key"""
        return key not in self
