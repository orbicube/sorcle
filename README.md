# sorcle
pyglet program to draw a spinning wheel, grabbing a list of names from a public Google Sheet file. Primarily designed for usage as an OBS source.

<img width="500" alt="image" src="https://github.com/user-attachments/assets/f6245651-c24d-49a8-9766-cc480d2c0349" />

## Installation
* Create a new [Google service account](https://console.cloud.google.com/apis/credentials) with Google Sheets and Google Drive API enabled in the organisation.
* Inside the service account's page, click on the `Keys` tab and then `Add key` -> `Create new key`, selecting JSON.
* Rename the automatically downloaded JSON file to account.json and put it in the same folder as the .py/.exe file.
* Find the `client_email` string in account.json, and share the spreadsheet you wish to use with that email. Make sure to give it editor permissions.
### Python (3.11+)
```
  python -m pip install -r requirements.txt
```
### Windows
Run the standalone .exe from [Releases](https://github.com/orbicube/sorcle/releases/latest).
## Usage
* To spin the wheel, create a file called "spin" in the directory.
* To re-import your list, create a file called "import" in the directory.
* After the wheel has finish spinning, you can create a file called "move" to move the winner to another sheet. Any text inside "move" will be added as an additional column.
* For Windows users there are .bat files to trigger these with a Stream Deck or similar application.

## Configuration
settings.toml is configurable, and you can swap out the sound and graphic files as needed. Changed settings will not be reflected on an import, you must restart the program for them to be reflected.
### Reference
```
[spreadsheet]
api_key: String # Create one at https://console.cloud.google.com/apis/api/sheets.googleapis.com/
id: String # found between /d/ and /edit in url of a Google Sheets spreadsheet
sheet: String # Sheet name, Sheet1 if you haven't renamed one
first_column: String # Leftmost column, in letter notation
last_column: String # Rightmost column, in letter notation
row: Integer # Row number to start from, indexing from 1
primary_column: String # Column to scan, in letter noation
sub_column: String # Optional secondary column to display under winner and written to sub.txt
extra_columns: Array # Optional extra columns written to files extra1.txt, extra2.txt, etc.
separator: String # Separator to use when writing multiple entries to files

[move]
enabled: Boolean # If true, will move columns into another sheet when "move" file is detected
sheet: String # Sheet name, different from
column: String # Leftmost column for data on the sheet we're moving to
row: Integer # Topmost row for data on the sheet we're moving to
prepend_date: Boolean # Will add a date in the first column
date_format: String # How to format the date in strftime format https://strftime.org/ e.g. "%Y-%m-%d"

[wheel]
font: String # Font installed in the system
colors: Array # Array of arrays containing RGB values to use for wedges; font color will change to match
remove_dupes: Boolean # Remove duplicate entries from the results; if false then entries will be combined
combine_dupes Boolean # If above is false, then this option will combine dupe wedges into a single, bigger wedge 
suppress_win: Boolean # Suppress winner notification if handling visuals elsewhere
decel_rate: Float # How fast the wheel decelerates; bigger number is faster (1.0 = -1% of current speed per tick)

[pointer] # Image that points to the result of the wheel
file: String # Can be animated GIF or any other arbitrary image type
scale: Float # 1.0 = 100%
x_pos: Integer # Position on screen, adjustable for different images
y_pos: Integer 

[center] # Image placed in the center of the wheel
file: String # Can be animated GIF or any other arbitrary image type
scale: Float # 1.0 = 100%
rotate: Boolean # Rotate with the wheel

[tick] # Sound played when pointer 'hits' wedge
file: String # WAV only I think
volume: Float # 1.0 = 100%

[finished] # Sound played when wheel finishes spinning
file: String # WAV only I think
volume: Float # 1.0 = 100%

[window]
nearest_neighbour: Boolean # Whether to use nearest neighbour scaling for pixel art sprites
```

