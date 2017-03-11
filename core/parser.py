#!/usr/bin/env python
'''
:mod:`core.parser` is a module containing class for parsing log files.
'''

import mmap
import os
import re
import traceback
import platform
from types import ListType

from module import ModuleController as mc

class Parser(object):
    '''
    Parser for benchmark outputs.
        :param filename: Name of the log file
        :type filename: str.
        :param module: Current module used to parse file
        :type module: object.
    '''

    def __init__(self, filename='', module=None):
        if module is None:
            raise Exception("Should choose a module to parse the log file.")
        self._info = {}
        self._module = module
        self.__filename = filename

        return None

    def load_file(self):
        '''
        Loads logfile.
            :return: ``True`` if loading and parsing of file went fine, \
            ``False`` if it failed (at any point)
        '''

        # We first split file into pieces
        searchunks = self._split_file()

        if searchunks:

            # And then we parse pieces into meaningful data
            self._info = self._parse_file(searchunks)

            return True

        else:
            return False

    def get_info(self):
        '''
        Returns parsed info
            :return: ``Dictionary``-style list of data
        '''

        file_parsed = self.load_file()
        if file_parsed:
            return self._info
        else:
            return False

    def _split_file(self):
        '''
        Splits log file (in ASCII format) in order to accelerate processing speed.
            :param data: Input data instead of file
            :type data: str.
            :return: ``List``-style of file sections
        '''

        # Filename passed checks through __init__
        if self.__filename and os.access(self.__filename, os.R_OK):

            fhandle = None

            try:
                fhandle = os.open(self.__filename, os.O_RDONLY)
            except OSError:
                raise Exception(("Couldn't open file {}".format(self.__filename)))

            if fhandle:

                datalength = 0

                # Dealing with mmap difference on Windows and Linux
                if platform.system() == 'Windows':
                    dataprot = mmap.ACCESS_READ
                else:
                    dataprot = mmap.PROT_READ

                try:
                    if platform.system() == 'Windows':
                        parmap = mmap.mmap(
                            fhandle, length=datalength, access=dataprot
                        )
                    else:
                        parmap = mmap.mmap(
                            fhandle, length=datalength, prot=dataprot
                        )
                except (TypeError, IndexError):
                    os.close(fhandle)
                    traceback.print_exc()
                    return False

                # Here we'll store chunks of file, unparsed
                searchunks = []
                oldchunkpos = 0
                dlpos = parmap.find(self._module.delimeter(), 0)
                size = 0

                # We can do mmap.size() only on read-only mmaps
                size = parmap.size()

                while dlpos > -1:  # mmap.find() returns -1 on failure.

                    tempchunk = parmap.read(dlpos - oldchunkpos)
                    searchunks.append(tempchunk.strip())

                    # We remember position, add 2 for 2 DD's
                    # (newspaces in production). We have to remember
                    # relative value
                    oldchunkpos += (dlpos - oldchunkpos) + 2

                    # We position to new place, to be behind \n\n
                    # we've looked for.
                    try:
                        parmap.seek(2, os.SEEK_CUR)
                    except ValueError:
                        print(("Out of bounds ({})!\n".format(parmap.tell())))
                    # Now we repeat find.
                    dlpos = parmap.find(self._module.delimeter())

                # If it wasn't the end of file, we want last piece of it
                if oldchunkpos < size:
                    tempchunk = parmap[(oldchunkpos):]
                    searchunks.append(tempchunk.strip())

                parmap.close()

            if fhandle != -1:
                os.close(fhandle)

            if searchunks:
                return searchunks
            else:
                return False

        return False

    def _parse_file(self, parts):
        '''
        Parses splitted file to get proper information from split parts.
            :param sar_parts: Array of SAR file parts
            :return: ``Dictionary``-style info (but still non-parsed) \
                from SAR file, split into sections we want to check
        '''
        pattern = None
        # If parts is a list
        if type(parts) is ListType:
            pattern = self._module.pattern()

            if pattern is None:
                return False

            results = []
            for part in parts:
                matches = pattern.finditer(part)
                for matchNum, match in enumerate(matches):
                    result = {key:match.group(pattern.groupindex[key]) for key in pattern.groupindex}
                    results.append(result)
            output = self.__split_info(results)
            del(parts)

            # Now we have parts pulled out and combined, do further
            # processing.
            # cpu_output = self.__split_info(cpu_usage, PART_CPU)

        return output

    def __find_column(self, column_names, part_first_line):
        '''
        Finds the column for the column_name in sar type definition,
        and returns its index.
            :param column_name: Names of the column we look for (regex) put in
                the list
            :param part_first_line: First line of the SAR part
            :return: ``Dictionary`` of names => position, None for not present
        '''
        part_parts = part_first_line.split()

        ### DEBUG
        #print("Parts: %s" % (part_parts))

        return_dict = {}

        counter = 0
        for piece in part_parts:
            for colname in column_names:
                pattern_re = re.compile(colname)
                if pattern_re.search(piece):
                    return_dict[colname] = counter
                    break
            counter += 1

        # Verify the content of the return dictionary, fill the blanks
        # with -1s :-)
        for colver in column_names:
            try:
                tempval = return_dict[colver]
                del(tempval)
            except KeyError:
                return_dict[colver] = None

        return(return_dict)

    def __split_info(self, parts):
        '''
        Maps parts into logical stuff
        :param parts: Parts to map into usable data
        :return: ``List``-style info from files, now finally \
            completely parsed into meaningful data for further processing
        '''
        # Common assigner

        return self._module.split_info(parts)
