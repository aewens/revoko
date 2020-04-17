from .context import daemon

from pathlib import Path
from argparse import Namespace

args = Namespace(timeout=3 * 60, no_scripts=False, no_updates=False,
    kill=[], kill_all=True)

def test_eprint():
    assert daemon.eprint("Hello, world!") is None, "eprint returned something"

def test_shell_run_pass():
    result = daemon.shell_run("echo 'Hello, world!'")
    assert result is not None, "shell_run returned nothing"
    assert hasattr(result, "returncode"), "shell_run has no return code"
    assert result.returncode == 0, "Command failed"

def test_shell_run_fail():
    result = daemon.shell_run("rm fake")
    assert result is not None, "shell_run returned nothing"
    assert hasattr(result, "returncode"), "shell_run has no return code"
    assert result.returncode != 0, "Command passed when it should fail"

def test_shell_run_timeout():
    result = daemon.shell_run("sleep 2", 1)
    assert result is None, "shell_run did not timeout"

def test_jsto_pass():
    result = daemon.jsto("[]")
    assert result is not None, "jsto failed to parse JSON"

def test_jsto_fail():
    result = daemon.jsto("[],")
    assert result is None, "jsto incorrectly parsed JSON"

def test_jots_pass():
    result = daemon.jots([])
    assert result is not None, "jots failed to encode data"

def test_jots_fail():
    result = daemon.jots(lambda x: x + 1)
    assert result is None, "jots incorrectly encoded a function"

def test_load_config():
    config_file = open("config.example.json")
    config = daemon.load_config(config_file, test=True)
    assert config is not None, "Config is invalid"
    config_file.close()

def test_load_components():
    config_file = open("config.example.json")
    config = daemon.load_config(config_file, test=True)
    config_file.close()

    components = daemon.load_components(config, args)
    for component_name in config.get("_components", dict()).keys():
        component_missing = f"{component_name} is missing"
        assert components.get(component_name) is not None, component_missing

        path_missing = f"{component_name} repository is missing"
        assert Path(f"components/{component_name}").exists(), path_missing
