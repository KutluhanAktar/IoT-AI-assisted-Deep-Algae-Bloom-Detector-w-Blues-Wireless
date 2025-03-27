       /////////////////////////////////////////////
      //  IoT AI-assisted Deep Algae Bloom       //
     //      Detector w/ Blues Wireless         //
    //             ---------------             //
   //             (Arduino Nano)              //
  //             by Kutluhan Aktar           //
 //                                         //
/////////////////////////////////////////////

//
// Take deep algae images w/ a borescope, collect water quality data, train a model, and get informed of the results over WhatsApp via Notecard.
//
// For more information:
// https://www.theamplituhedron.com/projects/IoT_AI_assisted_Deep_Algae_Bloom_Detector_w_Blues_Wireless
//
//
// Connections
// Arduino Nano :
//                                DFRobot Analog pH Sensor Pro Kit
// A0   --------------------------- Signal
//                                DFRobot Analog TDS Sensor
// A1   --------------------------- Signal
//                                DS18B20 Waterproof Temperature Sensor
// D2   --------------------------- Data
//                                Keyes 10mm RGB LED Module (140C05)
// D3   --------------------------- R
// D5   --------------------------- G
// D6   --------------------------- B
//                                Control Button (R)
// D7   --------------------------- +
//                                Control Button (C)
// D8   --------------------------- +


// Include the required libraries.
#include <OneWire.h>
#include <DallasTemperature.h>

// Define the water quality sensor pins:  
#define pH_sensor   A0
#define tds_sensor  A1

// Define the pH sensor settings:
#define pH_offset 0.21
#define pH_voltage 5
#define pH_voltage_calibration 0.96
#define pH_array_length 40
int pH_array_index = 0, pH_array[pH_array_length];

// Define the TDS sensor settings:
#define tds_voltage 5
#define tds_array_length 30
int tds_array[tds_array_length], tds_array_temp[tds_array_length];
int tds_array_index = -1;

// Define the DS18B20 waterproof temperature sensor settings:
#define ONE_WIRE_BUS 2
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature DS18B20(&oneWire);

// Define the RGB LED pins:
#define redPin     3
#define greenPin   5
#define bluePin    6

// Define the control button pins:
#define button_r   7
#define button_c   8

// Define the data holders:
float pH_value, pH_r_value, temperature, tds_value;
long timer = 0, r_timer = 0, t_timer = 0;

void setup(){
  // Initialize the hardware serial port (Serial) to communicate with Raspberry Pi via serial communication. 
  Serial.begin(115200);

  // RGB:
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  adjustColor(0,0,0);

  // Buttons:
  pinMode(button_r, INPUT_PULLUP);
  pinMode(button_c, INPUT_PULLUP);  

  // Initialize the DS18B20 sensor.
  DS18B20.begin();

}

void loop(){   
  if(millis() - timer > 20){
    // Calculate the pH measurement every 20 milliseconds.
    pH_array[pH_array_index++] = analogRead(pH_sensor);
    if(pH_array_index == pH_array_length) pH_array_index = 0;
    float pH_output = avr_arr(pH_array, pH_array_length) * pH_voltage / 1024;
    pH_value = 3.5 * pH_output + pH_offset;

    // Calculate the TDS measurement every 20 milliseconds.
    tds_array[tds_array_index++] = analogRead(tds_sensor);
    if(tds_array_index == tds_array_length) tds_array_index = 0;
    
    // Update the timer.  
    timer = millis();
  }
  
  if(millis() - r_timer > 800){
    // Get the accurate pH measurement every 800 milliseconds.
    pH_r_value = pH_value + pH_voltage_calibration;
    //Serial.print("pH: "); Serial.println(pH_r_value);

    // Obtain the temperature measurement in Celsius.
    DS18B20.requestTemperatures(); 
    temperature = DS18B20.getTempCByIndex(0);
    //Serial.print("Temperature: "); Serial.print(temperature); Serial.println(" °C");

    // Get the accurate TDS measurement every 800 milliseconds.
    for(int i=0; i<tds_array_length; i++) tds_array_temp[i] = tds_array[i];
    float tds_average_voltage = getMedianNum(tds_array_temp, tds_array_length) * (float)tds_voltage / 1024.0;
    float compensationCoefficient = 1.0 + 0.02 * (temperature - 25.0);
    float compensatedVoltage = tds_average_voltage / compensationCoefficient;
    tds_value = (133.42*compensatedVoltage*compensatedVoltage*compensatedVoltage - 255.86*compensatedVoltage*compensatedVoltage + 857.39*compensatedVoltage)*0.5;
    //Serial.print("TDS: "); Serial.print(tds_value); Serial.println(" ppm\n\n");

    // Update the timer.
    r_timer = millis();
  }

  if(millis() - t_timer > 3000){
    // Every three seconds, transfer the collected water quality sensor measurements in the JSON format to Raspberry Pi via serial communication. 
    String data = "{\"Temperature\": \"" + String(temperature) + " °C\", "
                  + "\"pH\": \"" + String(pH_r_value) + "\", "
                  + "\"TDS\": \"" + String(tds_value) + "  ppm\"}";
    Serial.println(data);

    adjustColor(255,0,255);
    delay(2000);
    adjustColor(0,0,0);
    
    // Update the timer.
    t_timer = millis();
    
  }

  // Send commands to Raspberry Pi via serial communication.
  if(!digitalRead(button_r)){ Serial.println("Run Inference!"); adjustColor(0,255,0); delay(1000); adjustColor(0,0,0); }
  if(!digitalRead(button_c)){ Serial.println("Collect Data!"); adjustColor(0,0,255); delay(1000); adjustColor(0,0,0); }
}

double avr_arr(int* arr, int number){
  int i, max, min;
  double avg;
  long amount=0;
  if(number<=0){ Serial.println("ORP Sensor Error: 0"); return 0; }
  if(number<5){
    for(i=0; i<number; i++){
      amount+=arr[i];
    }
    avg = amount/number;
    return avg;
  }else{
    if(arr[0]<arr[1]){ min = arr[0];max=arr[1]; }
    else{ min = arr[1]; max = arr[0]; }
    for(i=2; i<number; i++){
      if(arr[i]<min){ amount+=min; min=arr[i];}
      else{
        if(arr[i]>max){ amount+=max; max=arr[i]; } 
        else{
          amount+=arr[i];
        }
      }
    }
    avg = (double)amount/(number-2);
  }
  return avg;
}

int getMedianNum(int bArray[], int iFilterLen){  
  int bTab[iFilterLen];
  for (byte i = 0; i<iFilterLen; i++) bTab[i] = bArray[i];
  int i, j, bTemp;
  for (j = 0; j < iFilterLen - 1; j++) {
    for (i = 0; i < iFilterLen - j - 1; i++){
      if (bTab[i] > bTab[i + 1]){
        bTemp = bTab[i];
        bTab[i] = bTab[i + 1];
        bTab[i + 1] = bTemp;
      }
    }
  }
  if ((iFilterLen & 1) > 0) bTemp = bTab[(iFilterLen - 1) / 2];
  else bTemp = (bTab[iFilterLen / 2] + bTab[iFilterLen / 2 - 1]) / 2;
  return bTemp;
}

void adjustColor(int r, int g, int b){
  analogWrite(redPin, (255-r));
  analogWrite(greenPin, (255-g));
  analogWrite(bluePin, (255-b));
}
