# IoT AI-assisted Deep Algae Bloom Detector w/ Blues Wireless
#
# Raspberry Pi 4
#
# Take deep algae images w/ a borescope, collect water quality data,
# train a model, and get informed of the results over WhatsApp via Notecard. 
#
# By Kutluhan Aktar

import requests
from glob import glob
from time import sleep

# Define the webhook path for transferring the given images to the server — save_img.php.
webhook_img_path = "https://www.theamplituhedron.com/twilio_whatsapp_sender/save_img.php"
# Obtain all image files in the detections folder.
files = glob("./detections/*.jpg")

def send_image(file_path):
    files = {'captured_image': open("./"+file_path, 'rb')}
    # Make an HTTP POST request to the webhook so as to send the given image file.
    request = requests.post(webhook_img_path, files=files)
    print("Image File Transferred: " + file_path)
    # Print the response from the server.
    print("App Response => " + request.text + "\n")
    sleep(2)

# If the detections folder contains images, send each retrieved image file to the webhook via HTTP POST requests
# in order to update the detections folder on the server.
if(files): 
    i = 0
    t = len(files)
    print("Detected Image Files: {}\n".format(t))
    for img in files:
        i+=1
        print("Uploading Images: {} / {}".format(i, t))
        send_image(img)
else:
    print("No Detection Image Detected!")