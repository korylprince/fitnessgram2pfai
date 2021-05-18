# About

fitnessgram2pfai.py is a Python 3 script to convert data from [The Cooper Institute's Fitnessgram](https://fitnessgram.net/) to the format required by [Texas's Physical Fitness Assessment Initiative](https://tea.texas.gov/texas-schools/health-safety-discipline/physical-fitness-assessment-initiative). The script can also optionally merge data from another CSV and validate the data against the [specification](https://tea.texas.gov/sites/default/files/pfai-help-template-pdf.pdf).

# Installation

* If you don't have it already, download and install [Python 3](https://www.python.org/downloads/). Make sure to select the option in the installer that adds python to your PATH.
* Create a folder on your Desktop named `pfai`.
* [Download fitnessgram2pfai.py](https://raw.githubusercontent.com/korylprince/fitnessgram2pfai/master/fitnessgram2pfai.py) to this folder.
* Using either Terminal (macOS/Linux) or cmd/PowerShell, `cd` to the location of the script
  * e.g. `cd c:\users\<youruser>\Desktop\pfai` (Windows) or `cd /Users/<youruser>/Desktop/pfai` (macOS)




# Fitnessgram Data

Before exporting data from Fitnessgram, make sure that the "Local Identifier" for each campus (Settings -> Districts & Schools) is set to its 9-digit ID.

Next, make sure the "Process Scores" button for all of your Fitnessgram events has been clicked.

Finally, to get the input file for this script sign into Fitnessgram, and go to Menu -> Reports -> Data Export -> Fitnessgram Data Export and click "View Report". Make sure all of your data is selected, "DEIDENTIFY" is set to "No De-identification", and "REPORT OUTPUT" is set to "CSV". Click "Run Report" to download the CSV. It will be easiest if you place the downloaded file in the same directory as the `fitnessgram2pfai.py` script.

Note: this CSV is output in an odd, UTF-16 format. The script accounts for this, so don't try to edit the data in this spreadsheet. If you need to edit any data, edit it in Fitnessgram itself, or use a merge CSV.

# Merging Data

You can overwrite any of the fields per student in output file by using the optional `-merge` argument. This is useful if Fitnessgram doesn't have some information like race/ethnicity. The merge.csv file should have a `Student ID` column, followed by any other columns listed in the [specification](https://tea.texas.gov/sites/default/files/pfai-help-template-pdf.pdf). The Student ID should match whatever was loaded into Fitnessgram. This is likely the student's TSDS number.  It will be easiest if you place the merge.csv file in the same directory as the `fitnessgram2pfai.py` script.

## Example

Example merge.csv:


| Student ID | IsHispanicLatino | IsAmericanIndianAlaskaNative | IsAsian | IsBlackAfricanAmerican | IsNativeHawaiianOtherPacificIslander | IsWhite |
|-|-|-|-|-|-|-|
| 1234567890 | 0 | 0 | 0 | 0 | 1 | 0 |
| 9876543210 | 1 | 0 | 0 | 0 | 0 | 1 |
|...|...|...|...|...|...|...|

# Usage

```
usage: fitnessgram2pfai.py [-h] -in INPUT [-merge MERGE] [-warn] -out OUT

Convert Fitnessgram Export to PFAI Format

optional arguments:
  -h, --help    show this help message and exit
  -in INPUT     Input "Fitnessgram Data Export" file path
  -merge MERGE  Path to merge.csv
  -warn         Log any validation issues to stdout
  -out OUT      Output PFAI.csv file path
```

## Example

`python[.exe] fitnessgram2pfai.py -in "FitnessGram Data Export.csv" -merge "merge.csv" -warn -out "pfai.csv"`
