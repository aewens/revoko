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

def load_components(config, args):
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

        # Convert merged settings to JSON string
        config_data = jots(merge_settings, verbose=True)
        if config_data is None:
            continue

        # Create temporary file to pass custom settings to components
        config_temp = NamedTemporaryFile(delete=False, suffix=".json")
        config_file = config_temp.name
        config_temp.write(config_data.encode())
        config_temp.close()

        component_dir = f"components/{component_name}"
        component_path = Path(component_dir)
        if not component_path.exists():
            # Clone the repo if it does not exist already
            clone_command = f"git clone {component_uri} {str(component_path)}"
            clone_result = shell_run(clone_command)
            if clone_result.returncode != 0:
                eprint(clone_result.stderr)
                continue

        elif not args.no_updates:
            # Merge updates from the repo if they exist
            merge_flags = "--no-edit --commit -X theirs"
            merge_result = shell_run(f"git pull origin master {merge_flags}")
            if merge_result.returncode != 0:
                eprint(merge_result.stderr)
                continue

        if not args.no_scripts:
            # Run all of the component scripts in sorted order 
            component_scripts = component_path / "scripts"
            for component_script in sorted(component_scripts.glob("*")):
                script_name = str(component_script)
                log_file = str(Path(f"{component_dir}.log").absolute())
                pid_file = str(Path(f"{component_dir}.pid").absolute())
                shell_arguments = " ".join([config_file, log_file, pid_file])
                shell_command = f"{script_name} {shell_arguments}"
                # Pass config, log, and PID file to scripts as arguments
                script_result = shell_run(shell_command, timeout=args.timeout)
                if script_result.returncode != 0:
                    eprint(script_result.stderr)
                    continue

    return components

def entry(args):
    config = load_config(args.config)
    components = load_components(config, args)
    # DEBUG
    #pprint(components)
