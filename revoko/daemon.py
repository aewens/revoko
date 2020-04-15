from sys import stderr, exit
from json import loads as json_loads
from shlex import split as shell_split
from subprocess import run, PIPE
from pathlib import Path

# DEBUG
from pprint import pprint

## HELPERS

def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

def shell_run(command):
    proc = run(shell_split(command), stderr=PIPE, stdout=PIPE)
    return proc

def shell_result(proc):
    if proc.returncode != 0:
        return proc.stderr.decode()

    return proc.stdout.decode()

## UTILITIES

def load_config(config_file, test=False):
    config_data = config_file.read()
    try:
        return json_loads(config_data)

    except ValueError as e:
        eprint(e)
        if not test:
            exit(1)

    return None

def load_components(config):
    components = dict()
    config_components = config.get("_components")
    
    if not isinstance(config_components, dict):
        return components

    shared_settings = config.get("_shared", dict())

    # Create components directory if it does not exist already
    Path("components").mkdir(parents=True, exist_ok=True)
    for component_name, component_uri in config_components.items():
        components[component_name] = dict()

        # Check to see if any top-level keys belong to the component
        component_settings = config.get(component_name, dict())

        # Shared settings will be merged with component settings
        components[component_name] = {**component_settings, **shared_settings}

        component_path = f"components/{component_name}"
        if not Path(component_path).exists():
            clone_cmd = f"git clone {component_uri} {component_path}"
            clone_res = shell_run(clone_cmd)

    return components

def entry(config_file):
    config = load_config(config_file)
    components = load_components(config)
