# Video Processing and Data Export

## Overview
This project processes video files, extracts metadata and thumbnails, and exports data to various formats such as CSV, XLS, and Frame.io uploads. It incudes functionality for argparse commands, timecode generation, thumbnail extraction, and more.

---

## Features
1. **Download VP Video**
   - You can utilize the video provided

2. **Run Script with Arguments**
   - Use the `--process` argument to specify the video file.
   - Example:
     ```bash
     python3 main.py --process twitch_nft_demo.mp4 --output XLS
     ```

3. **Populate Database**
   - Matches video frames with database entries based on the video length.

4. **Timecode Extraction**
   - Extracts timecode using FFmpeg or a custom timecode conversion method.
   - Converts frame ranges to timecode.

5. **XLS Export**
   - Includes a new `--output XLS` flag for exporting data to an Excel file.
   - Additional columns include timecode ranges and thumbnails.

6. **Thumbnail Generation**
   - Creates 96x74 thumbnails from the middle-most frame of each range.
   - Adds thumbnails to the XLS file alongside their corresponding ranges.

7. **Frame.io Integration**
   - Uploads processed thumbnails as assets to Frame.io using their API.

---

## Installation

### Prerequisites
Ensure the following dependencies are installed:
- Python 3.x
- FFmpeg
- MySQL Connector
- OpenPyXL
- xlwt
- xlrd
- Frame.io Python SDK

### Install Python Libraries or use requiremnts.txt file to install lib dependencies 
```bash
pip install mysql-connector-python openpyxl xlwt xlrd frameioclient
```

### Set Up FFmpeg
Download and install FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html). Ensure FFmpeg is added to your system's PATH.

---

## Usage

### Script Arguments
- `--files`: List of Baselight/Flame files to process.
- `--xytech`: Xytech file input.
- `--process`: Specify the video file to process.
- `--output`: Choose between `DB`, `CSV`, `DBQ`, or `XLS`.
- `--verbose`: Enable detailed output.

### Example Command
```bash
python3 cmain.py --process twitch_nft_demo.mp4 --output XLS
```

---

## Deliverables
1. **Code**
   - Fully functional script with all required features implemented.
2. **Excel File**
   - Includes:
     - Timecode ranges.
     - Corresponding thumbnails.
3. **Frame.io Upload**
   - Screenshots of uploaded thumbnails on Frame.io.

---

## Development Notes
- **Timecode Conversion**
  - Frames are converted to timecode format using a custom function.
- **Thumbnail Generation**
  - Uses FFmpeg to extract middle frames from video ranges.
- **Frame.io API**
  - Assets uploaded programmatically to Frame.io using a valid API token.

---

## Example Outputs
### XLS File Format
| Path              | Frame Ranges | Timecode Ranges       | Thumbnail        |
|-------------------|--------------|-----------------------|------------------|
| /path/to/location | 15-40        | 00:00:00.625-00:00:01.667 | [Thumbnail.bmp] |

### Frame.io Integration
- Thumbnails uploaded to the specified project folder in Frame.io.

---

## Troubleshooting
1. **File Not Found**
   - Ensure all required files (Baselight, Flame, Xytech, video) are in the correct directory.

2. **FFmpeg Issues**
   - Verify FFmpeg is installed and accessible from the system PATH.

3. **Database Errors**
   - Confirm MySQL credentials and database setup.

4. **Frame.io API**
   - Ensure the API token is valid and the project ID is correct.

