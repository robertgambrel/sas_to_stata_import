# Convert SAS import scripts to STATA import scripts

We had a series of datasets in ASCII format, but the provided import programs were SAS only. Unfortunately, the data was all on Mac-encrypted drives, so we couldn't transfer them to a Windows computer with SAS. This script read through the SAS import script, pulled variable names and formats, and rewrote everything to a new Stata-syntaxed file.

It's likely that some of the choices made here will have to be changed for different data sources, but hopefully this helps get you started.

The import files came from [the Healthcare Cost and Utilization Project](https://www.hcup-us.ahrq.gov/db/nation/nis/nissasloadprog.jsp) and looked [like this](https://www.hcup-us.ahrq.gov/db/nation/nis/tools/pgms/SASLoad_NIS_2013_Core.SAS). My script was tailored to that format specifically, so it uses their coding patterns to consistently translate SAS import commands to Stata, taking into account the fact that variables not only have line indexes but also survey-defined missing value codings and formats. All of these are converted to Stata code and written to a do file.
