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
    build_file_target_finder = (
            digg.dev.hackbuilder.build.BuildFileTargetFinder(
                normalizer, build_file_reader))
    build_file_target_finder.seed_from_cli_build_target_ids(args.targets)
    build_target_trees = build_file_target_finder.get_target_trees()

    build = digg.dev.hackbuilder.build.Build(build_target_trees, normalizer)
    build.build()


def init_argparser(parser):
    parser.add_argument(
            '--jobs', '-j',
            default=1,
            type=int,
            help='Number of parallel actions. (default=1) '
                 '(parallel actions not yet implemented',)
    parser.add_argument(
            'targets',
            default=[''],
            help='Targets to operate on.',
            nargs='*')
    parser.set_defaults(func=do_build)
