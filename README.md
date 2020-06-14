# OPEXUploader
A user's guide for data upload to XNAT modules for the OPEX project.

This can be viewed directly in the OPEX Uploader App under Help.

## User Guide for Data Uploads

### Settings

A few settings are required for use of the OPEX Uploader.

#### Database

On first use, you will need to setup your XNAT login details (and you will need admin privileges in XNAT).

1. From the Menu, select "Settings" then "Database"
1. In the dropdown box, enter a name to describe this connection (eg 'opex' or 'dev-opex')
1. Enter username and password (these are stored in plain text so ensure you do not re-use important passwords here)
1. **Save**

Note this file is saved in your user home directory, called '.xnat.cfg'.

Multiple connections can be entered here.

#### Incorrect IDs

Occasionally, Subject IDs are not entered in the same format as XNAT or have been mis-typed.  
The OPEX Uploader will not "guess" an ID if it cannot find it in XNAT - it will however, report these unfound IDs in a file at the end of the upload called `missing.csv` in a directory called 'report'.
If possible, change the entry in the data files. Otherwise, the incorrect ID can be entered here and it will be automatically mapped to the correct Subject ID during upload (for all datatypes).  

1. From the Menu, select "Settings" then "Incorrect IDs"
1. To change a value, just click in the box then click **Save**
1. To add a new value, click on Add, then enter values, and **Save**
1. To remove a value, clear the data then click **Save**

### Getting started

**Test the connection** first 

1. select the database configuration
1. enter the project code (eg 'P1').
1. click **Test Connection**  

#### Data File Locations
The paths listed in the parentheses below refer to the **XnatUploaded** directory on the share drive.  It is best to copy the main data files here except for MRI scans, and Amunet and COSMED subdirectories which are too large.

All data upload is recorded in a log file in your user directory called `logs/xnatupload.log` which can be viewed in the OPEX Uploader by clicking on the 'VIEW LOG' button.

#### TEST Run
Before a run, do a trial run to ensure data is OK and there are no errors. 
The data will be extracted from the required datafiles, and formatted ready for upload to XNAT but the data will not actually be uploaded:
1. check **TEST RUN only**
1. click **RUN**

**Note, on Windows, datafiles to be uploaded must be closed before the run if they are being viewed in Excel.**

#### Upload data
Once files are in place, to upload them to XNAT, the procedure is:

1. Select the `Database config` (connection)
1. Enter the `project code` (eg P1)
2. Select the required datatype from the `Data Type dropdown`
1. Select the directory containing the files for upload for `Input data directory`
3. Click 'RUN'

Specific details for each datatype are noted below.

#### Updating existing data
Normally, on data upload, each Sample ID is checked to see if it already exists in XNAT and if so, the data is skipped.  This is to ensure the data in XNAT is not overwritten as it can be manually edited in XNAT directly and this should remain the 'Source of Truth'.

However, if a sample has data that was incorrect on upload or has been analysed differently and the data in XNAT **is** to be overwitten

1. Check 'Update existing data for selected experiment type'
1. Click 'RUN'

### CANTAB data (XnatUploaded/sampledata/cantab)

Downloaded excel sheet called 'RowBySession' should be copied into this directory.

1. Select this directory as input
1. Select 'CANTAB' from the Data Type dropdown
1. [OPTIONAL] If new subjects are present, check 'Create Subjects from CANTAB' to automatically generate new Subjects (use with caution)
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

There are several types of BLOOD sample data:
1. COBAS
2. MULTIPLEX
3. ELISAS
4. INFLAM (Inflammation)
5. IGF
6. SOMATO (Somatostatin)

Make sure the data files are stored in folders of the same name (the naming of the files doesn't matter) eg:
```shell script
├── sampledata
|   └── blood
|       ├── COBAS 
|         └── Cobas_datafile.xlsx
|       ├── MULTIPLEX 
|         └── Multiplex_datafile.xlsx
```
In the OPEX Uploader, select the subdirectory as Input, eg `sampledata/blood/COBAS` 

#### Data formatting
1. The field names for all blood types are in `blood_fields.csv` - https://github.com/QBI-Software/OPEXUploader/blob/master/resources/fields/blood_fields.csv
1. For COBAS, check that the headings are in the SECOND row (eg Prolactin, Insulin etc) in the Excel file  
1. For ELISAS and SOMATO, check that the data is in the THIRD TAB in the Excel file

#### Upload with OPEX Uploader
1. Select 'BLOOD' from the Data Type dropdown
1. Select the subdirectory as Input, eg `sampledata/blood/COBAS` 
1. Click 'RUN'

### COSMED data (XnatUploaded/sampledata/cosmed)

The COSMED data is uploaded from the original COSMED data directory.  

1. Use the input directory as 'XnatUploaded/sampledata/cosmed'
1. A text file in this directory called 'xnatpaths.txt' gives the actual COSMED directory to use, the subdirectory for individual files and the name of the datafile.  Check the paths are correct before running.   
1. An output of the compiled COSMED data is produced.
1. Also time-series data for individual files is generated into a subdirectory in the original data directory called 'processed'.

### DEXA data (XnatUploaded/sampledata/dexa)

1. Copy data file (DXA Data entry_20171215.xlsx) to this directory from share drive (\DATA\DXA Data)
1. Set input directory to this directory
1. Select 'DEXA' from the Data Type dropdown
1. Click 'RUN'

### DASS data (XnatUploaded/sampledata/dass)

1. Copy data file (DASS Data Entry Plus Check_20171206.xlsx) to this directory from share drive (\DATA\DATA ENTRY\PaperBasedPdfs\PaperBasedExcelSheets\DASS)
1. Set input directory to this directory
1. Select 'DASS' from the Data Type dropdown
1. Click 'RUN'


### GODIN data (XnatUploaded/sampledata/godin)

1. Copy data file (GODIN_Data_entry_180717.xlsx) to this directory from share drive (\DATA\DATA ENTRY\PaperBasedPdfs\PaperBasedExcelSheets\GODIN)
1. Set input directory to this directory
1. Select 'GODIN' from the Data Type dropdown
1. Click 'RUN'

### Insomnia (ISI) data (XnatUploaded/sampledata/insomnia)

1. Copy data file (ISI Data Entry 20180206.xlsx) to this directory from share drive (\DATA\DATA ENTRY\PaperBasedPdfs\PaperBasedExcelSheets\ISI Data Entry)
1. Set input directory to this directory
1. Select 'Insomnia' from the Data Type dropdown
1. Click 'RUN'

### PSQI data (XnatUploaded/sampledata/psqi)

1. Copy data file (PSQI data entry 20180206.xlsx) to this directory from share drive (\DATA\DATA ENTRY\PaperBasedPdfs\PaperBasedExcelSheets\PSQI Data)
1. Set input directory to this directory
1. Select 'PSQI' from the Data Type dropdown
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

1. Copy data file to this directory and **ensure either 'ASHS' or 'FreeSurf' is in the filename**
1. Two additional columns are required: 
    - 'Subject' : containing Subject IDs as found in XNAT 
    - 'Visit' or 'interval': sample collection interval as integer (eg 6 for 6 mth)
    - 'version': [OPTIONAL] if a new method is being used and the data is not to be overwritten for the same sample, enter a code here which will be appended to the sample id
1. For the Input data directory, browse to the directory containing the data files
1. In the OPEX uploader, select 'ASHS and Freesurfer' from the Data Type dropdown
1. Click 'RUN'

### FMRI data

There are several types of FMRI data. 

1. MRI analysis data - fMRI behaviour (FMRI)
1. MRI analysis data - fMRI Task Encoding (TASKENCODE)
1. MRI analysis data - fMRI Task Retrieval (TASKRET)
                  
As the upload data is in a machine-readable format, either the OPEX Uploader App or the XNAT Spreadsheet upload functionality can be used.

#### Upload via OPEX Uploader
1. Format the data for upload:
    - If necessary, replace the data headings with those in the `MRI_fields.csv` file: https://github.com/QBI-Software/OPEXUploader/blob/master/resources/fields/MRI_fields.csv
    - For FMRI data, the FMRImap data headings can be used instead
    - For TASKRET and TASKENCODE data, the parser expects 3 tabs (Bind, Bind3, Bind5) in an XLSX file - if these are not present, add empty ones
1. If a new method is being used, to prevent overwriting original data, add a 'version' column with a code eg 'J2020' which will be appended to the SampleID and added to the comments field.
1. In the OPEX Uploader app, select the required data type from the dropdown list (see above abbreviations)
1. Select the data folder (the name doesn't matter nor do the filenames)
1. Click 'RUN'

#### Upload via the XNAT Spreadsheet uploader (XnatUploaded\sampledata\spreadsheet_upload)

When data is able to match the headings directly, it is possible to use the Spreadsheet upload option in XNAT.  
Guidelines for this are in the OPEX XNAT User guide.  

- Instructions are here:  https://wiki.xnat.org/documentation/how-to-use-xnat/upload-experiment-data-via-spreadsheet
- Download the template for opex:fmritaskret
- The template shows the exact names and order required for the data headers
- To provide a generated ID, this base formula can be added in Excel in the ID column:

```
=CONCATENATE(prefix,"_",subjectid, "_",interval)

```



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
1. A LOT of data will need cleaning up which can be done via Excel "find and replace" to remove comments in number columns, etc 
- in Excel for the date columns, change "formats -> date -> yyyy-mm-dd"

Only experiments which exist in the database will be updated and only if the date is different so a comment "Date updated" is entered which can be checked on XNAT.


### Batch Upload

There is now an option to combine regular data uploads.  Follow the guidelines in the sections below to put the correct data files in the ```XnatUploaded/sampledata``` folders (this should then be entered in the Input directory field).  Select the **Bulk Upload** option from the Data Type dropdown and click 'RUN'.

These datasets are currently included:

1. CANTAB
1. DEXA
1. DASS
1. GODIN
1. INSOMNIA
1. PSQI
1. BLOODS (all)
1. Visits (final)


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
1. Check the "Deltas" if you also want the changes from baseline
1. Select the Output directory
1. Click on **'Generate'**

### View Logs

View more details about the processing from the log file which is generated each run and can be viewed from locally via a text editor (under your user home directory in subdirectory 'logs') or via the File Menu.

1. From the File Menu, Select "View Logs"
1. Scroll down to the bottom for the most recent entry
1. Close and re-open to refresh
