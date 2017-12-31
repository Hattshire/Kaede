#!/usr/bin/python3
from gi.repository import GLib
from appdirs import AppDirs
from configparser import ConfigParser
import os
import errno

APP_NAME = "Kaede"
APP_AUTHOR = "Hattshire"
CONFIG_VERSION = "0.1"
CONFIG_FILENAME = "config.ini"

dirs = AppDirs(APP_NAME, APP_AUTHOR, version=CONFIG_VERSION)
file_path = os.path.join(dirs.user_config_dir, CONFIG_FILENAME)
config = ConfigParser()

default_save_dir = GLib.get_user_special_dir(GLib.USER_DIRECTORY_PICTURES)
if default_save_dir is None:
    default_save_dir = os.path.join(os.path.expanduser("~"), "Pictures")

if not os.path.exists(file_path):
    if not os.path.exists(dirs.user_config_dir):
        try:
            os.makedirs(dirs.user_config_dir)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

    _file = open(file_path, "w")

    config['Search settings'] = {}
    config['Search settings']['Rating safe'] = "Enabled"
    config['Search settings']['Rating questionable'] = "Enabled"
    config['Search settings']['Rating explicit'] = "Enabled"
    config['Download settings'] = {}
    config['Download settings']['Save dir'] = default_save_dir

    config.write(_file)

    _file.close()
else:
    config.read(file_path)


def set_config(section, key, value):
    if section not in config:
        config[section] = {}
    config[section][key] = value

    _file = open(file_path, "w")
    config.write(_file)
    _file.close()


def get_config(section, key, default_value=None):
    if section not in config or key not in config[section]:
        value = default_value
    else:
        value = config[section][key]
    return value
