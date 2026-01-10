# Sorcle
pyglet program to draw a spinning wheel, grabbing a list of names from a public Google Sheet file. Primarily designed for usage as an OBS Game Source.
## Installation
### Python (3.11+)
```
  python -m pip install -r requirements.txt
  python wheel.py
```
### Windows
Run the standalone .exe from [Releases](https://github.com/orbicube/sorcle/releases/latest).
## Usage
* To spin the wheel, create a file called "spin" in the directory.
* To re-import your list, create a file called "import" in the directory.
* For Windows users there is a .bat file to trigger this with a Stream Deck or similar application.
* Currently text is partially transparent and has an aliased look.
* To somewhat alleviate this in OBS, use the provided `backboard.png` (or the -992 variant for a little border) as a source behind the program.

## Configuration
settings.toml is configurable, and you can swap out the sound and graphic files as needed. Sound files are statically referenced so must match their filename. 
```
[spreadsheet]
id: String # found between /d/ and /edit in url of a Google Sheets spreadsheet
gid: String # identifies the current sheet in the document URL, often 0 for single sheet documents
row: Integer # Row number to start from, indexing from 1
title_column: Integer # Column to scan, indexing from 1 e.g. C = 3

[wheel]
font: String # Font installed in the system
colors: Array # Array of arrays containing RGB values to use for wedges; font color will change to match
remove_dupes: Boolean # Remove duplicate entries from the results; if false then entries will be combined
suppress_win: Boolean # Suppress winner notification if handling visuals elsewhere

[pointer] # Image that points to the result of the wheel
file: String # Can be animated GIF or any other arbitrary image type
scale: Float
x_pos: Integer # Position on screen, adjustable for different images
y_pos: Integer

[center] # Image placed in the center of the wheel
file: String # Can be animated GIF or any other arbitrary image type
scale: Float 
rotate: Boolean # Rotate with the wheel

[window]
nearest_neighbour: Boolean # Whether to use nearest neighbour scaling for pixel art sprites
```
Changed settings will not be reflected on an import, you must restart the program for them to be reflected.
