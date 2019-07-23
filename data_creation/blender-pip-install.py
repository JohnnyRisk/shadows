# WIP - See: https://blender.stackexchange.com/questions/5287/using-3rd-party-python-modules

import sys
import subprocess

blender_python = subprocess.check_output(
    'blender -b --python-expr "import sys; print(sys.exec_prefix)"',
    shell=True
).decode('utf-8').split()[0]

package_to_install = sys.argv[1]

subprocess.check_output(f'{blender_python}/bin/python3.5m -m ensurepip')

import bpy as _bpy
from addon_utils import check, paths, enable


def get_all_addons(display=False):
    paths_list = paths()
    addon_list = []
    for path in paths_list:
        _bpy.utils._sys_path_ensure(path)
        for mod_name, mod_path in _bpy.path.module_names(path):
            is_enabled, is_loaded = check(mod_name)
            addon_list.append(mod_name)
            if display:  # for example
                print("%s default:%s loaded:%s" % (mod_name, is_enabled, is_loaded))
    return addon_list
