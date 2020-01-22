# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Arduino

Arduino Wiring-based Framework allows writing cross-platform software to
control devices attached to a wide range of Arduino boards to create all
kinds of creative coding, interactive objects, spaces or physical experiences.

http://arduino.cc/en/Reference/HomePage
"""


import sys
from os import listdir, walk
from os.path import abspath, basename, isdir, isfile, join

from SCons.Script import DefaultEnvironment

env = DefaultEnvironment()

ulp_lib = None
ulp_dir = join(env.subst("$PROJECT_DIR"), "ulp")
if isdir(ulp_dir) and listdir(ulp_dir):
    ulp_lib = env.SConscript("ulp.py", exports="env")

env.SConscript("_embed_files.py", exports="env")

if "espidf" not in env.subst("$PIOFRAMEWORK"):
    env.SConscript(
        join(
            DefaultEnvironment()
            .PioPlatform()
            .get_package_dir("framework-arduinoespressif32"),
            "tools",
            "platformio-build.py",
        )
    )


def get_sdk_configuration(config_path):
    if not isfile(config_path):
        sys.stderr.write('Error: Could not find "sdkconfig.h" file\n')
        env.Exit(1)

    config = {}
    with open(config_path) as fp:
        for l in fp.readlines():
            if not l.startswith("#define"):
                continue
            values = l.split()
            config[values[1]] = values[2]

    return config


def is_set(parameter, configuration):
    if int(configuration.get(parameter, 0)):
        return True
    return False


def is_ulp_enabled(sdk_params):
    ulp_memory = int(sdk_params.get("CONFIG_ULP_COPROC_RESERVE_MEM", 0))
    ulp_enabled = is_set("CONFIG_ULP_COPROC_ENABLED", sdk_params)
    return ulp_memory > 0 and ulp_enabled


sdk_config_header = join(env.subst("$PROJECTSRC_DIR"), "sdkconfig.h")
sdk_params = get_sdk_configuration(sdk_config_header)

libs = []

if ulp_lib:
    if not is_ulp_enabled(sdk_params):
        print(
            "Warning! ULP is not properly configured."
            "Add next configuration lines to your sdkconfig.h:"
        )
        print("    #define CONFIG_ULP_COPROC_ENABLED 1")
        print("    #define CONFIG_ULP_COPROC_RESERVE_MEM 1024")

    libs.append(ulp_lib)
    env.Append(
        CPPPATH=[join("$BUILD_DIR", "ulp_app")],
        LIBPATH=[join("$BUILD_DIR", "ulp_app")],
        LINKFLAGS=["-T", "ulp_main.ld"],
    )

env.Prepend(LIBS=libs)
