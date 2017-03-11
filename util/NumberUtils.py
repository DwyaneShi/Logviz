#!/usr/bin/env python
def as_number_otherwise_string(string):
    try:
        return int(string)
    except:
        try:
            return float(string)
        except:
            return string
