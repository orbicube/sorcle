# sorcle
pyglet program to draw a spinning wheel, grabbing a list of names from a public Google Sheet file. Primarily designed for usage as an OBS source.

<img width="500" alt="image" src="https://github.com/user-attachments/assets/f6245651-c24d-49a8-9766-cc480d2c0349" />

## Installation
Add a [Google API key with Google Sheets enabled](https://console.cloud.google.com/apis/api/sheets.googleapis.com/) to `settings.toml`.
### Python (3.11+)
```
  python -m pip install -r requirements.txt
  python sorcle.py
```
### Windows
Run the standalone .exe from [Releases](https://github.com/orbicube/sorcle/releases/latest).
## Usage
* To spin the wheel, create a file called "spin" in the directory.
* To re-import your list, create a file called "import" in the directory.
* For Windows users there is a .bat file to trigger this with a Stream Deck or similar application.
* Currently text is partially transparent and has an aliased look.  To somewhat alleviate this in OBS, use the provided `backboard.png` (or the -992 variant for a little border) as a source behind the program.

## Configuration
settings.toml is configurable, and you can swap out the sound and graphic files as needed. Changed settings will not be reflected on an import, you must restart the program for them to be reflected.
### Reference
```
[spreadsheet]
api_key: String # Create one at https://console.cloud.google.com/apis/api/sheets.googleapis.com/
id: String # found between /d/ and /edit in url of a Google Sheets spreadsheet
sheet: String # Sheet name, Sheet1 if you haven't renamed one
row: Integer # Row number to start from, indexing from 1
column: # Column to scan, in letter noation

[wheel]
font: String # Font installed in the system
colors: Array # Array of arrays containing RGB values to use for wedges; font color will change to match
remove_dupes: Boolean # Remove duplicate entries from the results; if false then entries will be combined
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

