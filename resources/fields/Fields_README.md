## Adding new or updating fields 
For new datatypes, a new table is added to the XNAT database.
This requires modification of the XNAT OPEX Plugin with the addition of new fields in XML/XSD format.

See https://github.com/QBI-Software/OPEXUploader/wiki/Developer-Notes#excel-or-csv-spreadsheets

The OPEX Uploader stores the field names in a local database called `opexconfig.db` (Sqlite3) so it can generate the correct data format for upload to XNAT.

For adding a new datatype, the following steps are required:
1. Open the file called `opex.csv`
2. Add a new line at the end with the new datatype information:
    - Expt: the experiment datatype as reference (unique)
    - interval: indicates how often the data is collected eg, 6 for once every 6 months (used in the missing data report)
    - total: the total number of experiments expected per patient (used to detect missing data)
    - xsitype: corresponds to the XNAT namespace eg opex:acer
    - prefix: the prefix of the XSD eg AC used in the Sample ID
    - date_provided: whether a date is provided in the data (this is a mandatory field in XNAT) - used for the Visit module which updates the dates from the appointments spreadsheet
    - name: Name of the experiment shown in the dropdown display
    - option: argument provided to uploader.py (the backend script) 
3. Open or create a file called `<DATATYPE>_fields.csv`
    - Provide the NAME of the experiment in the first cell (header) matching the 'expt' field above
    - List the fields in a column as matching with the XNAT fields
    - It is possible to provide a mapped fieldname column if this is needed (ie the upload data uses different field names)
    - Where there are several subtypes, such as BLOOD and FMRI, it is useful to add the columns to the same file.
4. Open the file called `dbsetup.py`
    - In the function called `load_fields` around line 112, add the new datatype and the matching `*fields.csv` file
    ```
    csvfiles = {'BLOOD': 'blood_fields.csv',
                 ...
                 'NEW-DATATYPE' : 'new-datatype_fields.csv'
    }
    ```
5. Load the fields from the CSV to the database (`opexconfig.db`) 
    - Test run by changing the database to `opexconfig_test.db` on Line 9
    ```
    DBNAME = join(BASEDIR, 'resources', 'opexconfig.db')
   TO 
   DBNAME = join(BASEDIR, 'resources', 'opexconfig_test.db')
    ```
   - Run the `dbsetup.py` file with `python dbsetup.py`
   - At the prompt type 'u' for update
   - check the fields have been added correctly
   
 **If a new field is added to an existing datatype, just add it to the appropriate `*.csv` file and run `dbsetup.py` with 'update'**
 
 *Note, fields should not be deleted from XNAT as this can cause all sorts of compatibility problems - just ignore them*
 
 ## Setup for the first time
 If somehow, you are setting up the database for the first time, assuming the first 3 steps above have been carried out, just run `dbsetup.py` with the 'initialize' option ('i') which will overwrite existing fields and load everything from *.csv files.
 
 # Tests
 Some testing is available in `tests/test_dbquery.py` - follow the existing format for `test_getInfo_TASK()` and add a test for the new datatype here.