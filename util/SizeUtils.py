#!/usr/bin/env python
def convert_size(string):
    if string[-2:] == 'KB':
        return float(string[:-2]) * 1024
    if string[-2:] == 'MB':
        return float(string[:-2]) * 1024 * 1024
    if string[-2:] == 'GB':
        return float(string[:-2]) * 1024 * 1024 * 1024
def number_to_size(num):
    string = "{}B".format(num)
    if num >= 1024 and num % 1024 == 0:
        num /= 1024
        string = "{}KB".format(num)
    if num >= 1024 and num % 1024 == 0:
        num /= 1024
        string = "{}MB".format(num)
    if num >= 1024 and num % 1024 == 0:
        num /= 1024
        string = "{}GB".format(num)
    return string
