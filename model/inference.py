# model/inference.py
from PIL import Image
import torch

def run_inference(model, image_path):

    results = model(image_path)  # inference
    return results