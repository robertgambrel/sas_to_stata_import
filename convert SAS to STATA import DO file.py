"""
June 2016
Robert Gambrel

Context: I need to take the SAS import text file and convert it to a STATA 
import do file. They use different syntax but have patterns that should convert 
from one to the other.
"""

import re
import os
import collections

## Changes for USER to Make:

# directory of ASCII Dataset, which is also where SAS code should be and 
# STATA text will be output to
data_directory = '/Users/worker/ASCII_DIRECTORY'
# Name of the SAS script 
sas_script_name = 'original_SAS.sas.txt'
# ASCII name, which will also be recoded as the dataset for STATA to save to
base_name = 'raw ASCII name'

## END THINGS TO CHANGE

os.chdir(data_directory)



# use base name to construct name of ASCII files and output Stata dataset
# use extra quotes so they're saved as strings
ascii_name = '"{}.asc"'.format(base_name)
stata_name = '"{}.dta"'.format(base_name)

# import SAS script
sas = open(sas_script_name, 'r').readlines()

# set up dictionary for recoding missing items
# This is the top section of the SAS dataset. Depending on variable type, different
# values are recoded as missing. This searches them and sets up a list automatically.
# It also looks up each SAS data type (string, int, float) and sets up a corresponding
# Stata data type (char, int, byte)
missing_dict = {}
types_dict = {}
for i in range(0, len(sas)-1):
    line = sas[i]
    # token for start of lines indicating how to recode missing values
    if re.search("INVALUE", line):
        # what is the name for the recode rule
        missing_key = re.findall('INVALUE ([a-zA-Z0-9_]+)', line)[0]
        missing_dict[missing_key] = []
        j = 1
        while True:
            # go line by line until you see ';', which is SAS's end delimiter
            if re.search(';', sas[i+j]):
                break
            # if there's a match for the missing key, add it to a list. If not, 
            # then catch the IndexError and move on
            try: 
                recoded_value = re.findall('\'(-[0-9\.]+)', sas[i+j])[0]
            except IndexError:
                pass
            # the missing are currently coded as strings. Convert to float / 
            # int as appropriate
            if float(recoded_value) % 1 != 0:
                recoded_value = float(recoded_value)
            else:
                recoded_value = int(recoded_value)
            missing_dict[missing_key].append(recoded_value)
            j += 1
        # SAS uses this formatting rule in the import scripts I'm modifying:
        # N#P#F. N# indicates digits before the decimal, P# indicates digits after.
        # So use that to translate to Stata format: long (integer) or byte (float)
        if re.search("N[0-9]+PF", missing_key):
            types_dict[missing_key] = "long"
        elif re.search("N[0-9]+P[0-9]+F", missing_key):
            types_dict[missing_key] = "byte"
        elif re.search("DATE", missing_key):
            types_dict[missing_key] = 'date'


# Set up an empty dictionary. Its keys will be variable names, and each variable 
# will have its own sub-dictionary with keys for variable label, type, recoding, etc.
stata_values = collections.OrderedDict()
line_start = False
        
# use indexing, so I can pull information from subsequent lines when necessary
for i in range(0, len(sas)):
    line = sas[i]
    # "length=" in the line means it's a variable name. Pull the name and length
    if re.search("LENGTH=", line):
        variable_name = re.findall('([a-zA-Z0-9_]+) ', line)[0]
        variable_length = int(re.findall('LENGTH=\$*([0-9]+)', line)[0])
        # Initialize the sub-dictionary
        stata_values[variable_name] = {}
        # add in length
        stata_values[variable_name]['length'] = variable_length
        # labels start at various points. account for some that take two lines, 
        # and some only take one. They can also start 2 lines below, 3 lines below,
        # or directly below
        if re.search("\"", sas[i+2]):
            first_label_line = re.findall("\"(.*)\\n", sas[i+2])[0]
            try:
                second_label_line = re.findall("(.*)\"", sas[i+3])[0]
            except IndexError:
                second_label_line = ''
            variable_label = first_label_line + second_label_line
        elif re.search("\"", sas[i+3]):
            first_label_line = re.findall("\"(.*)\\n", sas[i+3])[0]
            try:
                second_label_line = re.findall("(.*)\"", sas[i+4])[0]
            except IndexError:
                second_label_line = ''
            variable_label = first_label_line + second_label_line
        # single-line labels start directly below
        else:
            variable_label = re.findall("LABEL=\"(.*)\"", sas[i+1])[0]
        # preserver it as a hard string
        stata_values[variable_name]['label'] = '"{}"'.format(variable_label)
        "\"" + variable_label + "\""
    # at the bottom of the file, the @ values indicate starting points, and the 
    # numbers and letters at the end of the line indicate variable type. Pull the 
    # starting points and use the type to convert to Stata type, using the conversion
    # dictionary above
    # example line: @12 Var2 N2P4F.
    if re.search("\@[0-9]+", line):
        variable_name = re.findall("\@[0-9]+\s*([a-zA-Z0-9_]+) ", line)[0]
        variable_start = int(re.findall("\@([0-9]+)", line)[0])
        # base it off the next row if I can. If it's the last one, do start + length, 
        # where length is preserved in the dictionary created above     
        try:
            stop = int(re.findall("\@([0-9]+)", sas[i+1])[0]) - 1
        except IndexError:
            stop = variable_start + stata_values[variable_name]['length']
        stata_values[variable_name]['start'] = variable_start
        stata_values[variable_name]['end'] = stop
        # Find a series of characters before a period - this is the recode key
        recode_key = re.findall("(\S+)\.", line)[0]
        # pull recode key if it exists
        recode_list = missing_dict.get(recode_key, None)
        stata_values[variable_name]['recode_list'] = recode_list
        # pull type; if it's not in the list, assume a character type
        stata_values[variable_name]['type'] = types_dict.get(recode_key, "char")
    # the ASCII raw data might have a line or two at the top with descriptions. 
    # Pull the info in the SAS Import that says which line to start with.
    # Note above line_start was set to False. Immediately below, this condition
    # affects how the beginning of the Stata file is written.
    if re.search("INFILE", line):
        try:
            line_start = re.findall("FIRSTOBS=([0-9]+)", line)[0]
        except IndexError:
            line_start = False

# start writing the output file:
if line_start:
    output_lines = ['clear all', 
                    'cd "{}"'.format(data_directory), 
                    '/// Code to import {}'.format(ascii_name),
                    'infix {} firstlineoffile ///'.format(line_start)]
else:
    output_lines = ['clear all', 
                    'cd "{}"'.format(data_directory), 
                    '/// Code to import {}'.format(ascii_name),
                    'infix ///']
    
# lines to read in data (each line is a type, variable name, start-end, and /// 
# to continue to next line):
for variable in stata_values.keys():
    new_line = '{}    {}    {}-{}  ///'.format(stata_values[variable]['type'],
                                               variable,
                                               stata_values[variable]['start'],
                                               stata_values[variable]['end'])
    output_lines.append(new_line)

# using data source:
output_lines.append('using ' + ascii_name)

# label variables:
for variable in stata_values.keys():
    new_line = 'label var {}    {}'.format(variable, str(stata_values[variable]['label']))
    output_lines.append(new_line)

# recode as needed
for variable in stata_values.keys():
    recode = stata_values[variable].get('recode_list')
    if recode:
        recode = ' '.join(str(item) for item in recode)
        new_line = 'recode {}   ( {} = .)'.format(variable, recode)
        output_lines.append(new_line)
    recode = None
    
# line in STATA script to save the file as a dta
output_lines.append('save {}, replace'.format(stata_name))

# create a new file to write a DO file to
output_file = open('{}.do'.format(base_name), 'w')
output_file.flush()

for line in output_lines:
    output_file.write(line + ' \n')
    
output_file.close()


