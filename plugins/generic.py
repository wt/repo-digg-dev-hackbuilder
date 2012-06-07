#  Copyright 2012 Ooyala, Inc.
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

import logging
import os.path
import pipes

import digg.dev.hackbuilder.target
import digg.dev.hackbuilder.plugin_utils
from digg.dev.hackbuilder.plugins import build_file_targets
from digg.dev.hackbuilder.plugin_utils \
        import normal_dep_targets_from_dep_strings
from digg.dev.hackbuilder.plugin_utils import StartScriptBuilder
from digg.dev.hackbuilder.errors import Error


class UpstartScriptBuilder(
        digg.dev.hackbuilder.plugin_utils.StartScriptBuilder):

    def __init__(self, target):
        digg.dev.hackbuilder.plugin_utils.StartScriptBuilder.__init__(self,
                target)

    def do_pre_build_package_binary_install(self, builders, package_builder,
            bin_path, **kwargs):
        logging.info('Adding upstart script for %s to package %s',
                self.target.target_id, package_builder.target.target_id)

        binary_full_path = os.path.join(bin_path,
                self.target.binary_target_id.name)

        #TODO(wt) pipe.quote->shlex.quote when transitioning to python 3.3+
        escaped_args = [pipes.quote(arg) for arg in self.target.args]
        args_str = "'%s'" % "'".join(escaped_args)

        script_dir = os.path.abspath(
                os.path.sep.join((package_builder.full_package_hierarchy_dir,
                                  self.target.upstart_script_dir)))

        logging.info('Creating dir: %s', script_dir)
        os.makedirs(script_dir)

        upstart_script_text = (
                'description "{description}"\n'
                '\n'
                'start on filesystem\n'
                'stop on runlevel [!2345]\n'
                '\n'
                'umask 022\n'
                '\n'
                'exec {binary_full_path} {args_str}').format(
                        description=self.target.service_name,
                        binary_full_path=binary_full_path,
                        args_str=args_str)
        logging.debug('Upstart script script text:\n%s', upstart_script_text)

        full_path = os.path.join(script_dir,
                '{0}.conf'.format(self.target.service_name))
        logging.debug('Upstart script file absolute path: %s', full_path)
        with open(full_path, 'w') as upstart_script_file:
            upstart_script_file.write(upstart_script_text)


class UpstartScriptBuildTarget(
        digg.dev.hackbuilder.target.StartScriptBuildTarget):
    builder_class = UpstartScriptBuilder

    upstart_script_dir = '/etc/init'

    def __init__(self, normalizer, target_id, dep_ids=None, service_name=None,
            binary_target_id=None, args=None):
        digg.dev.hackbuilder.target.StartScriptBuildTarget.__init__(self,
                normalizer, target_id, dep_ids)

        if service_name is None:
            raise Error('No service name specified for upstart target (%s)',
                    self.target_id)
        self.service_name = service_name

        if binary_target_id is None:
            raise Error('No binary name specified for upstart target (%s)',
                    self.binary_target_id)
        self.binary_target_id = binary_target_id

        if args is None:
            args = []
        self.args = args


def build_file_upstart_script(repo_path, normalizer):
    def upstart_script(name, deps=(), service_name=None, binary=None,
            args=None):
        logging.debug('Build file target, Upstart script: %s', name)
        target_id = digg.dev.hackbuilder.target.TargetID(repo_path, name)
        dep_target_ids = normal_dep_targets_from_dep_strings(repo_path,
                normalizer, deps)
        binary_target_id = digg.dev.hackbuilder.target.TargetID.from_string(
                binary)
        normal_binary_target_id = normalizer.normalize_target_id(binary_target_id)
        upstart_script_target = UpstartScriptBuildTarget(normalizer, target_id,
                dep_ids=dep_target_ids, service_name=service_name,
                binary_target_id=normal_binary_target_id, args=args)
        build_file_targets.put(upstart_script_target)

    return upstart_script


def build_file_rules_generator(repo_path, normalizer):
    build_file_rules = {
            'upstart_script': build_file_upstart_script(repo_path, normalizer),
            }
    return build_file_rules
