import cv2
import math
import csv
import os
import time
from config import PTColor
from config import video_filename
from util import get_limits

# Define pixel-to-centimeter conversion values for each range
conversion_ranges = [
    (0, 58.5, 46.8),
    (58.5, 116.25, 44.4),
    (116.25, 173.25, 45.6),
    (173.25, 229, 44.6),
    (229, 287, 44.6),
    (287, 341, 43.2),
    (341, 392, 40.8),
    (392, 438.75, 40.8),
    (438.75, float('inf'), 36)
]


def get_conversion_factor(radius):
    for start, end, conversion in conversion_ranges:
        if start <= radius < end:
            return conversion
    return conversion_ranges[-1][2]  # Default to the last conversion value

video_filename = video_filename
video_name = os.path.splitext(os.path.basename(video_filename))[0]

PTColor = PTColor
initial_PTColor = PTColor.copy()  # Store initial color for manual adjustment
ignore_color = [0, 0, 255]
cap = cv2.VideoCapture(video_filename)

folder_name = 'bounding_box_data'

if not os.path.exists(folder_name):
    os.makedirs(folder_name)

csv_file_path = os.path.join(folder_name, f'{video_name}_bbox_coordinates.csv')

# Write header row
with open(csv_file_path, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow([
        'timestamp', 'x1', 'y1', 'x2', 'y2', 'avg_x', 'avg_y', 'radius', 'angle_radians',
        'frame_rate', 'new_avg_x', 'new_avg_y', 'avg_distance', 'angle_degrees',
        'distance_difference'  # Add the label for difference in avg_distance column
    ])

    start_time = time.time()
    prev_avg_x, prev_avg_y = None, None
    prev_radius = None
    prev_avg_distance = None  # Initialize prev_avg_distance
    frame_count = 0
    video_fps = cap.get(cv2.CAP_PROP_FPS)
    placeholder_added = False
    threshold = 10  # Threshold for difference in radius to add placeholder

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        hsvImage = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        lowerLimit, upperLimit = get_limits(color=PTColor)

        mask = cv2.inRange(hsvImage, lowerLimit, upperLimit)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        largest_area = 0
        largest_bbox = None

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 200:
                x1, y1, w, h = cv2.boundingRect(contour)
                x2 = x1 + w
                y2 = y1 + h

                avg_color = cv2.mean(frame[y1:y2, x1:x2])[:3]
                if avg_color != ignore_color:
                    if area > largest_area:
                        largest_area = area
                        largest_bbox = (x1, y1, x2, y2)

        if largest_bbox is not None:
            x1, y1, x2, y2 = largest_bbox
            frame = cv2.rectangle(frame, (x1, y1), (x2, y2), PTColor, 5)

            current_time = frame_count / video_fps

            avg_x = ((x1 + x2) / 2 - prev_avg_x) if prev_avg_x is not None else 0
            avg_y = -1 * ((y1 + y2) / 2 - prev_avg_y) if prev_avg_y is not None else 0

            radius = math.sqrt(avg_x**2 + avg_y**2)

            # Calculate new_avg_x, new_avg_y, and avg_distance using the appropriate conversion factor
            conversion_factor = get_conversion_factor(radius)
            new_avg_x = (avg_x / conversion_factor)
            new_avg_y = (avg_y / conversion_factor)
            avg_distance = radius / conversion_factor

            # Calculate angle_radians using new_avg_y and new_avg_x
            angle_radians = math.atan2(new_avg_y, new_avg_x)

            angle_degrees = math.degrees(angle_radians)

            # Calculate the difference between consecutive avg_distance values
            if prev_avg_distance is not None and avg_distance != '':
                diff_avg_distance = float(avg_distance) - prev_avg_distance
            else:
                diff_avg_distance = 0

            csvwriter.writerow([
                current_time, x1, y1, x2, y2, avg_x, avg_y, radius, angle_radians,
                video_fps, new_avg_x, new_avg_y, avg_distance, angle_degrees,
                diff_avg_distance  # Add the new column for difference in avg_distance
            ])

            prev_avg_distance = float(avg_distance) if avg_distance != '' else None

            if prev_avg_x is None and prev_avg_y is None:
                prev_avg_x, prev_avg_y = (x1 + x2) / 2, (y1 + y2) / 2
        else:
            # Placeholder values
            current_time = frame_count / video_fps
            csvwriter.writerow([
                current_time, -10000, -10000, -10000, -10000, -10000, -10000,
                -10000, -10000, video_fps, '', '', '', '', -10000  # Add 0 for diff_avg_distance in placeholder rows
            ])

        cv2.imshow('frame', frame)
        frame_count += 1

        # Manual adjustment of PTColor
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('u'):  # Increase Hue
            PTColor[0] = min(PTColor[0] + 1, 179)
        elif key == ord('d'):  # Decrease Hue
            PTColor[0] = max(PTColor[0] - 1, 0)
        elif key == ord('s'):  # Save current color
            initial_PTColor = PTColor.copy()

cap.release()
cv2.destroyAllWindows()
