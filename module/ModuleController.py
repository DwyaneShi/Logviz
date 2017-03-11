#!/usr/bin/env python
'''
:mod:`module.ModuleController` is a module controller for creating instances
of all modules in this project.
'''

import importlib as im

class ModuleController(object):
    '''
    Create instances.
    '''

    def __init__(self):
        self.instances = {}

    def get_module(self, module_name, sub_type):
        if module_name not in self.instances:
            module = im.import_module("module")
            try:
                clazz = getattr(module, module_name)
            except:
                raise Exception("{} is not an available module now.".format(module_name))
            self.instances[module_name] = clazz(sub_type)
        return self.instances[module_name]
