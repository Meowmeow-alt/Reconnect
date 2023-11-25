import numpy as np
import pickle
import cv2
from insightface.app import FaceAnalysis

face_analysis = FaceAnalysis(name="buffalo_l", allowed_modules=["detection", "recognition"])
face_analysis.prepare(ctx_id=0, det_size=(640, 640))

def get_embed(img):
    faces = face_analysis.get(img)
    if img is None:
        return "Could not open or find the image", 403
    if len(faces) != 1:
        return "There should be 1 face only", 403
    return faces[0]['embedding']

def read(file):
    return cv2.cvtColor(cv2.imread(file), cv2.COLOR_BGR2RGB)
     
