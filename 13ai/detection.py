

import numpy as np
import cv2
import base64
from io import BytesIO
from PIL import Image
from ultralytics import YOLO

CONF_THRESHOLD=0.5

def detect(img, width, height, timestamp):
    # print(type(img), width, height)
    
    # Check if img is a base64 string
    if isinstance(img, str) and img.startswith('data:image'):
        # Extract the base64 data (remove the prefix)
        base64_string = img.split(',')[1]
        # Decode base64 string
        img_data = base64.b64decode(base64_string)
        # Convert to image
        img_pil = Image.open(BytesIO(img_data)).convert('RGBA')
        pixel_data = np.array(img_pil, dtype=np.uint8)
    else:
        pixel_data = np.array(img, dtype=np.uint8)
    
    # Reshape to RGBA format
    img_array = pixel_data.reshape((height, width, 4))
    # print(img_array)
    # Convert to BGR (OpenCV format)
    bgr_img = cv2.cvtColor(img_array, cv2.COLOR_RGBA2BGR)
    result=aimodel(bgr_img)
    # print('result',result)
    return result

def aimodel(image):
    # Load the YOLOv8 model (replace with your own model if needed)
    model = YOLO('aimodel/modelv0.3.5.pt')  # Using nano version for smaller size
    # Perform detection
    results = model(image, conf=CONF_THRESHOLD)
    
    # Process results
    detections = []
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            
            detections.append({
                'class': class_name,
                'class_id': class_id,
                'confidence': confidence,
                'bbox': [x1, y1, x2, y2]
            })
    
    return detections