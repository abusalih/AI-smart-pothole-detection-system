from inference_sdk import InferenceHTTPClient
import cv2

CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key="BgHFp2MKPApEAjXl9joR"
)

result = CLIENT.infer("test.jpg", model_id="pothole-detection-bfeeg-hp6tw/1")

# Load image
image = cv2.imread("test.jpg")

# Draw bounding boxes
for prediction in result["predictions"]:
    x = int(prediction["x"])
    y = int(prediction["y"])
    w = int(prediction["width"])
    h = int(prediction["height"])

    # Convert center format to top-left format
    x1 = int(x - w / 2)
    y1 = int(y - h / 2)
    x2 = int(x + w / 2)
    y2 = int(y + h / 2)

    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 3)

# Save output image
cv2.imwrite("output.jpg", image)

print("Detection completed. Output saved as output.jpg")