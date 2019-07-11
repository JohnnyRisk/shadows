# WIP - See: https://blender.stackexchange.com/questions/5287/using-3rd-party-python-modules

import sys
import subprocess

blender_python = subprocess.check_output(
    'blender -b --python-expr "import sys; print(sys.exec_prefix)"', 
    shell=True
).decode('utf-8').split()[0]

package_to_install = sys.argv[1]

subprocess.check_output(f'{blender_python}/bin/python3.5m -m ensurepip')
