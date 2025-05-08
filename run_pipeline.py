# 파일: run_pipeline.py
# Description: 전체 파이프라인을 자동 실행하는 통합 스크립트입니다.
#              - 키워드(역 이름)와 크롤링할 가게 수를 입력받아,
#              - ① 가게/리뷰 크롤링 → ② 리뷰 전처리 및 JSON 변환 → ③ 리뷰 임베딩 및 벡터DB 저장 → ④ Gradio 챗봇 실행의 순서로 처리합니다.
# Author: 통합버전
# Date: 2025.04.29
# Requirements: subprocess, sys, os

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # 현재 경로
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 상위 루트

import os
import subprocess

# 역이름, 크롤링할 가게 수 입력받기
keyword = input("역 이름을 입력하세요 (예: 충정로역): ").strip()
while True:
    try:
        store_limit = int(input("크롤링할 가게 개수를 입력하세요 (최대 200개): ").strip())
        if 1 <= store_limit <= 200:
            break
        else:
            print("⚠️ 1 이상 200 이하의 숫자를 입력해주세요.")
    except ValueError:
        print("⚠️ 숫자를 입력해주세요.")
        
print("====== [1/4] 리뷰 및 가게 정보 크롤링 시작 ======")
subprocess.run(["python", "crawler/stores+menus.py", keyword, str(store_limit)])
subprocess.run(["python", "crawler/reviews.py", keyword])

print("====== [2/4] 리뷰 전처리 및 JSON 생성 ======")
subprocess.run(["python", "preprocessing/reviews_to_clean.py"])
subprocess.run(["python", "preprocessing/stores_menus_to_json.py"])

print("====== [3/4] 리뷰 임베딩 및 ChromaDB 생성 ======")
subprocess.run(["python", "vectordb/embed_reviews.py"])

print("====== [4/4] Gradio 챗봇 실행 ======")
subprocess.run(["python", "chatbot/app.py"])
