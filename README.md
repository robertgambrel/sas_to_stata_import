# Convert SAS import scripts to STATA import scripts

We had a series of datasets in ASCII format, but the provided import programs were SAS only. Unfortunately, the data was all on Mac-encrypted drives, so we couldn't transfer them to a Windows computer with SAS. This script read through the SAS import script, pulled variable names and formats, and rewrote everything to a new Stata-syntaxed file.

It's likely that some of the choices made here will have to be changed for different data sources, but hopefully this helps get you started.
