#!/usr/bin/python

import sys
import os

print 'Number of arguments:', len(sys.argv), 'arguments.'
print 'Argument List:', str(sys.argv)

bad_words = ['uid', 'UID']

filenames = os.listdir('ics_files')

print(filenames)

for filename in filenames:
    with open(filename) as oldfile, open('new_' + filename , 'w') as newfile:
        for line in oldfile:
            if not any(bad_word in line for bad_word in bad_words):
                newfile.write(line)

    #  for arg in sys.argv[1:]:
    #      with open(arg) as oldfile, open('new_' + arg , 'w') as newfile:
    #          for line in oldfile:
    #              if not any(bad_word in line for bad_word in bad_words):
    #                  newfile.write(line)
