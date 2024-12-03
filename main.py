import argparse
from xlutils.copy import copy
import sys
import csv
import os
import mysql.connector
import ffmpeg
import subprocess
import xlrd
import xlwt
from datetime import datetime, timedelta
from openpyxl import load_workbook
from openpyxl.drawing.image import Image
from frameioclient import FrameioClient

''' Process baselight file '''
def process_baselight_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.readlines()

            cleaned_baselight_paths = []
            for i in content:
                curr_line = i.replace('\n', '')
                cleaned_baselight_paths.append(curr_line)

            # parse each baselight file line into different parts
            Baselight_file_paths = []
            Baselight_file_frames = []

            for i in cleaned_baselight_paths:
                curr_line = i.split()
                if curr_line:
                    # Extract the file path (curr_line[0]) and frames (curr_line[1:])
                    path = curr_line[0]
                    frames = curr_line[1:]

                    # Append to the respective lists
                    Baselight_file_paths.append(path)
                    Baselight_file_frames.append(frames)

            baselight_trimed_path_split = []

            for i in Baselight_file_paths:
                curr_line = i.split('/')
                baselight_trimed_path_split.append(curr_line)

            baselight_trimed_path = []

            for i in baselight_trimed_path_split:
                curr_line = i[2:6]
                join_string = '/'.join(curr_line)
                base_trim_path = '/' + join_string
                baselight_trimed_path.append(base_trim_path)

        Baselight_path_and_frames = list(
            zip(baselight_trimed_path, Baselight_file_frames))

        return Baselight_path_and_frames

     # if file not found, output error
    except FileNotFoundError:
        print(f"\nInput file {file_path} not found.\n")
    # if error occurs while reading output error
    except Exception as e:
        print(f"An error occurred while reading {file_path}: {e}\n")


def process_flame_file(file_path):

    try:
        with open(file_path, 'r') as f:
            content = f.readlines()

            flame_path = []
            flame_frames = []
            flame_path_and_frames = []
            for curr_line in content:
                trim = curr_line.split()
                trimed_path = '/' + trim[1]
                trimed_frames = trim[2:]

                flame_path.append(trimed_path)
                flame_frames.append(trimed_frames)
                flame_path_and_frames = list(zip(flame_path, flame_frames))

        return flame_path_and_frames
     # if file not found, output error
    except FileNotFoundError:
        print(f"\nInput file {file_path} not found.\n")
    # if error occurs while reading output error
    except Exception as e:
        print(f"An error occurred while reading {file_path}: {e}\n")


def process_xytech_file(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.readlines()
            # Parse and process the Xytech content here
            parse_xytech_a = content[2:5]

            header_string_a = []
            for line in parse_xytech_a:
                curr_line = line.replace('\n', '')
                header_string_a.append(curr_line)

            parse_xytech_b = content[-1]

            parse_xytech_b = parse_xytech_b.replace('\n', '')
            parse_xytech_b_n = 'Notes: ' + parse_xytech_b

            final_header = []
            for i in header_string_a:
                final_header.append(i)
            final_header.append(parse_xytech_b_n)

            colorist_names = parse_xytech_b[37:-1]
            cleaned_colorist_names = colorist_names.replace('and', '')

        return final_header, cleaned_colorist_names
    # if file not found, output error
    except FileNotFoundError:
        print(f"\nInput file {file_path} not found.\n")
    # if error occurs while reading output error
    except Exception as e:
        print(f"An error occurred while reading {file_path}: {e}\n")


def extract_xytech_file_paths(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    capture = False
    file_paths = []

    for line in lines:
        stripped_line = line.strip()
        if stripped_line == "Location:":
            capture = True
            continue
        elif capture and (not stripped_line or stripped_line == "Notes:"):
            break
        elif capture:
            file_paths.append(stripped_line)

        '''We can continue parsing xytech path for comparison with Baselight and Flame file destination. '''

        trimmed_xytech_file_pathsources = []
        xytech_storages = []

        for i in file_paths:
            trim_line = i.split('/')
            trim_path_line = trim_line[3:]
            xy_storage = trim_line[1]
            trimmed_xytech_file_pathsources.append(trim_path_line)
            xytech_storages.append(xy_storage)

        joined_trimmed_paths = [
            '/' + '/'.join(path) for path in trimmed_xytech_file_pathsources]

    return file_paths, joined_trimmed_paths, xytech_storages

# parse file name for database insert


def parse_file_name(file):

    # Extract filename without extension
    name_without_extension = os.path.splitext(file)[0]

    # Split the filename
    parts = name_without_extension.split('_')

    machine = parts[0]
    user = parts[1]
    date = parts[2]

    return machine, user, date


def parse_numbers_to_ranges(numbers):
    # base case if input list is empty
    if not numbers:
        return []
    # create lists
    ranges = []
    current_range = []
    # Loop through the numbers
    for num in numbers:
        # Skip over any "<null>" or "<err>" or empty strings
        if num in ("<null>", "<err>", ""):
            continue

        try:
            # Convert the frame to an integer
            num = int(num)
        except ValueError:
            # Handle the case if num is not a valid integer
            continue
            # check if the current_range list is empty
        if not current_range:
            current_range = [num]
            # check if num is = to the last num in current range + 1
            # if true then, append it to current range list
        elif num == current_range[-1] + 1:
            current_range.append(num)
            # else current num is not part of the current range
        else:
            # check if current_range list contains 1 or mor enumber for the remainder of the list
            if len(current_range) > 1:
                ranges.append(f"{current_range[0]}-{current_range[-1]}")
            else:
                # only one number is left so append that to the range list
                ranges.append(str(current_range[0]))
                # reset current_range to start of range list
            current_range = [num]
    # next check if there are any numbers left in the current_range list
    if current_range:
        # check if there are more numbers in the current_range list
        if len(current_range) > 1:
            ranges.append(f"{current_range[0]}-{current_range[-1]}")
        else:
            # append the last num to the end of the list
            ranges.append(str(current_range[0]))
    # return the list of ranges
    return ranges



# function to get video duration in time code format using ffprobe
def get_video_duration_timecode(video_file):
    try:
        # Run ffprobe and capture stdout
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", video_file],
            capture_output=True,
            text=True,
            check=True
        )

        # Extract duration from the captured output and convert to float
        duration_seconds = float(result.stdout.strip())

        # Convert the duration to time code format
        duration_timecode = str(timedelta(seconds=duration_seconds))
        return duration_timecode

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running ffprobe: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
# ============================================================================================================
# ============================================================================================================


def convert_frame_to_timecode(frame, fps=24):
    # Calculate total seconds
    total_seconds = frame // fps

    # Calculate hours, minutes, and seconds
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Calculate remaining frames
    remaining_frames = frame % fps

    # Convert remaining frames to milliseconds
    milliseconds = int((remaining_frames / fps) * 1000)

    # Format timecode: HH:MM:SS:FF
    timecode = f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"
    return timecode

# Function to convert a frame range to time code format


def convert_frame_range_to_timecode(frame_range, fps=24):
    frame_parts = frame_range.split('-')

    # if single frame, start and end frame are the same
    if len(frame_parts) == 1:
        start_frame = int(frame_parts[0])
        # end_frame = start_frame
        start_timecode = convert_frame_to_timecode(start_frame, fps)
        return start_timecode

    elif len(frame_parts) == 2:
        start_frame = int(frame_parts[0])
        end_frame = int(frame_parts[1])
    else:
        raise ValueError("Invalid frame range format")

    start_timecode = convert_frame_to_timecode(start_frame, fps)
    end_timecode = convert_frame_to_timecode(end_frame, fps)

    return f"{start_timecode}-{end_timecode}"


# ============================================================================================================
# ============================================================================================================
def video_length_timecode_to_frame(timecode, fps=24):
    # Parse the timecode (HH:MM:SS.FFFFFF format)
    time_parts = timecode.split(':')

    # Extract seconds and microseconds from the last part
    seconds_part = time_parts[-1].split('.')
    seconds = int(seconds_part[0])
    microseconds = int(seconds_part[1])

    # Calculate the total number of frames
    total_frames = (int(time_parts[0]) * 3600 + int(time_parts[1])
                    * 60 + seconds) * fps + int(round(microseconds / 1e6 * fps))
    return total_frames



def is_in_range(frame_or_frame_range, video_length_frame):
    if '-' in frame_or_frame_range:
        # Frame range is provided, check if both start and end frames are within the video length
        start_frame, end_frame = map(int, frame_or_frame_range.split('-'))
        return start_frame <= video_length_frame and end_frame <= video_length_frame
    else:
        # Single frame is provided, check if it's within the video length
        frame = int(frame_or_frame_range)
        return frame <= video_length_frame




def get_thumbnail_2(frame_range, video_file, folder_path, fps=24):
    
    frame_parts = frame_range.split('-')

    # Determine the frame or frame range to use for the thumbnail
    if len(frame_parts) == 1:  # Single frame
        frame = int(frame_parts[0])
        timecode = convert_frame_to_timecode(frame, fps)
        frame_identifier = f"{frame:06d}"  # Zero-padded frame number
    elif len(frame_parts) == 2:  # Frame range
        start_frame = int(frame_parts[0])
        end_frame = int(frame_parts[1])
        middle_frame = (start_frame + end_frame) // 2
        timecode = convert_frame_to_timecode(middle_frame, fps)
        frame_identifier = f"{start_frame:06d}-{end_frame:06d}"
    else:
        raise ValueError("Invalid frame range format")

    # Modify the filename to include frame identifier and formatted timecode
    formatted_timecode_for_filename = timecode.replace(':', '').replace('.', '')
    thumbnail_file = f"thumb_{frame_identifier}_{formatted_timecode_for_filename}.bmp"

    # Full path for the thumbnail file
    thumbnail_full_path = os.path.join(folder_path, thumbnail_file)

    # Check if the thumbnail already exists
    if os.path.exists(thumbnail_full_path):
        return thumbnail_full_path

    # Command to generate the thumbnail using ffmpeg
    ffmpeg_command = [
        'ffmpeg',
        '-ss', timecode,
        '-i', video_file,
        '-vframes', '1',
        '-vf', 'scale=96:74',  # Adjust scale if needed
        thumbnail_full_path  # Save the thumbnail at the specified path
    ]

    # Execute the command and handle exceptions
    try:
        subprocess.run(ffmpeg_command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during thumbnail creation: {e}")
        return None

    return thumbnail_full_path

def main():
    parser = argparse.ArgumentParser(
        description="Process Baselight and Flame files along with Xytech file.")
    parser.add_argument("--files", dest="workFiles",
                        nargs='+', help="List of files to process")
    parser.add_argument("--xytech", dest="xytechFile",
                        help="Xytech file input")
    parser.add_argument("--verbose", action="store_true",
                        help="show verbose output")
    parser.add_argument("--process", dest="video_file",
                        help="Video file to process")
    parser.add_argument(
        "--output", choices=['DB', 'CSV', 'DBQ', 'XLS'], help="Output to CSV, Database, Print DB Query or XLS")

    args = parser.parse_args()

    if args.workFiles is not None:

        # pase Xytech file, preparing to update new paths, based on pattern matching
        xytech_data = None
        if args.xytechFile:
            xytech_data, colorist_names = process_xytech_file(args.xytechFile)
            xytech_paths, trimmed_xytech_file_pathsources, xytech_storages = extract_xytech_file_paths(
                args.xytechFile)
        else:
            print("No Xytech file provided!")
            # sys.exit(2)

        # create tuple for xyztech files
        Xytech_full_and_trim_path = list(
            zip(xytech_paths, trimmed_xytech_file_pathsources, xytech_storages))

        if args.verbose:
            print(
                "----------------------------------------------------------------------------")
            print(
                f"Processing Xytech file: {args.xytechFile}\n\nXytech header: {xytech_data}\nXytech Colorist names: {colorist_names}\n")
            print('Xytech filepaths: ')
            for i in xytech_paths:
                print(i)
            print()

            print('Trimmed Xytech filepaths:')
            for i in trimmed_xytech_file_pathsources:
                print(i)
            print()

            print('\nFull and Trimmed Xytech filepaths: ')
            for i in Xytech_full_and_trim_path:
                print(i)

        # here we store the parsed files in different sections, setting it up so that we can insert into csv file or database.
        Baselight_CSV_part = []
        Flame_CSV_part = []
        for file in args.workFiles:
            if args.verbose:
                print(
                    "----------------------------------------------------------------------------")
                print(f"Processing file: {file}\n")

            if "Baselight" in file:
                file_details = []
                Baselight_path_and_frames = process_baselight_file(file)
                machine, user, date = parse_file_name(file)
                file_details.append((machine, user, date))

                for base_path, base_frames in Baselight_path_and_frames:
                    for xy_full_path, xy_trim_path, xytech_storages in Xytech_full_and_trim_path:
                        if base_path == xy_trim_path:
                            # parse the location
                            Baselight_CSV_part.append(
                                (xy_full_path, base_frames, machine, user, date))
                            # Final_CSV_export.append((xy_full_path, parse_numbers_to_ranges(base_frames)))

                if args.verbose:
                    print("Machine:", machine)
                    print("User:", user)
                    print("Date:", date)
                    print()
                    print(f"Baselight_path_and_frames:\n")
                    for i in Baselight_path_and_frames:
                        print(i)
                    # print parsed Baselight of the file we are parsing

            elif "Flame" in file:
                flame_path_and_frames = process_flame_file(file)
                machine, user, date = parse_file_name(file)
                file_details.append((machine, user, date))

                for flame_path, flame_frames in flame_path_and_frames:
                    for xy_full_path, xy_trim_path, xytech_storages in Xytech_full_and_trim_path:
                        if flame_path == xy_trim_path:
                            Flame_CSV_part.append(
                                (xy_full_path, flame_frames, machine, user, date))

                if args.verbose:
                    print("\nMachine:", machine)
                    print("User:", user)
                    print("Date:", date)
                    print('\nflame_path_and_frames:\n')
                    for i in flame_path_and_frames:
                        print(i)

        db_csv_details = []

        for path, frames, machine, user, date in Baselight_CSV_part:
            curr_path = path.split('/')
            xy_location = curr_path[1]
            db_csv_details.append((path, parse_numbers_to_ranges(
                frames), xy_location, machine, user, date))

        for path, frames, machine, user, date in Flame_CSV_part:

            curr_path = path.split('/')
            xy_location = curr_path[1]
            db_csv_details.append((path, parse_numbers_to_ranges(
                frames), xy_location, machine, user, date))

        csv_export = []

        for path, frames, xy_storage, machine, user, date in db_csv_details:
            for i in frames:
                csv_export.append((path, i))

        if args.verbose:
            print(
                "\n----------------------------------------------------------------------------")
            print('FINAL CSV EXPORT:\n')
            for i in csv_export:
                print(i)

        if args.output == "DB":

            # Establish the connection
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root",
                database="COMP467_Proj2"
            )

            # Check if the connection is established
            if connection.is_connected():
                print("Connected to MySQL database")

            # SQL statements to create the tables
            database = connection.cursor()

            # Table 1
            table1_sql = """
            CREATE TABLE IF NOT EXISTS user_submission (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_script_runner VARCHAR(255) NOT NULL,
                machine VARCHAR(255) NOT NULL,
                user_on_file VARCHAR(255) NOT NULL,
                file_date DATE NOT NULL,
                submitted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """

            # Table 2
            table2_sql = """
            CREATE TABLE IF NOT EXISTS file_details (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_on_file VARCHAR(255) NOT NULL,
                file_date DATE NOT NULL,
                location VARCHAR(512) NOT NULL,
                frame_ranges VARCHAR(255) NOT NULL
            );
            """

            # Creating tables if they do not exist
            database.execute(table1_sql)
            database.execute(table2_sql)

            # Insert data into the database
            # table 1
            current_user = os.environ.get('USER') or os.environ.get('USERNAME')
            current_date = datetime.now().date()

            # setting up for DB export
            db_path_frames = []
            for path, frames, xy_storage, machine, user, date in db_csv_details:
                for i in frames:
                    db_path_frames.append((user, date, path, i))

            # print('Getting rid of dups:\n')
            # for i in file_details:
            #     print(i)
            print('\nDB user_submission table export\n')
            for i in file_details:
                print(i)

            print("\nDB file details table export\n")
            for i in db_path_frames:
                print(i)

            # temp = 'temp'
            for machine, user, date in file_details:
                database.execute("INSERT INTO user_submission (user_script_runner, machine, user_on_file, file_date, submitted_date) VALUES (%s, %s, %s, %s, %s)",
                                 (current_user, machine, user, date, current_date))

            for user, date, path, frames in db_path_frames:
                database.execute("INSERT INTO file_details (user_on_file, file_date, location, frame_ranges) VALUES (%s, %s, %s, %s)",
                                 (user, date, path, frames))

            connection.commit()

            # Close the connection
            database.close()
            connection.close()
            pass
        elif args.output == "CSV":
            # Output parsed data to a CSV file
            '''
            Parsed Data set up for CSV processing
            '''
            export_file = "project2_20230327_output.csv"

            with open(export_file, mode='w', newline='') as file:
                writer = csv.writer(file)

                # Write headers to the CSV file
                writer.writerow(xytech_data)
                # Skip line 2 and 3
                writer.writerow("")
                writer.writerow("")

                for i in csv_export:
                    writer.writerow(i)
            pass

        elif args.output == "DBQ":

            try:
                # Establish the connection
                connection = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    password="root",
                    database="COMP467_Proj2"
                )

                # Check if the connection is established
                if connection.is_connected():
                    print("Connected to MySQL database")

                    # Create a cursor object using the cursor() method
                    database = connection.cursor()

                    # List of queries to run
                    queries = {
                        "Query 1: List all work done by user BBONDS": '''SELECT * 
                                                                        FROM file_details 
                                                                        WHERE user_on_file = "BBONDS" ''',
                        "Query 2: All work done after 3-25-2023 date on a Flame": '''SELECT 
                                                                                    us.id AS submission_id, 
                                                                                    us.user_script_runner, 
                                                                                    us.machine, 
                                                                                    us.user_on_file, 
                                                                                    us.file_date, 
                                                                                    us.submitted_date, 
                                                                                    fd.location, 
                                                                                    fd.frame_ranges
                                                                                FROM 
                                                                                    user_submission AS us
                                                                                JOIN 
                                                                                    file_details AS fd ON us.user_on_file = fd.user_on_file AND us.file_date = fd.file_date
                                                                                WHERE 
                                                                                    us.machine = 'Flame'
                                                                                AND 
                                                                                    us.submitted_date > '2023-03-25'
                                                                                AND 
                                                                                    fd.file_date > '2023-03-25';''',
                        "Query 3: What work done on ddnsata7 on date 3-23-2023": '''SELECT 
                                                                                        us.id AS submission_id, 
                                                                                        us.user_script_runner, 
                                                                                        us.machine, 
                                                                                        us.user_on_file, 
                                                                                        us.file_date, 
                                                                                        us.submitted_date, 
                                                                                        fd.location, 
                                                                                        fd.frame_ranges
                                                                                    FROM 
                                                                                        user_submission AS us
                                                                                    JOIN 
                                                                                        file_details AS fd ON us.user_on_file = fd.user_on_file AND us.file_date = fd.file_date
                                                                                    WHERE 
                                                                                        fd.location LIKE '/ddnsata7%'
                                                                                    AND 
                                                                                        us.file_date = '2023-03-23';''',
                        "Query 4: Name of all Autodesk Flame users": '''SELECT DISTINCT
                                                                                        user_on_file
                                                                                    FROM 
                                                                                        user_submission
                                                                                    WHERE 
                                                                                        machine = 'Flame';
                                                                                        ''',
                        "Query 5: Name User(s) and Date(s) where they worked on hpsans15": '''SELECT user_on_file, file_date
                                                                                   FROM file_details
                                                                                   WHERE location LIKE 'hpsans15';'''
                        # "Query 5: ..." : ''' your query here '''
                    }

                    for query_name, query in queries.items():
                        print(query_name)
                        database.execute(query)
                        rows = database.fetchall()
                        for row in rows:
                            print(row)
                        print("\n")  # Print a newline for better readability

            except mysql.connector.Error as e:
                print(f"Error: {e}")

            finally:
                # Close the cursor and connection if open
                if connection.is_connected():
                    database.close()
                    connection.close()
                    print("MySQL connection is closed")

    # process video file
    if args.video_file is None:
        print("No video file selected")
        sys.exit(2)
    else:
        duration_timecode = get_video_duration_timecode(args.video_file)

        if duration_timecode is not None:
            print(f"Video duration: {duration_timecode}\n")

        # # Convert a single frame to timecode
        # print("Frame 15: ", convert_frame_range_to_timecode("15"))
        # print("Frame 40: ", convert_frame_range_to_timecode("40"))
        # print("Frame 24: ", convert_frame_range_to_timecode("24"))
        # print("Frame 24: ", convert_frame_range_to_timecode("24"))

        # # Convert other frame ranges to timecode
        # print("Frame 15-40: ", convert_frame_range_to_timecode("15-40"))

        video_frame_num = video_length_timecode_to_frame(
            duration_timecode)  # Replace with your desired timecode
        print("\nVideo Frame Num: ", video_frame_num)

        try:
            # Establish the connection
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="root",
                database="COMP467_Proj2"
            )

            # Check if the connection is established
            if connection.is_connected():
                print("Connected to MySQL database")

                # Create a cursor object using the cursor() method
                database = connection.cursor()

                # Build the SQL query dynamically
                query = "SELECT location, frame_ranges FROM file_details"

                print(f"Executing query: Frames in range")
                database.execute(query)
                rows = database.fetchall()

                frames_in_range = []
                for row in rows:
                    # frame_ranges is in the fourth column (index 4)
                    frame_ranges = row[1]
                    video_length_frame = video_frame_num  # video length

                    if is_in_range(frame_ranges, video_length_frame) == True:
                        # print(row)  # Print the row if is_in_range is True
                        frames_in_range.append(row)

                    try:
                        pass
                    except mysql.connector.Error as e:
                        print(f"Error: {e}")

        finally:
            # Close the cursor and connection if open
            if connection.is_connected():
                database.close()
                connection.close()
                print("MySQL connection is closed")

    if args.output == "XLS":
        # Define the path for the thumbnails folder
        thumbnails_folder = "thumbnails_folder"
        os.makedirs(thumbnails_folder, exist_ok=True)  # Create the folder if it doesn't exist

        export_file = "COMP467_project3_xls_output.xls"

        # Create a new workbook
        workbook = xlwt.Workbook()

        # Add a sheet to the workbook
        sheet = workbook.add_sheet('Sheet1')

        image_column_index = 3  # For example, if you want to insert images in the 6th column

        for row_index, row_data in enumerate(frames_in_range):
            # Assuming frame_ranges is the 5th element in row_data
            frame_ranges = row_data[1]
            timecode = convert_frame_range_to_timecode(frame_ranges)

            # Add existing data and timecode to the sheet
            new_row_data = list(row_data) + [timecode]
            for col_index, cell_value in enumerate(new_row_data):
                sheet.write(row_index, col_index, cell_value)
            
            thumbnail_path = get_thumbnail_2(frame_ranges, args.video_file,thumbnails_folder)

            # Insert the BMP image into the specified column
            if thumbnail_path and os.path.exists(thumbnail_path):
                sheet.insert_bitmap(
                    thumbnail_path, row_index, image_column_index)

        # Save the workbook to an Excel file
        workbook.save(export_file)

        # For own use make sure you change the token generated in Frameio
        TOKEN = 'fio-u-vQBjA1fBTMQ2Av4Te1W4J_2smh2TghAOHmA8BMOrFrepuZwhwIsTu4hJwsRCWESd'
        client = FrameioClient(TOKEN) 
        project_id = '2c9a70a0-2b6b-4edf-87b3-a1f4dd342975' # this is the original one 
        


        folder_id = client.projects.get(project_id)['root_asset_id']

        # Directory containing your thumbnails
        thumbnail_folder = 'thumbnails_folder'

        # List all files in the directory
        all_files = os.listdir(thumbnail_folder)

        # Filter for thumbnail files (modify this according to your file naming or extension)
        thumbnails = [file for file in all_files if file.endswith('.bmp')]

        # Upload each thumbnail
        for thumbnail in thumbnails:
            file_path = os.path.join(thumbnail_folder, thumbnail)
            client.assets.upload(folder_id, file_path)
            print(f'Uploaded {thumbnail}')



# run the script
if __name__ == "__main__":
    main()

