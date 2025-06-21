# 🤚✈️ Collision Avoidance using Palm Detection (Drone Safety System)

This project demonstrates a **hand gesture-based collision avoidance system** using a webcam or Pi camera. The core idea is simple: **if a drone comes too close to a human, it can detect the palm of a hand and stop or hover** — ensuring safety during flight testing or operation.

---

## 📹 Demo

![image](https://github.com/user-attachments/assets/56b50d52-a9c5-4476-acf0-3aad5807cf34)


---

## 🧠 Features

- 🖐 Detects human palm using **MediaPipe**
- 📏 Estimates real-time distance using **camera-based calibration**
- ⚠️ Shows on-screen warning when user is too close (`< 60 cm`)
- 📁 Saves calibration data for future sessions
- 🛠️ Can be extended to **trigger drone commands** using MAVLink, ROS, etc.

---

## 📂 File Structure
```bash
collision-avoidance-drone/
│
├── hand_estimation.py # Main Python script
├── calibration_data.txt # Auto-generated file to store focal length and hand width
└── README.md # This file
```

---

## 🛠️ Requirements

Make sure you have the following Python libraries installed:

```bash
pip install opencv-python mediapipe

```

🧪 Calibration
Before using the system, you must calibrate your hand:

Run the script:

```bash
python hand_estimation.py
```
Enter your actual hand width (in cm)

Place your palm exactly 30 cm from the camera and press c

This will generate calibration_data.txt containing:

php-template
```bash
<focal_length>
<your_hand_width>
```
▶️ How to Run
After calibration, simply run:
```bash
python hand_estimation.py
```
Then:

Show your palm to the camera

Get real-time distance estimate on-screen

Warning will appear if your hand is within 60 cm
