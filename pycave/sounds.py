"""Tools for working with sounds in Cave projects
"""
import xml.etree.ElementTree as ET
from features import CaveFeature
from validators import AlwaysValid, IsNumeric, OptionListValidator
from errors import ConsistencyError, BadCaveXML
from xml_tools import bool2text, text2bool


class CaveSound(CaveFeature):
    """Store data on a sound to be used in the Cave

    :param str name: Unique name of this sound object
    :param str filename: File from which to take audio
    :param bool autostart: Start sound when project starts?
    :param str movement_mode: One of Positional or Fixed, determining if the
    sound is ambient or coming from an apparent position
    :param int repetitions: Number of times to repeat sound. Negative value
    indicates sound should loop forever
    :param float frequency_scale: Factor by which to scale frequency
    :param float volume_scale: Factor by which to scale volume (must be
    0.0-1.0)
    :param float pan: Stereo panning left to right (-1.0 to 1.0)
    """
    argument_validators = {
        "name": AlwaysValid(
            help_string="This should be a string specifying a unique name for"
            " this sound"),
        "filename": AlwaysValid(
            help_string="This should be a string specifying the audio file"),
        "autostart": AlwaysValid(help_string="Either true or false"),
        "movement_mode": OptionListValidator("Positional", "Fixed"),
        "repetitions": IsNumeric(),
        "frequency_scale": IsNumeric(min_value=0),
        "volume_scale": IsNumeric(min_value=0, max_value=1),
        "pan": IsNumeric(min_value=-1, max_value=1)
        }
    default_arguments = {
        "autostart": False,
        "movement_mode": "Positional",
        "repetitions": 0,
        "frequency_scale": 1,
        "volume_scale": 1,
        "pan": 0}

    def toXML(self, all_sounds_root):
        """Store CaveSound as Sound node within SoundRoot node

        :param :py:class:xml.etree.ElementTree.Element all_sounds_root
        """
        attrib = {}
        try:
            attrib["name"] = str(self["name"])
        except KeyError:
            raise ConsistencyError(
                'CaveSound must set a value for "name" key')
        try:
            attrib["filename"] = str(self["filename"])
        except KeyError:
            raise ConsistencyError(
                'CaveSound must set a value for "filename" key')
        if not self.is_default("autostart"):
            attrib["autostart"] = bool2text(self["autostart"])
        sound_root = ET.SubElement(all_sounds_root, "Sound", attrib=attrib)

        node = ET.SubElement(sound_root, "Mode")
        ET.SubElement(node, self["movement_mode"])

        node = ET.SubElement(sound_root, "Repeat")
        if self["repetitions"] == 0:
            ET.SubElement(node, "NoRepeat")
        if self["repetitions"] < 0:
            ET.SubElement(node, "RepeatForever")
        if self["repetitions"] > 0:
            node = ET.SubElement(node, "RepeatNum")
            node.text = str(self["repetitions"])

        settings = {}
        attrib_map = {
            "frequency_scale": "freq", "volume_scale": "volume", "pan": "pan"}
        for key, xml_attrib in attrib_map:
            if not self.is_default(key):
                settings[xml_attrib] = str(self[key])
        node = ET.SubElement(sound_root, "Settings", attrib=settings)

        return sound_root

    @classmethod
    def fromXML(sound_root):
        """Create CaveSound from Sound node

        :param :py:class:xml.etree.ElementTree.Element sound_root
        """
        new_sound = CaveSound()
        try:
            new_sound["name"] = sound_root.attrib["name"]
        except KeyError:
            raise BadCaveXML(
                "Sound node must specify name attribute")
        try:
            new_sound["filename"] = sound_root.attrib["filename"]
        except KeyError:
            raise BadCaveXML(
                "Sound node must specify filename attribute")
        if "autostart" in sound_root.attrib:
            new_sound["autostart"] = text2bool(sound_root.attrib["autostart"])

        movement_node = sound_root.find("Mode")
        if movement_node is None:
            raise BadCaveXML(
                "Sound node must contain Mode child node")
        for mode in new_sound.argument_validators[
                "movement_mode"].valid_options:
            if movement_node.find(mode) is not None:
                new_sound["movement_mode"] = mode
                break
        if "movement_mode" not in new_sound:
            raise BadCaveXML(
                "Mode node must contain child node specifying a valid mode"
                )

        repeat_node = sound_root.find("Repeat")
        if repeat_node is None:
            raise BadCaveXML(
                "Sound node must contain Repeat child node")
        if repeat_node.find("NoRepeat") is not None:
            new_sound["repetitions"] = 0
        elif repeat_node.find("RepeatForever") is not None:
            new_sound["repetitions"] = -1
        else:
            repeat_node = repeat_node.find("RepeatNum")
            try:
                new_sound["repetitions"] = int(repeat_node.text.strip())
            except AttributeError:
                raise BadCaveXML(
                    "Repeat node must contain child node specifying"
                    " repetitions")

        settings_node = sound_root.find("Settings")
        if settings_node is None:
            raise BadCaveXML(
                "Sound node must have Settings child node")
        xml_map = {
            "freq": "frequency_scale", "volume": "volume_scale", "pan": "pan"}
        for key, value in xml_map:
            if key in settings_node.attrib:
                new_sound[value] = float(settings_node.attrib[key])

        return new_sound

    def blend(self):
        """Create representation of CaveSound in Blender"""
        raise NotImplementedError  # TODO