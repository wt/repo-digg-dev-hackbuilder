#  Copyright 2011 Digg, Inc.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import Queue

import digg.dev.hackbuilder.errors


plugin_names = [
        'python',
        'debian',
        ]

def _get_all_build_file_rules_generators(plugins):
    build_file_rules_generators = set()
    for plugin in plugins:
        build_file_rules_generators.add(plugin.build_file_rules_generator)

    return build_file_rules_generators

def get_all_build_file_rules(repo_path, normalizer):
    all_build_file_rules = {}
    all_build_file_rules_keys = set()
    duplicate_keys = set()
    for plugin in plugin_modules:
        build_file_rules = plugin.build_file_rules_generator(repo_path,
                normalizer)
        plugin_build_file_rules_keys = set(build_file_rules.iterkeys())
        duplicate_keys.update(all_build_file_rules_keys &
                plugin_build_file_rules_keys)
        all_build_file_rules_keys.update(plugin_build_file_rules_keys)
        all_build_file_rules.update(build_file_rules)

    if duplicate_keys != set():
        raise digg.dev.hackbuilder.errors.Error(
                'The selected plugins have caused the following '
                'duplicate build_file_locals to be defined: %s'
                % (', '.join(duplicate_keys),))

    return all_build_file_rules


def initialize_plugins(plugins, argparser):
    global plugin_modules
    global build_file_rules_generators
    build_file_rules_generators = _get_all_build_file_rules_generators(plugins)
    plugin_modules = set(plugins)
    for plugin_module in plugin_modules:
        try:
            plugin_module.add_argparser_arguments(argparser)
        except AttributeError:
            # Plugin module doesn't have additional args.
            pass


def share_args_with_plugins(plugin_modules, args):
    for plugin_module in plugin_modules:
        plugin_module.ARGS = args


# This is a global variable that is meant to hold all the functions that
# generate build file rules that are found in any plugins.
build_file_rules_generators = set()

# This is a global variable that is used to communicate build file targets
# discovered in a build file.
build_file_targets = Queue.Queue()

# This is a global variable that is used to communicate the plugin modules.
plugin_modules = set()
