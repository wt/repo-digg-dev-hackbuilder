#  Copyright 2011 Digg, Inc.
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
import subprocess

import digg.dev.hackbuilder.target
import digg.dev.hackbuilder.plugin_utils
from digg.dev.hackbuilder.plugins import build_file_targets
from digg.dev.hackbuilder.plugin_utils \
        import normal_dep_targets_from_dep_strings
from digg.dev.hackbuilder.plugin_utils import BinaryLauncherBuilder


class MacPackageBuilder(digg.dev.hackbuilder.plugin_utils.PackageBuilder):
    def __init__(self, target):
        digg.dev.hackbuilder.plugin_utils.PackageBuilder.__init__(self, target)

        self.full_package_hierarchy_dir = os.path.join(
                self.target.target_build_dir, 'macosx_hierarchy')

    def do_pre_build_package_binary_install(self, builders):
        logging.info('Copying built binaries to package hierarchy for %s',
                self.target.target_id)

        package_data = {
                'bin_path': '/bin',
                'sbin_path': '/sbin',
                'lib_path': '/Library',
                }

        for dep_id in self.target.dep_ids:
            builder = builders[dep_id]
            if isinstance(builder, BinaryLauncherBuilder):
                builder.do_pre_build_package_binary_install(builders, self,
                        **package_data)

    def do_build_package_work(self):
        self._create_mac_binary_package()

    def _create_mac_binary_package(self):
        logging.info('Creating Mac binary package for %s', self.target.target_id)
        package_file_path = os.path.join(self.target.package_root,
                                         self.target.pkg_filename)
        proc = subprocess.Popen(
                    ('packagemaker',
                     '--root', self.full_package_hierarchy_dir,
                     '--id', 'zyzzx.' + self.target.target_id.name,
                     '--domain', 'system',
                     '--domain', 'user',
                     '--domain', 'anywhere',
                     '--target', '10.5',
                     '--filter', '\.DS_Store',
                     '--version', self.target.version,
                     '--out', package_file_path,
                     ),
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE)
        (stdoutdata, stderrdata) = proc.communicate()
        retcode = proc.returncode
        if retcode != 0:
            logging.info('Mac binary package creation failed.')
            logging.info('Mac binary package creation failed with exit code = %s',
                    retcode)
            logging.info('Mac binary package creation stdout:\n%s',
                    stdoutdata)
            logging.info('Mac binary package creation stderr:\n%s',
                    stderrdata)
            raise digg.dev.hackbuilder.errors.Error(
                    'packagemaker call failed with exitcode %s', retcode)

        logging.info('Package build at: %s', package_file_path)


class MacPackageBuildTarget(
        digg.dev.hackbuilder.target.PackageBuildTarget):
    builder_class = MacPackageBuilder

    def __init__(self, normalizer, target_id, pkg_filebase, dep_ids=None,
            version=None):
        digg.dev.hackbuilder.target.PackageBuildTarget.__init__(self,
                normalizer, target_id, dep_ids=dep_ids, version=version)

        if os.path.basename(pkg_filebase) != pkg_filebase:
            raise digg.dev.hackbuilder.errors.Error(
                    'Pkg_filebase in target (%s) cannot contain a path '
                    'separator.', target_id)

        self.pkg_filebase = pkg_filebase
        self.pkg_filename = '{0}-{1}.pkg'.format(pkg_filebase, version)


def build_file_mac_pkg(repo_path, normalizer):
    def mac_pkg(name, deps=(), version=None, pkg_filebase=None):
        logging.debug('Build file target, Mac package: %s', name)
        target_id = digg.dev.hackbuilder.target.TargetID(repo_path, name)
        dep_target_ids = normal_dep_targets_from_dep_strings(repo_path,
                normalizer, deps)

        if pkg_filebase is None:
            raise digg.dev.hackbuilder.errors.Error(
                    'No pkg_filebase specified for mac package (%s)',
                    target_id)

        mac_pkg_target = MacPackageBuildTarget(normalizer, target_id,
                dep_ids=dep_target_ids, version=version,
                pkg_filebase=pkg_filebase)
        build_file_targets.put(mac_pkg_target)

    return mac_pkg


def build_file_rules_generator(repo_path, normalizer):
    build_file_rules = {
            'mac_pkg': build_file_mac_pkg(repo_path, normalizer)
            }
    return build_file_rules
