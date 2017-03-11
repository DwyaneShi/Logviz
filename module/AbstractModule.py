#!/usr/bin/env python
'''
:mod:`module.AbstractModule`
'''

class AbstractModule(object):
    '''
    AbstractModule lists the methods that needs to implement.
    '''
    def delimeter(self):
        raise NotImplementedError("Should have implemented this method")
    def pattern(self):
        raise NotImplementedError("Should have implemented this method")
    def split_info(self, parts):
        raise NotImplementedError("Should have implemented this method")

    def num_plots(self):
        raise NotImplementedError("Should have implemented this method")
    def xy_data(self, data):
        raise NotImplementedError("Should have implemented this method")
    def preprocess_data(self, data):
        raise NotImplementedError("Should have implemented this method")
    def paint(self, fig):
        raise NotImplementedError("Should have implemented this method")
