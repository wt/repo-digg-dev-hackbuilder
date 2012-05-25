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

import logging
import os.path

import digg.dev.hackbuilder.build
import digg.dev.hackbuilder.target
from digg.dev.hackbuilder.util import get_root_of_repo_directory_tree


def do_build(args):
    logging.info('Entering build mode.')

    repo_root = get_root_of_repo_directory_tree()
    logging.info('Repository root: %s', repo_root)

    normalizer = digg.dev.hackbuilder.target.Normalizer(repo_root)
    build_file_reader = digg.dev.hackbuilder.build.BuildFileReader(normalizer)

    for target_str in args.targets:
        logging.info("Building target %s", target_str)
        target_id = digg.dev.hackbuilder.target.TargetID.from_string(
                target_str)
        normal_target_id = normalizer.normalize_target_id(target_id)
        logging.info("Normalized target id: %s", normal_target_id)
        build_target_resolver = (
                digg.dev.hackbuilder.build.BuildTargetFromBuildFileResolver(
                    build_file_reader))
        build_target = build_target_resolver.resolve(normal_target_id)
        build_target_trees = {
            build_target: build_target.get_transitive_deps(
                build_target_resolver)
            }
        build = digg.dev.hackbuilder.build.Build(build_target_trees, normalizer)
        build.build()


def init_argparser(parser):
    parser.add_argument(
            'targets',
            default=[''],
            help='Targets to operate on.',
            nargs='*')
    parser.set_defaults(func=do_build)
