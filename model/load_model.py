# model/load_model.py
import os
import torch
from ultralytics import YOLO

def load_model(model_path="yolov8n.pt"):
    # PyTorch 2.6+ 호환성을 위한 환경 변수 설정
    os.environ['TORCH_WEIGHTS_ONLY'] = 'False'
    
    model = YOLO(model_path)
    return model