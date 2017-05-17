#!/usr/bin/python

import sys
import os

print 'Number of arguments:', len(sys.argv), 'arguments.'
print 'Argument List:', str(sys.argv)

words_to_remove = ['uid', 'UID']

for arg in sys.argv[1:]:
    with open(arg) as oldfile, open('new_' + arg , 'w') as newfile:
        for line in oldfile:
            if not any(word_to_remove in line for word_to_remove in words_to_remove):
                newfile.write(line)
    os.remove(arg)

#  filenames = os.listdir('ics_files')
#
#  print(filenames)
#
#  for filename in filenames:
#      with open(filename, 'rt') as oldfile, open('new_' + filename , 'w') as newfile:
#          for line in oldfile:
#              if not any(word_to_remove in line for word_to_remove in to_remove):
#                  newfile.write(line)
