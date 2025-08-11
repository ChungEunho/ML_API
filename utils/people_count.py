#utils/people_count.py
import sys
import os

from model.load_model import load_model
from model.inference import run_inference
from PIL import Image, ImageDraw, ImageFont
import warnings
warnings.simplefilter("ignore", FutureWarning)

def count_people_in_image(model, image_path, confidence_threshold=0.1):
    # 이미지 추론
    results = run_inference(model, image_path)
    result = results[0]
    
    # 클래스 인덱스와 이름 매핑 가져오기
    names = model.model.names
    
    # 사람 클래스 인덱스 찾기 (COCO 데이터셋에서 'person'은 보통 0번)
    person_class_id = 0  # COCO 데이터셋 기준
    
    # 사람만 필터링
    people_detections = []
    for i in range(len(result.boxes)):
        class_id = int(result.boxes.cls[i])
        confidence = result.boxes.conf[i]
        
        # 사람 클래스이고 신뢰도가 임계값 이상인 경우만
        if class_id == person_class_id and confidence >= confidence_threshold:
            people_detections.append({
                'bbox': result.boxes.xyxy[i].tolist(),
                'confidence': confidence,
                'index': i
            })
    
    return people_detections

def visualize_people_count(image_path, people_detections, output_path="test_output/people_count_result.jpg"):
    # 이미지 열기
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    
    # 사람 수 카운트
    people_count = len(people_detections)
    
    # 각 감지된 사람에 대해 바운딩 박스 그리기
    for i, detection in enumerate(people_detections):
        bbox = detection['bbox']
        x1, y1, x2, y2 = map(int, bbox)
        confidence = detection['confidence']
        
        # 바운딩 박스 그리기 (녹색으로 사람 표시)
        draw.rectangle([x1, y1, x2, y2], outline="green", width=3)
        
        # 사람 번호와 신뢰도 표시
        label = f"Person {i+1} ({confidence:.2f})"
        text_bbox = draw.textbbox((x1, y1), label, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        text_bg = [x1, y1 - text_height, x1 + text_width, y1]
        draw.rectangle(text_bg, fill="green")
        draw.text((x1, y1 - text_height), label, fill="white", font=font)
    
    # 전체 사람 수를 이미지 상단에 표시
    count_text = f"Total People Count: {people_count}"
    count_bbox = draw.textbbox((10, 10), count_text, font=font)
    count_width = count_bbox[2] - count_bbox[0]
    count_height = count_bbox[3] - count_bbox[1]
    
    # 배경 박스 그리기
    draw.rectangle([10, 10, 10 + count_width + 20, 10 + count_height + 10], fill="blue")
    draw.text((20, 15), count_text, fill="white", font=font)
    
    # 결과 이미지 저장
    image.save(output_path)
    return image

def test(confidence_threshold=0.1, test_img="test_input/bus.jpg"):
    model = load_model()
    print("=== ROBOT Perception: Population count system ===")
    people_detections = count_people_in_image(model, test_img, confidence_threshold)

    print(f"\nDetected people number: {len(people_detections)} persons")
    for i, detection in enumerate(people_detections):
        print(f"Person {i+1}: confidence {detection['confidence']:.2f}")

    # 시각화 및 저장
    visualize_people_count(test_img, people_detections, "test_output/people_count_result.jpg")
    print("\nResult img saved as: people_count_result.jpg.")

    # 로봇 Perception 시나리오 출력
    print(f"\n=== Robot Perception Result ===")
    print(f"Population in the scene: {len(people_detections)}")
    if len(people_detections) > 0:
        print("Person(s) detected. Need Caution.")
    else:
        print("Perons(s) not detected. It is safe.")

# 테스트를 실행하려면 직접 호출하세요
if __name__ == "__main__":
    test()