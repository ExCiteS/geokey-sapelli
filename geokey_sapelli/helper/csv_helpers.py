"""
Safely deal with unicode (utf-8) in csv files removing nasty BOM surprises

Based on: http://stackoverflow.com/a/6187936/1084488
Modifications by Matthias Stevens, post here: http://stackoverflow.com/a/34257200/1084488
"""

import csv
import codecs


class UnicodeCsvReader(object):
    def __init__(self, csv_file, encoding='utf-8', **kwargs):
        if encoding == 'utf-8-sig':
            # convert from utf-8-sig (= UTF8 with BOM) to plain utf-8 (without BOM):
            self.csv_file = codecs.EncodedFile(csv_file, 'utf-8', 'utf-8-sig')
            encoding = 'utf-8'
        else:
            self.csv_file = csv_file
        self.csv_reader = csv.reader(self.csv_file, **kwargs)
        self.encoding = encoding

    def __iter__(self):
        return self

    def next(self):
        # read and split the csv row into fields
        row = self.csv_reader.next() 
        # now decode
        return [unicode(cell, self.encoding) for cell in row]

    @property
    def line_num(self):
        return self.csv_reader.line_num

class UnicodeDictReader(csv.DictReader):
    def __init__(self, csv_file, encoding='utf-8', fieldnames=None, **kwds):
        reader = UnicodeCsvReader(csv_file, encoding=encoding, **kwds)
        csv.DictReader.__init__(self, reader.csv_file, fieldnames=fieldnames, **kwds)
        self.reader = reader
