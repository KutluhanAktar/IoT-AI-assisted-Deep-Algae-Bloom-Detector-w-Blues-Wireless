# IoT AI-assisted Deep Algae Bloom Detector w/ Blues Wireless
#
# Raspberry Pi 4
#
# Take deep algae images w/ a borescope, collect water quality data,
# train a model, and get informed of the results over WhatsApp via Notecard. 
#
# By Kutluhan Aktar

import cv2
import serial
import json
import notecard
from periphery import I2C
from threading import Thread
from time import sleep
import os
import datetime
from edge_impulse_linux.image import ImageImpulseRunner

class deep_algae_detection():
    def __init__(self, modelfile):
        # Define the required settings to connect to Notehub.io.
        productUID = "<_product_UID_>"
        device_mode = "continuous"
        port = I2C("/dev/i2c-1")
        self.card = notecard.OpenI2C(port, 0, 0)
        sleep(5)
        # Connect to the given Notehub.io project.
        req = {"req": "hub.set"}
        req["product"] = productUID
        req["mode"] = device_mode
        rsp = self.card.Transaction(req)
        print("Notecard Connection Status:")
        print(rsp)
        # Initialize serial communication with Arduino Nano to obtain water quality sensor measurements and the given commands.
        self.arduino_nano = serial.Serial("/dev/ttyUSB0", 115200, timeout=1000)
        # Initialize the borescope camera feed.
        self.camera = cv2.VideoCapture(0)
        # Define the Edge Impulse FOMO model settings.
        dir_path = os.path.dirname(os.path.realpath(__file__))
        self.modelfile = os.path.join(dir_path, modelfile)
        self.detection_results = ""        
        
    def get_transferred_data_packets(self):
        # Obtain the transferred sensor measurements and commands from Arduino Nano via serial communication.
        if self.arduino_nano.in_waiting > 0:
            data = self.arduino_nano.readline().decode("utf-8", "ignore").rstrip()
            if(data.find("Run") >= 0):
                print("\nRunning an inference...")
                self.run_inference()
            if(data.find("Collect") >= 0):
                print("\nCapturing an image... ")
                self.save_img_sample()
            if(data.find("{") >= 0):
                self.sensors = json.loads(data)
                print("\nTemperature: " + self.sensors["Temperature"])
                print("pH: " + self.sensors["pH"])
                print("TDS: " + self.sensors["TDS"])
        sleep(1)

    def run_inference(self):
        # Run an inference with the FOMO model to detect potential deep algae bloom.
        with ImageImpulseRunner(self.modelfile) as runner:
            try:
                # Print the information of the Edge Impulse FOMO model converted to a Linux (ARMv7) application (.eim).
                model_info = runner.init()
                print('Loaded runner for "' + model_info['project']['owner'] + ' / ' + model_info['project']['name'] + '"')
                labels = model_info['model_parameters']['labels']
                # Get the latest frame captured by the borescope camera, resize it depending on the given model, and run an inference.
                model_img = self.latest_frame 
                features, cropped = runner.get_features_from_image(model_img)
                res = runner.classify(features)
                # Obtain the prediction (detection) results for each label (class).
                results = 0
                if "bounding_boxes" in res["result"].keys():
                    print('Found %d bounding boxes (%d ms.)' % (len(res["result"]["bounding_boxes"]), res['timing']['dsp'] + res['timing']['classification']))
                    for bb in res["result"]["bounding_boxes"]:
                        # Count the detected objects:
                        results+=1
                        print('\t%s (%.2f): x=%d y=%d w=%d h=%d' % (bb['label'], bb['value'], bb['x'], bb['y'], bb['width'], bb['height']))
                        # Draw bounding boxes for each detected object on the resized (cropped) image.
                        cropped = cv2.rectangle(cropped, (bb['x'], bb['y']), (bb['x'] + bb['width'], bb['y'] + bb['height']), (0, 255, 255), 1)
                # Save the modified image by appending the current date & time to its file name.
                date = datetime.datetime.now().strftime("%Y-%m-%d_%H_%M_%S")
                filename = 'detections/DET_{}.jpg'.format(date)
                cv2.imwrite(filename, cv2.cvtColor(cropped, cv2.COLOR_RGB2BGR))
                # After running an inference successfully, transfer the detection results
                # and the obtained water quality sensor measurements to Notehub.io.
                if results == 0:
                    self.detection_results = "Algae Bloom ➡ Not Detected!"
                else:
                    self.detection_results = "Potential Algae Bloom ➡ {}".format(results) 
                print("\n" + self.detection_results)
                self.send_data_to_Notehub(self.detection_results)
                
            # Stop the running inference.    
            finally:
                if(runner):
                    runner.stop() 

    def display_camera_feed(self):
        # Display the real-time video stream generated by the borescope camera.
        ret, img = self.camera.read()
        cv2.imshow("Deep Algae Bloom Detector", img)
        # Stop the video stream if requested.
        if cv2.waitKey(1) != -1:
            self.camera.release()
            cv2.destroyAllWindows()
            print("\nCamera Feed Stopped!")
        # Store the latest frame captured by the borescope camera.
        self.latest_frame = img
        
    def save_img_sample(self):    
        date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = './samples/IMG_{}.jpg'.format(date)
        # If requested, save the recently captured image (latest frame) as a sample.
        cv2.imwrite(filename, self.latest_frame)
        print("\nSample Saved Successfully: " + filename)
    
    def send_data_to_Notehub(self, results):
        # Send the model detection results and the obtained water quality sensor measurements transferred by Arduino Nano
        # to the webhook (twilio_whatsapp_sender) by performing an HTTP GET request via Notecard through Notehub.io.
        req = {"req": "web.get"}
        req["route"] = "TwilioWhatsApp"
        query = "?results=" + self.detection_results + "&temp=" + self.sensors["Temperature"] + "&pH=" + self.sensors["pH"] + "&TDS=" + self.sensors["TDS"]
        req["name"] = query.replace(" ", "%20")
        rsp = self.card.Transaction(req)
        print("\nNotehub Response:")
        print(rsp)
        sleep(2)
        
        
# Define the algae object.
algae = deep_algae_detection("model/iot-ai-assisted-deep-algae-bloom-detector-linux-armv7-v1.eim")

# Define and initialize threads.
def borescope_camera_feed():
    while True:
        algae.display_camera_feed()
        
def activate_received_commands():
    while True:
        algae.get_transferred_data_packets()

Thread(target=borescope_camera_feed).start()
Thread(target=activate_received_commands).start()
