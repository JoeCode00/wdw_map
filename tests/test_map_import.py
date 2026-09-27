import importlib
import sys


def test_map_module_imports_without_running_input():
    sys.modules.pop('map', None)
    module = importlib.import_module('map')
    assert hasattr(module, 'RemoteDesktopPortal')
