from sys import stderr, exit
from json import loads as json_loads, dumps as json_dumps
from shlex import split as shell_split
from subprocess import run, PIPE, TimeoutExpired
from pathlib import Path
from tempfile import NamedTemporaryFile

# DEBUG
from pprint import pprint

## HELPERS

def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

def shell_run(command, timeout=None):
    try:
        proc = run(shell_split(command), stderr=PIPE, stdout=PIPE,
            timeout=timeout)

    except TimeoutExpired as e:
        eprint(e)
        return None

    return proc

def shell_result(proc):
    if proc.returncode != 0:
        return proc.stderr.decode()

    return proc.stdout.decode()

def jsto(data, verbose=False):
    try:
        return json_loads(data)

    except ValueError as e:
        if verbose:
            eprint(e)

        return None

def jots(data, readable=False, verbose=False):
    kwargs = dict()

    # If readable is set, it pretty prints the JSON to be more human-readable
    if readable:
        # kwargs["sort_keys"] = True
        kwargs["indent"] = 4 
        kwargs["separators"] = (",", ":")

    try:
        return json_dumps(data, **kwargs)

    except ValueError as e:
        if verbose:
            eprint(e)

        return None

## UTILITIES

def load_config(config_file, test=False):
    config_data = config_file.read()
    config = jsto(config_data, verbose=True)
    if config is None and not test:
        exit(1)

    return config

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
        merge_settings = {**component_settings, **shared_settings}
        components[component_name] = merge_settings

        # Create temporary file to pass custom settings to components
        config_data = jots(merge_settings, verbose=True)
        if config_data is None:
            continue

        config_file = NamedTemporaryFile(delete=False, suffix=".json")
        config_name = config_file.name
        config_file.write(config_data.encode())
        config_file.close()

        component_dir = f"components/{component_name}"
        component_path = Path(component_dir)
        if not component_path.exists():
            clone_command = f"git clone {component_uri} {str(component_path)}"
            clone_result = shell_run(clone_command)
            if clone_result.returncode != 0:
                eprint(clone_result.stderr)
                continue

        component_scripts = component_path / "scripts"
        for component_script in sorted(component_scripts.glob("*")):
            script_name = str(component_script)
            log_file = str(Path(f"{component_dir}.log").absolute())
            pid_file = str(Path(f"{component_dir}.pid").absolute())
            timeout = 3 * 60
            shell_command = f"{script_name} {config_name} {log_file} {pid_file}"
            script_result = shell_run(shell_command, timeout=timeout)
            if script_result.returncode != 0:
                eprint(script_result.stderr)
                continue

    return components

def entry(config_file):
    config = load_config(config_file)
    components = load_components(config)
    #pprint(components)
