Just a personal media converter tool/project that handles conversion and file merging, powered by FFmpeg.
If you somehow managed to find this and want to try using it, run 
python Converter.py

or build it into an executable with (requires pyinstaller):
- pip install pyinstaller
- pyinstaller --onefile Converter.py

or without console window:
- pyinstaller --onefile --windowed Converter.py

or with custom output name:
- pyinstaller --onefile --name AppName Converter.py
