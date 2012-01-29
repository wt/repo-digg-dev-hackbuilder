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

import collections
import errno
import logging
import os
import os.path
import shutil
import Queue

import digg.dev.hackbuilder.common
import digg.dev.hackbuilder.errors
import digg.dev.hackbuilder.plugins
from digg.dev.hackbuilder.plugin_utils import BinaryBuilder
from digg.dev.hackbuilder.plugin_utils import PackageBuilder


class BuildFileReader(object):
    """A build file reader for reading the HACK_BUILD files.

    Attributes:
        cached_build_file_targets: This is a cache to prevent build files from
            having to be processed more than once. It's keys are a repository
            paths, and it's values are the discoverd build file targets for
            that path.
    """
    def __init__(self, normalizer):
        self.normalizer = normalizer
        self.cached_build_file_targets = dict()

    def get_build_file_targets_for_repo_path(self, build_file_dirname):
        if build_file_dirname in self.cached_build_file_targets:
            return self.cached_build_file_targets[build_file_dirname]

        build_file_filename = os.path.join(self.normalizer.repo_root_path,
                build_file_dirname[1:], 'HACK_BUILD')
        build_file_locals = (
                digg.dev.hackbuilder.plugins.get_all_build_file_rules(
                    build_file_dirname, self.normalizer))
        logging.info('loading build file at: %s', build_file_filename)
        execfile(build_file_filename, {}, build_file_locals)

        build_file_targets = self._get_all_targets_from_global_queue()

        self.cached_build_file_targets[build_file_dirname] = build_file_targets
        return build_file_targets

    def _get_all_targets_from_global_queue(self):
        """Fetch all the build file targets from the global variable queue.

        These build file targets are store in a global queue after each build
        file is processed.
        
        Returns: A set of all the build file targets that were on the queue.
        """
        global_build_file_targets_queue = (
                digg.dev.hackbuilder.plugins.build_file_targets)
        build_file_targets = set()
        while True:
            try:
                item = global_build_file_targets_queue.get_nowait()
            except Queue.Empty:
                break
            build_file_targets.add(item)
            global_build_file_targets_queue.task_done()

        return build_file_targets

class BuildFileTargetFinder(object):
    def __init__(self, normalizer, build_file_reader):
        self.normalizer = normalizer
        self.build_file_reader = build_file_reader
        self.target_ids = set()
        self.build_file_path_seen = set()

    def seed_from_cli_build_target_ids(self, arg_targets):
        self.seed_target_ids = self._get_normalized_target_ids_from_cli_args(
                arg_targets)

    def get_target_trees(self, target_ids_to_discover=None):
        if target_ids_to_discover is None:
            target_ids_to_discover = self.seed_target_ids.copy()

        dep_trees = {}
        for target_id in target_ids_to_discover:
            build_target = self._get_build_target(target_id)
            dep_targets = self.get_target_trees(
                    target_ids_to_discover=build_target.dep_ids)
            dep_trees[build_target] = dep_targets
        return dep_trees

    def _get_build_target(self, target_id):
        get_build_file_targets_for_repo_path = (
                self.build_file_reader.get_build_file_targets_for_repo_path)
        build_file_path = target_id.path

        possible_build_file_targets = set()
        possible_build_file_targets.update(
                get_build_file_targets_for_repo_path(
                    build_file_path))

        build_file_targets_to_discover = set()
        for build_file_target in possible_build_file_targets:
            if build_file_target.target_id == target_id:
                return build_file_target

        raise digg.dev.hackbuilder.errors.Error(
                'No build target found for target id(%s)'
                % target_id)

    def _get_normalized_target_ids_from_cli_args(self, arg_targets):
        normalized_targets = set()
        for target in arg_targets:
            target_id = digg.dev.hackbuilder.target.TargetID.from_string(
                    target)
            normalized_targets.add(
                    self.normalizer.normalize_target_id(target_id))
        return normalized_targets


class Build(object):
    def __init__(self, build_target_trees, normalizer,
            source_path=digg.dev.hackbuilder.common.DEFAULT_SOURCE_DIR,
            build_path=digg.dev.hackbuilder.common.DEFAULT_BUILD_DIR,
            package_path=digg.dev.hackbuilder.common.DEFAULT_PACKAGE_DIR):
        self.build_target_trees = build_target_trees
        self.normalizer = normalizer

        self.source_path = source_path
        self.build_path = build_path
        self.package_path = package_path

        self.builders = {}
        if build_target_trees is not None:
            target_dep_sequences = self._get_target_dep_sequences()
            for target_deps in target_dep_sequences.itervalues():
                for target in [i[0] for i in target_deps]:
                    if target.target_id not in self.builders:
                        builder = target.builder_class(target)
                        self.builders[target.target_id] = builder


    def build(self):
        logging.info('Starting build.')
        self.create_dirs()
        self.do_create_source()
        self.do_create_build_environment()
        self.do_build_binary()
        self.do_build_package()
        logging.info('Finishing build.')

    def create_dirs(self):
        logging.info('Creating infrastructure directories')

        logging.info('Creating source directory: %s', self.source_path)
        self._mkdir_in_repo_dir(self.source_path)

        logging.info('Creating build directory: %s', self.build_path)
        self._mkdir_in_repo_dir(self.build_path)

        logging.info('Creating package directory: %s', self.package_path)
        self._mkdir_in_repo_dir(self.package_path)

    def _mkdir_in_repo_dir(self, path):
        full_path = os.path.join(self.normalizer.repo_root_path, path)
        logging.debug('Creating absolute directory: %s', full_path)
        try:
            os.mkdir(full_path)
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise

    def remove_directories(self):
        logging.info('Removing infrastructure directories')

        logging.info('Removing source hierarchy: %s', self.source_path)
        self._rmtree_in_repo_dir(self.source_path)

        logging.info('Removing build hierarchy: %s', self.build_path)
        self._rmtree_in_repo_dir(self.build_path)

        logging.info('Removing package hierarchy: %s', self.package_path)
        self._rmtree_in_repo_dir(self.package_path)

    def _rmtree_in_repo_dir(self, path):
        full_path = os.path.join(self.normalizer.repo_root_path, path)
        logging.debug('Removing absolute directory: %s', full_path)
        try:
            shutil.rmtree(full_path)
        except OSError, e:
            if e.errno != errno.ENOENT:
                raise

    def do_create_source(self):
        logging.info('Entering create source tree state')

        target_sequences = self._get_target_dep_sequences()

        targets_handled = set()
        #while True:
        #    # build targets from target_deques
        #    break
        for targets in target_sequences.itervalues():
            for target in [i[0].target_id for i in targets]:
                if target not in targets_handled:
                    builder = self.builders[target]
                    if isinstance(builder, BinaryBuilder):
                        builder.do_pre_create_source_tree_work(
                                self.builders)
                    self.builders[target].do_create_source_tree_work()
                    targets_handled.add(target)

        logging.info('Exiting create source tree state')

    def do_create_build_environment(self):
        logging.info('Entering create build environment state')

        target_sequences = self._get_target_dep_sequences()

        targets_handled = set()
        #while True:
        #    # build targets from target_deques
        #    break
        for targets in target_sequences.itervalues():
            for target in [i[0].target_id for i in targets]:
                if target not in targets_handled:
                    builder = self.builders[target]
                    builder.do_create_build_environment_work()
                    targets_handled.add(target)

        logging.info('Exiting create build environment state')

    def do_build_binary(self):
        logging.info('Entering build binary state')

        target_sequences = self._get_target_dep_sequences()

        targets_handled = set()
        #while True:
        #    # build targets from target_deques
        #    break
        for targets in target_sequences.itervalues():
            for target in [i[0].target_id for i in targets]:
                if target not in targets_handled:
                    builder = self.builders[target]
                    if isinstance(builder, BinaryBuilder):
                        builder.do_pre_build_binary_library_install(
                                self.builders)
                    builder.do_build_binary_work()
                    targets_handled.add(target)

        logging.info('Exiting build binary state')

    def do_build_package(self):
        logging.info('Entering build package state')

        target_sequences = self._get_target_dep_sequences()

        targets_handled = set()
        #while True:
        #    # build targets from target_deques
        #    break
        for targets in target_sequences.itervalues():
            for target in [i[0].target_id for i in targets]:
                if target not in targets_handled:
                    builder = self.builders[target]
                    if isinstance(builder, PackageBuilder):
                        builder.do_pre_build_package_binary_install(
                                self.builders)
                    builder.do_build_package_work()
                    targets_handled.add(target)

        logging.info('Exiting build package state')

    def _get_target_dep_sequences(self):
        target_deques = {}
        for root_node in self.build_target_trees.iteritems():
            target_deques[root_node[0].target_id] = collections.deque()
            working_deque = collections.deque()
            working_deque.append(root_node)
            while len(working_deque) > 0:
                current_node = working_deque.pop()
                target_deques[root_node[0].target_id].appendleft(
                        current_node)
                for dep in current_node[1].iteritems():
                    working_deque.append(dep)

        return target_deques
