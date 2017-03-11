#!/usr/bin/env python
'''
log visualizer.
'''

import os
import sys

from core import parser
from core import viz
from module import ModuleController as mc


def main(log_type, sub_type, in_log, output_path):
    module = mc().get_module(log_type, sub_type)
    inlog = parser.Parser(in_log, module)
    logviz = viz.Visualization(inlog.get_info(), module)
    logviz.save(output_path, output_type=viz.Visualization.PDF_OUTPUT)


def set_include_path():
    include_path = os.path.abspath("./")
    sys.path.append(include_path)

if __name__ == "__main__":
    set_include_path()

    if not os.path.isfile(sys.argv[3]):
        raise Exception('Cannot find log file {}'.format(sys.argv[2]))

    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
