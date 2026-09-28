#include <WiFi.h>
#include <HTTPClient.h>
#include <ESP32Servo.h>



// ===============================
// WIFI
// ===============================

const char* ssid = "SmartParking";

const char* password = "12345678";


String serverURL =
"http://192.168.43.81:5000/update";





// ===============================
// ULTRASONIC
// ===============================

#define TRIG1 25
#define ECHO1 35


#define TRIG2 26
#define ECHO2 34






// ===============================
// LED
// ===============================

#define GREEN1 18
#define RED1   19


#define GREEN2 22
#define RED2   23






// ===============================
// IR + SERVO + BUZZER
// ===============================

#define IR_ENTRY 14

#define IR_EXIT 33


#define SERVO_PIN 13


#define BUZZER_PIN 27





Servo gateServo;







// ===============================
// SETTINGS
// ===============================

const float OCCUPIED_DISTANCE = 15;


#define GATE_OPEN 90

#define GATE_CLOSE 0







// ===============================
// COUNTER
// ===============================

int totalEntries = 0;


int totalExit = 0;


int currentCars = 0;







// ===============================
// IR MEMORY
// ===============================

bool lastEntry = HIGH;


bool lastExit = HIGH;



unsigned long lastEntryTime = 0;


unsigned long lastExitTime = 0;



const unsigned long debounceTime = 2000;








// ===============================
// DISTANCE
// ===============================

float readDistance(
int trig,
int echo
)

{


digitalWrite(
trig,
LOW
);


delayMicroseconds(3);



digitalWrite(
trig,
HIGH
);


delayMicroseconds(10);



digitalWrite(
trig,
LOW
);




long duration =

pulseIn(
echo,
HIGH,
30000
);





if(duration==0)

return -1;





return duration*0.0343/2;



}









// ===============================
// BUZZER
// ===============================

void beep()

{


digitalWrite(
BUZZER_PIN,
HIGH
);


delay(200);


digitalWrite(
BUZZER_PIN,
LOW
);



}









// ===============================
// SERVO
// ===============================

void openGate()

{


gateServo.write(
GATE_OPEN
);


delay(3000);


gateServo.write(
GATE_CLOSE
);



}









// ===============================
// SEND DATA TO FLASK
// ===============================

void sendData(

String slot1,

String slot2,

float d1,

float d2,

String gate,

String buzzer,

String event

)

{


if(WiFi.status()==WL_CONNECTED)

{


HTTPClient http;



http.begin(serverURL);



http.addHeader(

"Content-Type",

"application/json"

);





String json = "{";



json += "\"slot1\":\""+slot1+"\",";



json += "\"slot2\":\""+slot2+"\",";





json += "\"distance1\":"+String(d1)+",";



json += "\"distance2\":"+String(d2)+",";





json += "\"gate\":\""+gate+"\",";



json += "\"buzzer\":\""+buzzer+"\",";





// NEW STEP 2 EVENT DATA

json += "\"event\":\""+event+"\",";





json += "\"available\":"+String(2-currentCars)+",";



json += "\"entries\":"+String(totalEntries)+",";



json += "\"exit\":"+String(totalExit)+",";



json += "\"inside\":"+String(currentCars);




json += "}";







int response =

http.POST(json);






Serial.print(
"Server Response:"
);



Serial.println(response);





http.end();



}



}





// ===============================
// SETUP
// ===============================


void setup()

{


Serial.begin(115200);





pinMode(TRIG1,OUTPUT);

pinMode(ECHO1,INPUT);



pinMode(TRIG2,OUTPUT);

pinMode(ECHO2,INPUT);







pinMode(GREEN1,OUTPUT);

pinMode(RED1,OUTPUT);



pinMode(GREEN2,OUTPUT);

pinMode(RED2,OUTPUT);







pinMode(IR_ENTRY,INPUT);

pinMode(IR_EXIT,INPUT);



pinMode(BUZZER_PIN,OUTPUT);








gateServo.setPeriodHertz(50);



gateServo.attach(

SERVO_PIN,

500,

2400

);



gateServo.write(

GATE_CLOSE

);









WiFi.begin(

ssid,

password

);



Serial.print(

"Connecting WiFi"

);





while(

WiFi.status()!=WL_CONNECTED

)

{


delay(500);


Serial.print(".");



}





Serial.println();


Serial.println(

"WiFi Connected"

);



Serial.println(

"SMART PARKING READY"

);



}











// ===============================
// LOOP
// ===============================


void loop()

{


// Event reset every cycle

String event = "NONE";





// ===============================
// READ DISTANCE
// ===============================


float distance1 =

readDistance(

TRIG1,

ECHO1

);




delay(60);




float distance2 =

readDistance(

TRIG2,

ECHO2

);








bool slot1 =

(

distance1 > 0 &&

distance1 <= OCCUPIED_DISTANCE

);






bool slot2 =

(

distance2 > 0 &&

distance2 <= OCCUPIED_DISTANCE

);









// ===============================
// SLOT 1 LED
// ===============================


if(slot1)

{


digitalWrite(

RED1,

HIGH

);


digitalWrite(

GREEN1,

LOW

);



}

else

{


digitalWrite(

RED1,

LOW

);


digitalWrite(

GREEN1,

HIGH

);



}









// ===============================
// SLOT 2 LED
// ===============================


if(slot2)

{


digitalWrite(

RED2,

HIGH

);


digitalWrite(

GREEN2,

LOW

);



}

else

{


digitalWrite(

RED2,

LOW

);


digitalWrite(

GREEN2,

HIGH

);



}









String gate = "CLOSED";


String buzzer = "OFF";









// ===============================
// READ IR SENSOR
// ===============================


int entryState =

digitalRead(IR_ENTRY);



int exitState =

digitalRead(IR_EXIT);











// ===============================
// ENTRY EVENT
// ===============================


if(

lastEntry == HIGH &&

entryState == LOW

)

{


if(

millis() - lastEntryTime > debounceTime

)

{


if(currentCars < 2)

{


totalEntries++;


currentCars++;





event = "ENTRY";





Serial.println(

"CAR ENTER"

);




gate = "OPEN";


openGate();



}

else

{


Serial.println(

"PARKING FULL"

);



buzzer = "ON";


beep();



}




lastEntryTime = millis();



}



}












// ===============================
// EXIT EVENT
// ===============================


if(

lastExit == HIGH &&

exitState == LOW

)

{


if(

millis() - lastExitTime > debounceTime

)

{


if(currentCars > 0)

{


totalExit++;


currentCars--;





event = "EXIT";





Serial.println(

"CAR EXIT"

);





gate = "OPEN";


openGate();



}

else

{


Serial.println(

"NO CAR INSIDE"

);



}




lastExitTime = millis();



}



}











// Save IR state


lastEntry = entryState;


lastExit = exitState;











// ===============================
// SERIAL MONITOR
// ===============================


Serial.println(

"======================"

);



Serial.print(

"Slot 1: "

);



if(slot1)

Serial.println(

"OCCUPIED"

);

else

Serial.println(

"EMPTY"

);






Serial.print(

"Slot 2: "

);



if(slot2)

Serial.println(

"OCCUPIED"

);

else

Serial.println(

"EMPTY"

);







Serial.print(

"Distance 1: "

);


Serial.print(distance1);


Serial.println(

" cm"

);







Serial.print(

"Distance 2: "

);


Serial.print(distance2);


Serial.println(

" cm"

);







Serial.print(

"Cars Inside: "

);


Serial.println(currentCars);







Serial.print(

"Total Entry: "

);


Serial.println(totalEntries);







Serial.print(

"Total Exit: "

);


Serial.println(totalExit);







Serial.print(

"EVENT: "

);


Serial.println(event);





Serial.println(

"======================"

);











// ===============================
// SEND DATA TO FLASK
// ===============================


sendData(


slot1 ? "OCCUPIED":"EMPTY",



slot2 ? "OCCUPIED":"EMPTY",



distance1,



distance2,



gate,



buzzer,



event



);








delay(1000);



}