import ctypes
import json
import os
import sys
import traceback


TARGET_FILE = os.environ.get(
    "SYSCALL_DIG_TARGET_FILE",
    "/syscall-dig-target.py",
)
INPUTS_FILE = os.environ.get(
    "SYSCALL_DIG_INPUTS_FILE",
    "/syscall-dig-inputs.json",
)

with open(TARGET_FILE, encoding="utf-8") as target_file:
    target_source = target_file.read()
target_code = compile(target_source, TARGET_FILE, "exec")

with open(INPUTS_FILE, encoding="utf-8") as inputs_file:
    inputs_source = inputs_file.read()

enable_network_value = os.environ.get(
    "SYSCALL_DIG_ENABLE_NETWORK",
    "true",
).lower()
if enable_network_value not in {"true", "false"}:
    raise ValueError(
        "SYSCALL_DIG_ENABLE_NETWORK must be either true or false."
    )
enable_network = enable_network_value == "true"


def excepthook(type, value, tb):
    sys.stderr.write("".join(traceback.format_exception(type, value, tb)))
    sys.stderr.flush()
    sys.exit(-1)


sys.excepthook = excepthook

lib = ctypes.CDLL("/var/sandbox/sandbox-python/python.so")
lib.DifySeccomp.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_bool]
lib.DifySeccomp.restype = None

os.chdir("/var/sandbox/sandbox-python")
lib.DifySeccomp(65537, 1001, enable_network)

target_globals = {
    "__file__": TARGET_FILE,
    "__name__": "__main__",
}
exec(target_code, target_globals)

main = target_globals.get("main")
if not callable(main):
    raise TypeError(f"{TARGET_FILE} must define a callable main function.")

inputs = json.loads(inputs_source)
if not isinstance(inputs, dict):
    raise TypeError("The syscall test inputs must be a JSON object.")

output = main(**inputs)
output_json = json.dumps(output, indent=4)

result = f"""<<RESULT>>
{output_json}
<<RESULT>>"""

print(result)
