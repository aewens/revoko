from sys import stderr, exit
from json import loads as json_loads, dumps as json_dumps
from shlex import split as shell_split
from subprocess import run, PIPE, TimeoutExpired
from pathlib import Path
from tempfile import NamedTemporaryFile
from os import kill
from signal import SIGTERM

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

# NOTE - I can probably remove this
#def shell_result(proc):
#    if proc.returncode != 0:
#        return proc.stderr.decode()
#
#    return proc.stdout.decode()

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

    except Exception as e:
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

def load_component(args, component_path, component_uri):
    if not component_path.exists():
        # Clone the repo if it does not exist already
        clone_command = f"git clone {component_uri} {str(component_path)}"
        clone_result = shell_run(clone_command)
        if clone_result.returncode != 0:
            eprint(clone_result.stderr)
            return False

    elif not args.no_updates:
        # Merge updates from the repo if they exist
        merge_flags = "--no-edit --commit -X theirs"
        merge_result = shell_run(f"git pull origin master {merge_flags}")
        if merge_result.returncode != 0:
            eprint(merge_result.stderr)
            return False

    return True

def run_component_scripts(args, component_path, config_data):
    prefix = "revoko_"
    suffix = ".json"
    tmp_glob = f"{prefix}*{suffix}"

    # Clear out previous temporary config file
    for tmp in component_path.glob(tmp_glob):
        tmp.unlink()

    # Create temporary file to pass custom settings to components
    config_temp = NamedTemporaryFile(delete=False, prefix=prefix, suffix=suffix)

    config_file = config_temp.name
    config_temp.write(config_data.encode())
    config_temp.close()

    # Run all of the component scripts in sorted order 
    component_dir = str(component_path)
    component_scripts = component_path / "_scripts"
    if not component_scripts.exists():
        return None

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
            return False

    return True

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

        component_path = Path(f"components/{component_name}")

        # If new get the source code, if old try to merge updates
        loaded = load_component(args, component_path, component_uri)
        if not loaded:
            continue

        if not args.no_scripts:
            # Convert merged settings to JSON string
            config_data = jots(merge_settings, verbose=True)
            if config_data is None:
                continue

            ran = run_component_scripts(args, component_path, config_data)
            if not ran:
                continue

    return components

def kill_components(components, args):
    kill_components = components.keys() if args.kill_all else args.kill
    for component_name in components.keys():
        if component_name not in kill_components:
            continue

        component_path = Path(f"components/{component_name}.pid")
        if not component_path.exists():
            print(f"Skipping {component_name}: no PID file...")
            continue

        # Get list of PIDs from file to send SIGTERM
        for pid in map(int, component_path.read_text().split()):
            try:
                kill(pid, SIGTERM)

            except ProcessLookupError as e:
                continue

def entry(args):
    killing = args.kill_all or args.kill
    if killing:
        args.no_updates = True
        args.no_scripts = True

    config = load_config(args.config)
    components = load_components(config, args)

    # DEBUG
    #pprint(components)

    if killing:
        kill_components(components, args)
