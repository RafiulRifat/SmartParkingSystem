# Smart Parking System – IoT Based Smart Parking Management

An IoT-based smart parking management system combining an ESP32 parking controller, Raspberry Pi camera monitoring, and a Flask web server.

## Features

- Real-time parking slot monitoring
- Automatic vehicle entry and exit detection
- ESP32-based parking control
- Ultrasonic sensor-based slot detection
- IR-based entry/exit detection
- Automatic servo gate control
- Buzzer and LED status indication
- Raspberry Pi camera integration
- Live camera streaming in the Admin panel
- Automatic ENTRY and EXIT image capture
- Parking history with captured images
- Admin dashboard
- Reservation management
- SQLite database

## System Architecture

```text
ESP32
 ├── Ultrasonic Sensors
 ├── IR Sensors
 ├── Servo Gate
 ├── LEDs
 └── Buzzer
       │
       ▼
   Flask Server
       │
       ├── Web Dashboard
       ├── Admin Panel
       ├── Parking History
       ├── Reservation System
       └── SQLite Database
       │
       ▲
 Raspberry Pi
 └── Camera
     ├── Live Video
     └── Event Capture