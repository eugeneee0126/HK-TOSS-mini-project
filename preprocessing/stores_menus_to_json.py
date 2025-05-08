# 파일: preprocessing/stores_menus_to_json.py
# Description: 크롤링한 가게 정보(stores.csv)와 메뉴 정보(menus.csv)를 통합하여 store_info.json 파일로 변환하는 전처리 스크립트
# Author: 통합버전
# Date: 2025.04.29
# Requirements: pandas, json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 상위 폴더 경로 추가


import json
import pandas as pd
from config import STORES_CSV, MENUS_CSV, STORE_INFO_JSON

def load_and_prepare_store_info(store_path: str, menu_path: str) -> list:
    """CSV 경로를 받아 store_info_json 형태로 변환"""
    stores_df = pd.read_csv(store_path).fillna("")
    menus_df = pd.read_csv(menu_path).fillna("")

    merged_df = pd.merge(menus_df, stores_df, on="store_id", how="left")
    grouped = merged_df.groupby("store_id")

    result = []
    for store_id, group in grouped:
        store_info = {
            "store_id": store_id,
            "store_name": group["store_name"].iloc[0],
            "address": group["address"].iloc[0],
            "phone": group["phone"].iloc[0],
            "openhours": group["openhours"].iloc[0],
            "categories": group["categories"].iloc[0],
            "facilities": group["facilities"].iloc[0],
            "hashtags": group["hashtags"].iloc[0],
            "main_image_url": group["main_image_url"].iloc[0],
            "menus": []
        }

        for _, row in group.iterrows():
            store_info["menus"].append({
                "menu_name": row["menu_name"],
                "price": row["price"],
                "description": row["description"],
                "image_url": row["image_url"]
            })

        result.append(store_info)

    print("[INFO] store_info_json 생성 완료")
    return result


if __name__ == "__main__":
    store_info_json = load_and_prepare_store_info(STORES_CSV, MENUS_CSV)

    with open(STORE_INFO_JSON, "w", encoding="utf-8") as f:
        json.dump(store_info_json, f, ensure_ascii=False, indent=2)

    print(f"[INFO] store_info.json 저장 완료: {STORE_INFO_JSON}")
