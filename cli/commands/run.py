#  Copyright 2012 Warren Turkal
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

from __future__ import print_function

import logging
import os.path

import digg.dev.hackbuilder.build
import digg.dev.hackbuilder.target
from digg.dev.hackbuilder.util import get_root_of_repo_directory_tree


def do_run(args):
    logging.info('Entering run mode.')

    repo_root = get_root_of_repo_directory_tree()
    logging.info('Repository root: %s', repo_root)

    normalizer = digg.dev.hackbuilder.target.Normalizer(repo_root)

    build_file_reader = digg.dev.hackbuilder.build.BuildFileReader(normalizer)
    build_file_target_finder = (
            digg.dev.hackbuilder.build.BuildFileTargetFinder(
                normalizer, build_file_reader))
    target_id = digg.dev.hackbuilder.target.TargetID.from_string(args.target)
    target_id = normalizer.normalize_target_id(target_id)
    target = build_file_target_finder.get_build_target(target_id)
    all_args = [target.bin_path] + args.args
    command_string = '" "'.join(all_args)
    logging.info('Execing command: %s', command_string)
    os.execv(target.bin_path, all_args)


def get_argparser(subparsers):
    parser = subparsers.add_parser('run', help='Run binary targets.',
            description='This subcommand can be used to run a binary '
                        'target. In order to pass arguments prefixed '
                        'with dashes (e.g. -a or --blah), please add '
                        'a -- argument to prevent further argument '
                        'parsing. For example: "%(prog)s -- binary '
                        'arg0 --arg1"')
    parser.add_argument(
            'target',
            default='',
            help='Target to run.')
    parser.add_argument(
            'args',
            default=[],
            type=str,
            help='Command line arguments for the target.',
            nargs='*')
    parser.set_defaults(func=do_run)

    return parser
