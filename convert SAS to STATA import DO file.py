# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 23 11:39:36 2016

@author: Bobby Gambrel

Context: Carrie has HCUP data but no way to import it to Stata. I need to 
take the SAS inport text file and convert it to a STATA import do file. They use 
different syntax but have patterns that should convert from one to the other.
"""

import re
import os
import collections

# THINGS FOR CARRIE TO CHANGE:

# directory of ASCII Dataset, which is also where SAS code should be and 
# STATA text will be output to
os.chdir('/Users/healthpolicyanalyst/Documents/Box Sync/python/Carrie\'s HCUP data')
# Name of the SAS script (which is also the name of the ASCII file), 
# without file extension
base_name = "FL_SID_2014_CORE"


## END THINGS TO CHANGE




# use base name to construct name of ASCII files and output Stata dataset
ascii_name = "\"" + base_name + ".asc\""
stata_name = "\"" + base_name + ".dta\""
sas_script_name = base_name + ".sas"


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
    if re.search("INVALUE", line):
        missing_key = re.findall('INVALUE ([a-zA-Z0-9_]+) ', line)[0]
        missing_dict[missing_key] = []
        j = 1
        while True:
            if re.search('OTHER', sas[i+j]):
                break
            recoded_value = re.findall('\'(-[0-9\.]+)', sas[i+j])[0]
            if float(recoded_value) % 1 != 0:
                recoded_value = float(recoded_value)
            else:
                recoded_value = int(recoded_value)
            missing_dict[missing_key].append(recoded_value)
            j += 1
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
        
# use indexing, so I can pull following lines together
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
        # labels start at various points. account for some that take one line, some take 2
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
            variable_label = first_label_line + second_label_line
        else:
            variable_label = re.findall("LABEL=\"(.*)\"", sas[i+1])[0]
        stata_values[variable_name]['label'] = "\"" + variable_label + "\""
    # at the bottom of the file, the @ values indicate starting points, and the 
    # numbers and letters at the end of hte line indicate variable type. Pull the 
    # starting points and use the type to convert to Stata type, using the conversion
    # dictionary above
    if re.search("\@[0-9]+", line):
        variable_name = re.findall("\@[0-9]+\s*([a-zA-Z0-9_]+) ", line)[0]
        variable_start = int(re.findall("\@([0-9]+)", line)[0])
        # base it off the next row if I can. If it's the last one, do start + length       
        try:
            stop = int(re.findall("\@([0-9]+)", sas[i+1])[0]) - 1
        except IndexError:
            stop = variable_start + stata_values[variable_name]['length']
        stata_values[variable_name]['start'] = variable_start
        stata_values[variable_name]['end'] = stop
        # Find a series of characters before a period
        recode_key = re.findall("(\S+)\.", line)[0]
        # pull recode key if it exists
        recode_list = missing_dict.get(recode_key, None)
        stata_values[variable_name]['recode_list'] = recode_list
        # pull type; if it's not in the list, assume a character type
        stata_values[variable_name]['type'] = types_dict.get(recode_key, "str")
    if re.search("INFILE", line):
        line_start = re.findall("FIRSTOBS=([0-9]+)", line)[0]

# start writing the output file:
if line_start:
    output_lines = ['clear all', 'cd \"/Volumes/NEO Patrick Reserach /Kentucky SID/KY SID 2013\"', "/// Code to import " + ascii_name,'infix ' + line_start + ' firstlineoffile ///']
else:
    output_lines = ['clear all', 'cd \"/Volumes/NEO Patrick Reserach /Kentucky SID/KY SID 2013\"', "/// Code to import " + ascii_name,'infix ///']
    
# lines to read in data (each line is a type, variable name, start-end, and /// 
# to continue to next line):
for variable in stata_values.keys():
    new_line = (stata_values[variable]['type'] + "   " + variable +'    ' +
                str(stata_values[variable]['start']) + '- ' + 
                str(stata_values[variable]['end']) + "  ///")
    output_lines.append(new_line)

# using data source:
output_lines.append('using ' + ascii_name)

# label variables:
for variable in stata_values.keys():
    new_line = ("label var " + variable +'    ' +
                str(stata_values[variable]['label']))
    output_lines.append(new_line)

# recode as needed
for variable in stata_values.keys():
    recode = stata_values[variable].get('recode_list')
    if recode:
        recode = ' '.join(str(item) for item in recode)
        new_line = ("recode " + variable + "   (" +
                    recode + " = .)" )
        output_lines.append(new_line)
    recode = None
    
# save the file
output_lines.append("save " + stata_name + ", replace")

# create a new file to write a DO file to
output_file = open(base_name+'.do', 'w')
output_file.flush()

for line in output_lines:
    output_file.write(line + ' \n')
    
output_file.close()


