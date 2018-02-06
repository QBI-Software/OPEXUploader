# OPEXUploader
Data upload to XNAT modules for OPEX project

## Quick Guide for Data Uploads

### Settings

#### Database

On first use, you will need to add your XNAT login details.

1. From the Menu, select "Settings" then "Database"
1. In the dropdown box, enter a name for the db config (eg 'opex')
1. Enter username and password
1. **Save**

Note this file is saved in your user home directory, called '.xnat.cfg'

#### Incorrect IDs

1. From the Menu, select "Settings" then "Incorrect IDs"
1. To change a value, just click in the box then click **Save**
1. To add a new value, click on Add, to add a new row, then enter values, and **Save**
1. To remove a value, clear the data then click **Save**

### Getting started

**Test the connection** first after selecting the database configuration and entering the project code (eg 'P1').  

Before a run, it is good to check **TEST RUN** to ensure data is OK - it will not be loaded to the database.  Note, that datafiles must be closed if being viewed in Excel. (See Setup for initial use.)

The following steps refer to the **XnatUploaded** directory on the share drive.  It is best to copy the main data files here except for MRI scans, and Amunet and COSMED subdirectories which are too large.

All data upload is recorded in a log file in your user directory called logs/xnatupload.log.

### CANTAB data (XnatUploaded/sampledata/cantab)

Downloaded excel sheet called 'RowBySession' should be copied into this directory.

1. Select this directory as input
1. Select 'CANTAB' from the Data Type dropdown
1. Check 'Skip ABORTED'
1. Click 'RUN'

### AMUNET data (XnatUploaded/sampledata/amunet)

**aka Virtual Human Water Maze (vHWM)**

Interval subdirectories have been created (0m, 3m, 6m, 9m, 12m).

1. Copy appropriate Excel files into the subdirectories (Amunet1 and Amunet2 are split).
1. Check the file path is correct in the file called 'folderpath.txt' in each subdirectory - this is where the original files are and the script gets the dates from the filenames.
1. Select 'AMUNET' from the Data Type dropdown
1. Click 'RUN'

### ACER data (XnatUploaded/sampledata/acer)

Copy data file to this directory.  Add a column for the visit interval called 'Visit' and set to value of 0,3,6,9 or 12 as appropriate. Then click 'RUN'. (NB a lot of this data has been entered manually.)

### Blood data (XnatUploaded/sampledata/blood)

Copy data files to appropriate subdirectories ('COBAS', 'MULTIPLEX','ELISAS'), then select the subdirectory eg XnatUploaded/sampledata/blood/COBAS as Input.

1. Check that headings are in the second row (eg Prolactin, etc) although the script should rename them if the columns are still in the same order
1. Select 'BLOOD' from the Data Type dropdown
1. Click 'RUN'

### COSMED data (XnatUploaded/sampledata/cosmed)

The COSMED data is uploaded from the original COSMED data directory.  

1. Use the input directory as 'XnatUploaded/sampledata/cosmed'
1. A text file in this directory called 'xnatpaths.txt' gives the actual COSMED directory to use, the subdirectory for individual files and the name of the datafile.  Check the paths are correct before running.   
1. An output of the compiled COSMED data is produced.
1. Also time-series data for individual files is generated into a subdirectory in the original data directory called 'processed'.

### DASS data (XnatUploaded/sampledata/dass)

1. Copy data file (DASS Data Entry Plus Check_20171206.xlsx) to this directory from share drive (\DATA\DATA ENTRY\PaperBasedPdfs\PaperBasedExcelSheets\DASS)
1. Set input directory to this directory
1. Select 'DASS' from the Data Type dropdown
1. Click 'RUN'

### DEXA data (XnatUploaded/sampledata/dexa)

1. Copy data file (DXA Data entry_20171215.xlsx) to this directory from share drive (\DATA\DXA Data)
1. Set input directory to this directory
1. Select 'DEXA' from the Data Type dropdown
1. Click 'RUN'


### MRI Scans (XnatUploaded/sampledata/mri)

MRI scans must be sorted into their series before uploading so this is a two step process.

#### Scans Organizer

1. From the Menu, select "Functions" then "MRI Scans Organizer"
1. Check OPEX IDs (default is checked)
1. Enter the raw data directory as input (eg \DATA\7TMRIData\raw for baseline and \DATA\7TMRIData\raw_06 for 6mth)
1. Select one of two subdirectories ('sorted_0m', 'sorted_6m') in the sampledata/mri directory as output depending on baseline or 6mth scan.
1. Previous uploads can be ignored by adding the 'done' directories (sampledata\mri\done_0m or sampledata\mri\done_6m)
1. The 'done' directory is where the files will be moved after uploading.
1. When complete, move the files to the appropriate done_0m or done_6m directory.
1. Click 'RUN'

#### MRI upload

1. Select the 'sorted_0m' or 'sorted_6m' directory
1. Select MRIscans from the Data Type dropdown
1. Click 'RUN'

Both steps involve the script copying scans around 5GB in total which can take around 15-30 mins per participant depending on the network.  Checking the log file regularly will let you know how it's going.

### MRI data (XnatUploaded/sampledata/mridata)

Both ASHS and Freesurfer hippocampal volume data can be uploaded.  (NB, Fields for cortical volumes are still under discussion)

1. Copy data file to this directory and rename if necessary with 'ASHS' or 'FreeSurf' in the filename
1. Two additional columns are required: 'Subject' and 'Visit'
1. Click 'RUN'

### Visits (XnatUploaded/sampledata/visit)

Some experimental data is not accompanied by the visit date: 
+ all bloods
+ DEXA
+ DASS
+ MRIdata (FS or ASHS) 
+ FMRI

so it is extracted from the participants file after these data have been uploaded.  This file cannot be used directly however as it is full of inconsistent data.

1. Copy data file ('Participant visit record_20171110.xlsx') to this directory from share drive (\CENTRE ADMIN\PARTICIPANTS)
1. Save to a new file called 'Visits.xlsx' (can overwrite)
1. A new line of headers needs to be added - see the existing file 'Visits.xlsx'
1. Insert a new column called BLOOD_FASTED_3 which has the same values as DEXA_3 (3mth Assessment)
1. A LOT of data will need cleaning up which I have done via Excel "find and replace" and "formats -> date -> yyyy-mm-dd" (if in doubt, leave it out)

Only experiments which exist in the database will be updated and only if the date is different so a comment "Date updated" is entered which can be checked on XNAT.

### FMRI data (XnatUploaded\sampledata\spreadsheet_upload)

When data is able to match the headings directly, it is quicker to use XNAT's Spreadsheet upload option.  Guidelines for this are in the OPEX XNAT User guide.  It mostly involves setting up the columns in the right order with the headers matching the template exactly.  

If an ID is to be generated, it is usually:

```
=CONCATENATE(prefix,"_",subjectid, "_",interval)

```


## General Housekeeping

1. Reports are created in the report directory showing missing and matched participants - these should be checked and any repeated incorrect IDs can be added to the file called 'incorrectIds.csv' in the application resources directory.
1. Once uploaded, it is good to move the file into the 'done' directory

## Other Options

### Create Subjects from Data

If the subject doesn't exist, this will create it in the database. Generally, this isn't used in case there are often errors in the Participant IDs and thus incorrect data entry.

### Update existing data

This will reload the data over existing data.  This is useful, for example, with the MRIdata (hippocampal volumes) where there have been improvements in the methods.

### Download CSVs

This function generates CSV files for each experiment type.  They are currently used for statistics and is a lot quicker than downloading the data via XNAT.

1. From the File Menu, Select "Download CSVs"
1. Check the "Deltas" if you also want the changes between intervals (per individual - note that baseline data remains the same)
1. Select the Output directory
1. Click on **'Download'**

### Generate Reports

This generates reports of processed data, grouped by parameter or group (AIT,MIT,LIT) for further analysis. Currently, just Blood and CANTAB data.

1. From the File Menu, Select "Generate Reports"
1. Check the "Deltas" if you also want the changes between intervals
1. Select the Output directory
1. Click on **'Generate'**