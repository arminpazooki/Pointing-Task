import csv
import math
import os
from config import PTColor
from config import contrast_factor
from config import video_filename

def interpolate_avg_distances(csv_file_path, PTColor, contrast_factor):
    # Read CSV file
    data = []
    with open(csv_file_path, 'r', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)  # Read header
        for row in csvreader:
            data.append(row)

    # Interpolate avg_distance, new_avg_x, and new_avg_y simultaneously
    prev_non_empty_row = None
    start_index = None
    for i, row in enumerate(data):
        avg_distance = row[12]  # Index 12 is for avg_distance column
        new_avg_x = row[10]  # Index 10 is for new_avg_x column
        new_avg_y = row[11]  # Index 11 is for new_avg_y column
        if avg_distance == '' and new_avg_x == '' and new_avg_y == '':
            if start_index is None:
                start_index = i
        else:
            if start_index is not None:
                end_index = i
                prev_avg_distance = float(prev_non_empty_row[12])
                prev_new_avg_x = float(prev_non_empty_row[10])
                prev_new_avg_y = float(prev_non_empty_row[11])
                next_avg_distance = float(row[12])
                next_new_avg_x = float(row[10])
                next_new_avg_y = float(row[11])
                num_empty_rows = end_index - start_index
                interpolation_step_distance = (next_avg_distance - prev_avg_distance) / (num_empty_rows + 1)
                interpolation_step_new_avg_x = (next_new_avg_x - prev_new_avg_x) / (num_empty_rows + 1)
                interpolation_step_new_avg_y = (next_new_avg_y - prev_new_avg_y) / (num_empty_rows + 1)
                for j in range(start_index, end_index):
                    interpolated_distance = prev_avg_distance + (interpolation_step_distance * (j - start_index + 1))
                    interpolated_new_avg_x = prev_new_avg_x + (interpolation_step_new_avg_x * (j - start_index + 1))
                    interpolated_new_avg_y = prev_new_avg_y + (interpolation_step_new_avg_y * (j - start_index + 1))
                    data[j][12] = str(interpolated_distance)
                    data[j][10] = str(interpolated_new_avg_x)
                    data[j][11] = str(interpolated_new_avg_y)
                start_index = None
        if avg_distance != '' and new_avg_x != '' and new_avg_y != '':
            prev_non_empty_row = row

    # Calculate total path and add it as a new column
    total_distance = 0
    prev_avg_distance = None  # Initialize prev_avg_distance for total_path calculation
    for row in data:
        timestamp = float(row[0])
        avg_distance = float(row[12]) if row[12] != '' else 0
        if prev_avg_distance is not None:
            total_distance += abs(avg_distance - prev_avg_distance)
        prev_avg_distance = avg_distance
        row.append(total_distance)

    # Calculate angle_degrees for rows where it's blank
    for row in data:
        if row[13] == '':  # Index 13 is for angle_degrees column
            new_avg_x = float(row[10]) if row[10] != '' else 0
            new_avg_y = float(row[11]) if row[11] != '' else 0
            if new_avg_x != 0 or new_avg_y != 0:  # Avoid division by zero
                angle_degrees = math.degrees(math.atan2(new_avg_y, new_avg_x))
                row[13] = str(angle_degrees)

    # Add PTColor and contrast_factor to the end of the CSV file
    for row in data:
        row.extend([str(row[-1]), str(PTColor), str(contrast_factor)])

    # Save the updated data to CSV file
    with open(csv_file_path, 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile)
        headers.extend(['total_path', 'PTColor', 'contrast_factor'])  # Add total_path, PTColor, and contrast_factor headers
        csvwriter.writerow(headers)  # Write headers
        csvwriter.writerows(data)

folder_name = 'bounding_box_data'
video_filename = video_filename
video_name = os.path.splitext(os.path.basename(video_filename))[0]
csv_file_path = os.path.join(folder_name, f'{video_name}_bbox_coordinates.csv')
PTColor = PTColor  # Example PTColor from main.py
contrast_factor = contrast_factor  # Example contrast_factor from util.py
interpolate_avg_distances(csv_file_path, PTColor, contrast_factor)
