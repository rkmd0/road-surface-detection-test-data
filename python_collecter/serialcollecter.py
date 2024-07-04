# simple code to collect data with an senseboxMCU
# what to do:
# upload the 'basic_readings.ino' code to the senseboxMCU
# connect the senseboxMCU to the computer via a long USB cable
# ---> might have the change the settings for 'zuklappen' (laptop)
# run the code (change the label if necessary)

'''
possible bugs:
paula experienced the same annoying bug where the com port wont get recognized after x-runs (randomly) because the serial port overflows (?)
possible solution to this: use a sd card, increase the sleep to avoid overwhelming the serial port or restart the mcu via reset button
'''

# general comments:
# needed all these exception because i couldnt figure out a few problem - might delete later
# currently data gets collected each 0.1 seconds (Filter Bandwidth is set to 21Hz)


import serial # this library provides a way to read and write data to the serial port
import time
import keyboard # for checking if a key is pressed - to stop the 'infinite loop' :-)
import csv # collected data gets into a csv for training purposes
from datetime import datetime
from pynput import mouse # necessary for the mouse listener - for advanced data collection
import os

# function to get the next filename by appending a counter to the base name
# simple and fast way to create new files (not appending)

def get_next_filename(base_name, extension):
    counter = 1
    while True:
        file_name = f"{base_name}{counter}.{extension}"
        if not os.path.exists(file_name):
            return file_name
        counter += 1

# configure the serial port
ser = serial.Serial('COM7', 115200)  # 'COM7' serial port - change if necessary (my first board had 'COM5')
time.sleep(1)  # wait for the Arduino to reset

# list to store the data for saving
data_records = []

# currently not used because: couldnt come so far to actually collect 'advanced' road surface quality data
# but idea here is simple:
# value will always be 'normal' unless the left or right mouse button is pressed
# to do the labeling work on runtime

def on_click(x, y, button, pressed):
    global bumpiness
    if pressed:
        if button == mouse.Button.left:
            bumpiness = 'lightly'
            #print("bumpiness level: lightly") # verify test
        elif button == mouse.Button.right:
            bumpiness = 'a lot' # might have to change this value one day
            #print("bumpiness level: a lot") # verify test
    else:
        bumpiness = 'normal'
        # print("Bumpiness level: normal") # verify test

# initialize the bumpiness level to 'normal'
bumpiness = 'normal'

try:
    # create a mouse listener
    listener = mouse.Listener(on_click=on_click)
    listener.start()

    while True:
        if keyboard.is_pressed('1'):  # check if 1 is pressed
            print("Exiting loop.")
            break  # exit the while loop

        # read a line from the serial port
        line = ser.readline().decode('utf-8').strip()

        # if line is not empty
        if line:
        
            # split the line into individual key-value pairs
            pairs = line.split(',')
            
            # extract values
            accel_x = float(pairs[0].split(':')[1])
            accel_y = float(pairs[1].split(':')[1])
            accel_z = float(pairs[2].split(':')[1])
            gyro_x = float(pairs[3].split(':')[1])
            gyro_y = float(pairs[4].split(':')[1])
            gyro_z = float(pairs[5].split(':')[1])

            # ensure there are exactly 6 values
            if len(pairs) != 6:
                print(f"Unexpected number of values: {len(pairs)}")
                continue

            # get current timestamp
            timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]

            # append the data to the list of records
            data_record = {
                'timestamp': timestamp,
                'accel_x': accel_x,
                'accel_y': accel_y,
                'accel_z': accel_z,
                'gyro_x': gyro_x,
                'gyro_y': gyro_y,
                'gyro_z': gyro_z,
                'label': 'kiesweg',
                'bumpiness': bumpiness
            }
            data_records.append(data_record)

            # print the values in one line - honestly not necessarily needed but i like to have some way of 'verification' that data is collected
            print(f"Timestamp: {timestamp}, Acceleration: X={accel_x}, Y={accel_y}, Z={accel_z}, "
                f"Gyroscope: X={gyro_x}, Y={gyro_y}, Z={gyro_z}, Bumpiness: {bumpiness}")
    
        # wait for a short period to avoid overwhelming the serial port
        time.sleep(0.1)

except KeyboardInterrupt:
    pass

finally:
    listener.stop()  # stop the mouse listener
    # check if data_records is not empty before writing to file
    if data_records:
        # save data to CSV file
        #csv_filename = 'sensor_data_s1chloss9.csv'
        base_name = 'sensor_kiesweg_test_1454_'
        csv_filename = get_next_filename(base_name, 'csv') # add the counter to the filename
        try:
            with open(csv_filename, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z', 'label', 'bumpiness']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data_records)
            print(f"CSV file saved: {csv_filename}")
        except Exception as e:
            print(f"Error saving CSV file: {e}")
    else:
        print("No data to write to CSV file.")

    ser.close()
    print("Program stopped.")