#!/usr/bin/env python
"""
Simple wrapper for main SfePy commands (scripts).

Available [commands] are dynamically defined by presence *.py scripts
in pre-defined directory ``scripts-common``.
"""

import os.path as op
import glob
import argparse
import subprocess

import sfepy


def main():

    cmd_list = get_commands()

    parser = argparse.ArgumentParser(
        description='Simple wrapper for main SfePy commands.',
        version='%(prog)s' + sfepy.__version__,
        usage='%(prog)s [command] [options]'
    )

    parser.add_argument(
        '-w',
        '--window',
        help='use alternative (pythonw) interpreter',
        action='store_true',
        dest='py_cmd'
    )

    parser.add_argument(
        'command',
        choices=cmd_list.keys(),
        help='Available SfePy command(s).')

    parser.add_argument(
        'options',
        nargs=argparse.REMAINDER,
        help='Additional options passed directly to selected [command].')

    py_cmd = 'python' if not parser.parse_args().py_cmd else 'pythonw'
    command = parser.parse_args().command
    options = ', '.join(parser.parse_args().options)

    args = [py_cmd, cmd_list[command], options]

    subprocess.call(args)


def get_commands():
    """
    Get available commands (and corresponding scripts) for SfePy wrapper.

    Commands are dynamically defined by presence *.py scripts in pre-defined
    directory ``scripts-common``.

    :rtype : dict { command: path_to_script }
    """

    bin_dir = 'scripts-common'
    if not sfepy.in_source_tree:
        bin_dir = op.normpath(op.join(sfepy.data_dir, bin_dir))

    scripts = glob.glob(op.normpath(op.join(bin_dir, '*.py')))
    cmd = [op.splitext(op.basename(i))[0] for i in scripts]

    commands = dict(zip(cmd, scripts))

    return commands


if __name__ == '__main__':
    main()
