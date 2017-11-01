# -*- coding: utf-8 -*-
"""
CW-Manage-Dashboard

handler.lambda_handler calls .lib/cw_dashboard.py

TO DO: None
"""


import os


def lambda_handler(event, context):
    """Entry Point"""
    execute_main()


def execute_main():
    """Calls cw_dashboard.py"""
    from lib.cw_dashboard import main
    main()


if __name__ == '__main__':
    # ensures the cwd is root of project
    __WS_DIR__ = os.path.dirname(os.path.realpath(__file__))
    os.chdir('{}/..'.format(__WS_DIR__))
    lambda_handler(None, None)
