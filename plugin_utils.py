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

import errno
import logging
import os.path

import digg.dev.hackbuilder.target


def normal_dep_targets_from_dep_strings(repo_path, normalizer, deps):
    normalized_deps = set()
    for dep in deps:
        orig_dep_id = digg.dev.hackbuilder.target.TargetID.from_string(
                dep)
        new_dep_id = normalizer.normalize_target_id_in_build_file(
                orig_dep_id, repo_path)
        normalized_deps.add(new_dep_id)

    return normalized_deps


class Builder(object):
    def __init__(self, normalizer, target, source_path, build_path,
            package_path):
        self.normalizer = normalizer
        self.target = target

        self.source_path = source_path
        self.build_path = build_path
        self.package_path = package_path

    def do_create_source_tree_work(self):
        pass

    def do_create_build_environment_work(self):
        pass

    def do_build_binary_work(self):
        pass

    def do_build_package_work(self):
        pass


class PackageBuilder(Builder):
    pass


class BinaryBuilder(Builder):
    pass


class LibraryBuilder(Builder):
    def do_create_source_tree_work(self):
        logging.info('Copying %s into source tree', self.target.target_id)
        full_src_path = os.path.join(self.normalizer.repo_root_path,
                self.target.target_id.path[1:])
        full_target_path = os.path.join(self.normalizer.repo_root_path,
                self.source_path, self.target.target_id.path[1:])
        for filename in self.target.files:
            src_filename = os.path.join(full_src_path, filename)
            dest_filename = os.path.join(full_target_path, filename)

            try:
                dest_dirname = os.path.dirname(dest_filename)
                os.makedirs(dest_dirname)
                logging.debug('Created directory: %s', dest_dirname)
            except OSError, e:
                if not e.errno == errno.EEXIST:
                    raise
                else:
                    logging.debug('Directory already exists: %s', dest_dirname)
            logging.debug('Creating symlink from  %s to %s', src_filename, dest_filename)
            os.symlink(src_filename, dest_filename)
