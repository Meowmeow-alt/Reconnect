import cv2
import numpy as np
from insightface.app import FaceAnalysis

window_name = 'Image'
app = FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "recognition"])
app.prepare(ctx_id=0, det_size=(640, 640))


def get_embed(img):
    faces = app.get(img)
    if img is None:
        print("Could not open or find the image")
    for face in faces:
        return face['embedding']
    
def cosine(i1,i2):
    i1 = i1.flatten()
    i2 = i2.flatten()
    cosine = (i1 @ i2) / (np.linalg.norm(i1) * np.linalg.norm(i2))
    return cosine


cap = cv2.VideoCapture(0) # mở webcam

img1 = cv2.imread('frontend/static/img/profile/57103407-360c-4a9d-9bd9-e888708c27ea_z4864360310264_37d2988e70da185a0e68aabbdb6bdfe7.jpg')
btienne = get_embed(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
# Check if the webcam is opened correctly
if not cap.isOpened():
    raise IOError("Cannot open webcam")

while True:
    ret, img = cap.read() # ret: take frame successfully or not
    if not ret:
        break


    faces = app.get(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    for face in faces:
        bbox = face['bbox'].astype(float)
        start_point = bbox[:2].astype(int)
        end_point = bbox[2:].astype(int)
        thickness = 2
        cos = cosine(btienne, face["embedding"])
        
        if cos >= 0.5:
            img = cv2.rectangle(img, start_point, end_point, (255, 0, 0) , thickness)
            cv2.putText(img, f"Bao Tien de thuong {cos:.2f}", (start_point[0], start_point[1] - 10),
                fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                fontScale = 0.6,
                color = (255, 255, 255),
                thickness=2)
        else:
            img = cv2.rectangle(img, start_point, end_point, (255, 0, 0) , thickness)
            cv2.putText(img, f"{cos:.2f}", (start_point[0], start_point[1] - 10),
                        fontFace = cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale = 0.6,
                    color = (255, 255, 255),
                    thickness=2)

        keypoints = face['kps'].astype(int)
        for point in keypoints:
            img = cv2.circle(img, point, 3, (0, 0, 255) , thickness)
    
    cv2.imshow(window_name, img)

    c = cv2.waitKey(100) # wait 1ms user press button
    if c == 27: # ESC button
        break


cap.release()
cv2.waitKey(0)
cv2.destroyAllWindows()

# bbox là khung bao quanh đầu
# kps là bao gồm toạ độ mắt mũi miệng
# det_score là phần trăm có gương mặt
# embeddings là array nhận diện gương mặt