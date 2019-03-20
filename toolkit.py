import os
from json import load
from pathlib import Path

def get_config(name):
    '''Loads a json file located in the same directory as the running script'''

    # Scripts running location. Only set if called via python.exe
    __location__ = os.path.realpath(
        # From https://docs.python.org/3/library/os.path.html
        # If a component is an absolute path, all previous components
        # are thrown away and joining continues from the absolute path component.
        os.path.join(os.getcwd(), os.path.dirname(__file__)))

    # Build file path
    config_file_path = Path(os.path.join(__location__, name))

    # Read in configuration file.
    if(config_file_path.is_file()):
        # Build an object from the config file present
        with open(config_file_path) as json_file:
            return load(json_file)
    else:
        print("The configuration file '{}' does not exist".format(path=config_file_path))
