#!/usr/bin/python3
from gi.repository import GLib
from appdirs import AppDirs
from configparser import ConfigParser
import os
import errno

APP_NAME = "Kaede"
APP_AUTHOR = "Hattshire"
CONFIG_FILENAME = "config.ini"


class KaedeConfig(ConfigParser):
    """Configuration manager."""

    __defaults__ = {
        'search': {
            'rating-safe': True,
            'rating-questionable': True,
            'rating-explicit': False
        },
        'download': {
            'folder': GLib.get_user_special_dir(GLib.USER_DIRECTORY_PICTURES)
            or
            os.path.join(os.path.expanduser("~"), "Pictures")
        }
    }

    # To access from anywhere (from threads.py)
    __instance__ = None

    def __init__(self):
        """Init function."""
        super(KaedeConfig, self).__init__()
        self.dirs = AppDirs(APP_NAME, APP_AUTHOR)
        self.file = os.path.join(self.dirs.user_config_dir, CONFIG_FILENAME)

        # Set the defaults in case of bad or outdated file
        for item in KaedeConfig.__defaults__.items():
            self[item[0]] = item[1]

        if not os.path.exists(self.file):
            self.save()
        else:
            self.read(self.file)
        KaedeConfig.__instance__ = self

    def save(self):
        """Write settings to the settings file."""
        # Check if the folder containing the file exists.
        # If not, create it, we don't want annoying errors,
        # do you?
        file_dir = os.path.dirname(self.file)
        if not os.path.exists(file_dir):
            try:
                os.makedirs(file_dir)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise

        with open(self.file, 'w') as inifile:
            self.write(inifile)
