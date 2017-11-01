# -*- coding: utf-8 -*-
"""
Return from Lambda
"""


import os

if __name__ == '__main__':
    # ensures the cwd is root of project
    __WS_DIR__ = os.path.dirname(os.path.realpath(__file__))
    os.chdir('{}/..'.format(__WS_DIR__))

    # execute lambda_handler
    from handler import lambda_handler
    lambda_handler(None, None)
