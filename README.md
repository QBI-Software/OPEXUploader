# OPEXUploader
Data upload to XNAT modules for OPEX project

## Quick Guide for Data uploads

**Test the connection** first after selecting the database configuration and entering the project code (eg 'P1').  Before a run, it is good to check **TEST RUN** to ensure data is OK.  Note, that datafiles must be closed if being viewed in Excel. (See Setup for initial use.)

The following steps refer to the XnatUploaded directory on the share drive.  It is best to copy the main data files here except for MRI scans, and Amunet and COSMED subdirectories which are too large.

All data upload is recorded in a log file in your user directory called logs/xnatupload.log.

### CANTAB data (XnatUploaded/sampledata/cantab)

Downloaded excel sheet called 'RowBySession' should be copied into this directory.

1. Select this directory
1. Check 'Skip ABORTED'
1. Click 'RUN'

### AMUNET data (XnatUploaded/sampledata/amunet)

**aka Virtual Human Water Maze (vHWM)**

Interval subdirectories have been created (0m, 3m, 6m, 9m, 12m).

1. Copy appropriate Excel files into the subdirectories (Amunet1 and Amunet2 are split).
1. Check the file path is correct in the file called 'folderpath.txt' in each subdirectory - this is where the original files are and the script gets the dates from the filenames.
1. Click 'RUN'

### ACER data (XnatUploaded/sampledata/acer)

Copy data file to this directory.  Add a column for the visit interval called 'Visit' and set to value of 0,3,6,9 or 12 as appropriate. Then click 'RUN'. (NB a lot of this data has been entered manually.)

### Blood data (XnatUploaded/sampledata/blood)

Copy data files to appropriate subdirectories ('COBAS', 'MULTIPLEX','ELISAS'), then select the subdirectory eg XnatUploaded/sampledata/blood/COBAS as Input.

1. Check that headings are in the second row (eg Prolactin, etc) although the script should rename them but any changes may cause errors
1. Click 'RUN'

###

###

## General Housekeeping

1. Reports are created in the report directory showing missing and matched participants - these should be checked and any repeated incorrect IDs can be added to the file called 'incorrectIds.csv' in the application resources directory.
1. Once uploaded, it is good to move the file into the 'done' directory