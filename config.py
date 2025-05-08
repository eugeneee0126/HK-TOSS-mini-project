# config.py
# Description: 프로젝트 전역에서 사용할 주요 파일 경로 및 설정 상수를 정의한 설정 파일

import os

# 현재 프로젝트 루트 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 데이터 디렉토리
DATA_DIR = os.path.join(BASE_DIR, "data")

# 각 파일 경로
STORES_CSV = os.path.join(DATA_DIR, "stores.csv")
MENUS_CSV = os.path.join(DATA_DIR, "menus.csv")
REVIEWS_CSV = os.path.join(DATA_DIR, "reviews.csv")
REVIEW_FINAL_CSV = os.path.join(DATA_DIR, "reviews_final.csv")
STORE_INFO_JSON = os.path.join(DATA_DIR, "store_info.json")

# 벡터 DB 경로
CHROMA_DB_DIR = os.path.join(BASE_DIR, "vectordb", "chroma_reviews")
