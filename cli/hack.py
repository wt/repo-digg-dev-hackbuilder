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

import argparse
import logging
import os
import os.path

from digg.dev.hackbuilder.util import get_root_of_repo_directory_tree
import digg.dev.hackbuilder.cli.commands.build
import digg.dev.hackbuilder.cli.commands.run
import digg.dev.hackbuilder.plugins


def main():
    logging.basicConfig(level=logging.DEBUG)

    logging.info('Initial working directory: %s', os.getcwd())

    parser = get_parser()
    plugin_modules = get_plugin_modules(
            digg.dev.hackbuilder.plugins.plugin_names)
    digg.dev.hackbuilder.plugins.initialize_plugins(plugin_modules, parser)
    args = parser.parse_args()
    digg.dev.hackbuilder.plugins.share_args_with_plugins(plugin_modules, args)
    args.func(args)


def get_parser():
    parser = argparse.ArgumentParser(description='Hack build tool.')
    subparsers = parser.add_subparsers(title='Subcommands')

    parser_help = subparsers.add_parser('help', help='Subcommand help')
    parser_help.add_argument(
            'subcommand_name',
            help='Name of command to get help for',
            nargs='?')

    parser_build = subparsers.add_parser('build', help='Build targets.')
    digg.dev.hackbuilder.cli.commands.build.init_argparser(parser_build)

    parser_run = subparsers.add_parser('run', help='Run binary targets.',
            description='This subcommand can be used to run a binary '
                        'target. In order to pass arguments prefixed '
                        'with dashes (e.g. -a or --blah), please add '
                        'a -- argument to prevent further argument '
                        'parsing. For example: "%(prog)s -- binary '
                        'arg0 --arg1"')
    digg.dev.hackbuilder.cli.commands.run.init_argparser(parser_run)

    parser_clean = subparsers.add_parser('clean', help='Clean up the mess.')
    parser_clean.set_defaults(func=do_clean)

    subcommand_parsers = {
            'help': parser_help,
            'build': parser_build,
            'run': parser_run,
            'clean': parser_clean,
            }

    parser_help.set_defaults(func=get_help_parser_handler(parser,
            subcommand_parsers))

    return parser


def get_help_parser_handler(main_parser, subcommand_parsers):
    def do_help(args):
        try:
            subcommand_parser = subcommand_parsers[args.subcommand_name]
            subcommand_parser.print_help()
        except KeyError:
            main_parser.print_help()

    return do_help


def do_clean(args):
    repo_root = os.path.abspath(get_root_of_repo_directory_tree())
    logging.info('Repository root: %s', repo_root)

    normalizer = digg.dev.hackbuilder.target.Normalizer(repo_root)
    build = digg.dev.hackbuilder.build.Build(None, normalizer)
    build.remove_directories()


def get_plugin_modules(requested_plugins):
    plugins = set()
    for requested_plugin in requested_plugins:
        plugin_name = 'digg.dev.hackbuilder.plugins.' + requested_plugin
        logging.info('Loading plugin module: %s', plugin_name)
        module = __import__(plugin_name, fromlist=['buildfile_locals'],
                level=0)
        plugins.add(module)

    return plugins

if __name__ == '__main__':
    main()
