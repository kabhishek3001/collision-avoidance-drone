import cv2
import mediapipe as mp
import time
import os

# --- Constants ---
CALIBRATION_FILE = "calibration_data.txt"
# Known distance (in cm) for calibration. The user will be asked to place their hand at this distance.
KNOWN_DISTANCE_FOR_CALIBRATION = 30.0

# --- Helper Functions ---

def get_hand_details(hand_landmarks, image_width, image_height):
    """
    Calculates the pixel width of the hand's palm and draws a bounding box.
    Uses stable landmarks (wrist, index MCP, pinky MCP) for width calculation.
    """
    points = hand_landmarks.landmark
    
    # Get coordinates of key palm points
    wrist_pt = points[mp.solutions.hands.HandLandmark.WRIST]
    index_mcp_pt = points[mp.solutions.hands.HandLandmark.INDEX_FINGER_MCP]
    pinky_mcp_pt = points[mp.solutions.hands.HandLandmark.PINKY_MCP]

    # Convert normalized coordinates to pixel coordinates
    x_coords = [p.x * image_width for p in [wrist_pt, index_mcp_pt, pinky_mcp_pt]]
    y_coords = [p.y * image_height for p in [wrist_pt, index_mcp_pt, pinky_mcp_pt]]

    # Calculate bounding box coordinates
    x_min, x_max = int(min(x_coords)), int(max(x_coords))
    y_min, y_max = int(min(y_coords)), int(max(y_coords))

    # The width is the horizontal distance between the index and pinky knuckles
    pixel_width = abs(x_max - x_min)

    return pixel_width, (x_min, y_min, x_max, y_max)

def estimate_distance(known_width_cm, focal_length, pixel_width):
    """
    Estimates the distance from the camera to the hand.
    Formula: Distance = (Known_Width * Focal_Length) / Pixel_Width
    """
    if pixel_width == 0:
        return 0
    return (known_width_cm * focal_length) / pixel_width

def calibrate():
    """
    Guides the user through a calibration process to find the focal length.
    Saves the calibrated values to a file.
    """
    print("--- Starting Calibration ---")
    
    # Get user's hand width
    while True:
        try:
            known_hand_width = float(input("Please enter your hand width in cm (measure across your palm): "))
            if known_hand_width > 0:
                break
            print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    print(f"\nPlease place your hand at a known distance of {KNOWN_DISTANCE_FOR_CALIBRATION} cm from the camera.")
    print("Ensure your palm is facing the camera.")
    print("Press 'c' to capture and calibrate.")

    cap = cv2.VideoCapture(0)
    mp_hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
    
    focal_length = 0
    
    while True:
        success, image = cap.read()
        if not success:
            continue
        
        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, _ = image.shape
        results = mp_hands.process(image_rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            pixel_width, bbox = get_hand_details(hand_landmarks, w, h)
            cv2.rectangle(image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            cv2.putText(image, f"Pixel Width: {pixel_width}", (bbox[0], bbox[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.putText(image, f"Place hand at {KNOWN_DISTANCE_FOR_CALIBRATION} cm and press 'c'", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.imshow("Calibration", image)

        if cv2.waitKey(5) & 0xFF == ord('c') and results.multi_hand_landmarks:
            pixel_width, _ = get_hand_details(results.multi_hand_landmarks[0], w, h)
            if pixel_width > 0:
                focal_length = (pixel_width * KNOWN_DISTANCE_FOR_CALIBRATION) / known_hand_width
                
                # Save calibration data
                with open(CALIBRATION_FILE, "w") as f:
                    f.write(f"{focal_length}\n")
                    f.write(f"{known_hand_width}\n")
                    
                print(f"\nCalibration successful! Focal Length calculated: {focal_length:.2f}")
                print(f"Saved to {CALIBRATION_FILE}")
                break
            else:
                print("Could not measure hand width. Please try again.")

    cap.release()
    cv2.destroyAllWindows()
    return focal_length, known_hand_width

def get_calibration_data():
    """
    Asks the user to calibrate or use a previous calibration.
    Returns the focal length and known hand width.
    """
    focal_length, known_width = None, None
    
    if os.path.exists(CALIBRATION_FILE):
        while True:
            choice = input("Use previous calibration (y) or run new calibration (n)? [y/n]: ").lower()
            if choice == 'y':
                try:
                    with open(CALIBRATION_FILE, "r") as f:
                        focal_length = float(f.readline().strip())
                        known_width = float(f.readline().strip())
                    print("Loaded calibration data successfully.")
                    return focal_length, known_width
                except (ValueError, IndexError):
                    print("Calibration file is corrupt. Please recalibrate.")
                    return calibrate()
            elif choice == 'n':
                return calibrate()
            else:
                print("Invalid choice. Please enter 'y' or 'n'.")
    else:
        print("No calibration file found.")
        return calibrate()

def main():
    """ Main function to run the hand distance estimator. """
    focal_length, known_hand_width = get_calibration_data()
    
    if focal_length is None or known_hand_width is None:
        print("Could not obtain calibration data. Exiting.")
        return

    # Initialize MediaPipe and OpenCV
    mp_hands = mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5)
    mp_drawing = mp.solutions.drawing_utils

    cap = cv2.VideoCapture(0)
    
    print("\nStarting distance estimation... Press 'q' to quit.")

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            continue

        image = cv2.flip(image, 1)
        h, w, _ = image.shape
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        results = mp_hands.process(image_rgb)

        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            
            # Draw landmarks
            mp_drawing.draw_landmarks(image, hand_landmarks, mp.solutions.hands.HAND_CONNECTIONS)
            
            # Get hand width and bounding box
            pixel_width, bbox = get_hand_details(hand_landmarks, w, h)
            
            # Draw bounding box around the palm
            cv2.rectangle(image, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 255), 2)
            
            # Estimate and display distance
            if pixel_width > 0:
                distance = estimate_distance(known_hand_width, focal_length, pixel_width)
                
                # Display distance
                cv2.putText(image, f"Distance: {distance:.2f} cm", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                
                # Display warning if too close
                if distance < 60:
                    cv2.putText(image, "Too Close!! Move Back", (w // 2 - 200, h // 2), cv2.FONT_HERSHEY_TRIPLEX, 1.2, (0, 0, 255), 2)
        
        cv2.imshow('Hand Distance Estimator', image)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    mp_hands.close()
    cap.release()
    cv2.destroyAllWindows()
    print("Program finished.")


if __name__ == '__main__':
    main()