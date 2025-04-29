#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
카카오 맵 맛집 데이터 수집기
"""

import requests
import pandas as pd
import time
import os
import json
import re
from tqdm import tqdm
from bs4 import BeautifulSoup
from pathlib import Path

# 상대 경로 설정
CURRENT_DIR = Path(__file__).parent
DATA_DIR = CURRENT_DIR.parent / 'data'

# Kakao API 키
REST_API_KEY = "668977541fc5a5fd5c0d271902df39c5"

# API URL
KEYWORD_LOCAL_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

# API 요청 헤더
headers = {
    "Authorization": f"KakaoAK {REST_API_KEY}"
}

def get_user_input():
    """사용자 입력 받기"""
    print("\n===== 맛집 데이터 수집 설정 =====")
    
    # 지역 입력 받기
    locations_input = input("검색할 지역을 입력하세요 (쉼표로 구분): ")
    locations = [loc.strip() for loc in locations_input.split(',')]
    
    # 수집할 가게 수 입력 받기
    while True:
        try:
            max_stores = int(input("수집할 최대 가게 수를 입력하세요: "))
            if max_stores > 0:
                break
            else:
                print("1 이상의 숫자를 입력해주세요.")
        except ValueError:
            print("유효한 숫자를 입력해주세요.")
    
    return locations, max_stores

def get_stores_by_keyword(keyword, page=1, size=15):
    """키워드로 맛집 검색"""
    params = {
        "query": f"{keyword} 맛집",
        "page": page,
        "size": size,
        "radius": 1000,
        "sort": "accuracy"
    }
    
    try:
        response = requests.get(KEYWORD_LOCAL_URL, headers=headers, params=params)
        time.sleep(0.5)  # API 호출 제한 방지
        
        if response.status_code != 200:
            print(f"API 오류: {response.status_code}")
            return None
            
        return response.json()
    except Exception as e:
        print(f"API 요청 오류: {e}")
        return None

def scrape_place_details(place_id):
    """가게 상세 정보 스크래핑"""
    url = f"https://place.map.kakao.com/{place_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 이미지 URL 추출
        image_url = ""
        # 1. JSON에서 이미지 추출
        try:
            script_content = ""
            for script in soup.find_all("script"):
                if script.string and "PlaceItem" in str(script.string):
                    script_content = script.string
                    break
                    
            json_match = re.search(r'placeItem:\s*({.*?}),\s*relatedPlace', script_content, re.DOTALL)
            if json_match:
                json_data_str = json_match.group(1)
                json_data_str = re.sub(r'(\w+):', r'"\1":', json_data_str)
                json_data_str = re.sub(r',\s*}', '}', json_data_str)
                
                data = json.loads(json_data_str)
                if 'mainphotourl' in data:
                    image_url = data['mainphotourl']
        except Exception:
            pass
        
        # 2. 이미지 태그에서 추출
        if not image_url:
            try:
                img_tag = soup.select_one('.bg_present')
                if img_tag and 'style' in img_tag.attrs:
                    style = img_tag['style']
                    url_match = re.search(r'url\((.*?)\)', style)
                    if url_match:
                        image_url = url_match.group(1)
            except Exception:
                pass
        
        # 3. 대체 이미지 경로
        if not image_url:
            try:
                photo_viewer = soup.select_one('#photoViewer')
                if photo_viewer:
                    img_tags = photo_viewer.select('img')
                    for img in img_tags:
                        if 'src' in img.attrs:
                            image_url = img['src']
                            break
            except Exception:
                pass
        
        # 영업시간 추출
        operation_hours = "정보 없음"
        try:
            # 영업시간 추출 방법들
            hours_section = soup.select_one('.openhour_wrap')
            if hours_section:
                hours_tags = hours_section.select('.txt_operation')
                if hours_tags:
                    operation_hours = ' | '.join([tag.text.strip() for tag in hours_tags])
            
            if operation_hours == "정보 없음":
                hour_tags = soup.select('.fold_floor .list_operation .txt_operation')
                if hour_tags:
                    operation_hours = ' | '.join([tag.text.strip() for tag in hour_tags])
                    
            if operation_hours == "정보 없음":
                section = soup.select_one('.location_detail .location_present')
                if section:
                    for item in section.select('li'):
                        if '영업시간' in item.text:
                            operation_hours = item.text.replace('영업시간', '').strip()
                            break
        except Exception:
            pass
        
        # 주차 정보 추출
        parking = "정보 없음"
        try:
            # 주차 정보 추출 방법들
            facility_tags = soup.select('.fold_floor .list_facility')
            for tag in facility_tags:
                if '주차' in tag.text:
                    parking = tag.text.strip()
                    break
            
            if parking == "정보 없음":
                info_sections = soup.select('.place_section')
                for section in info_sections:
                    if section.select_one('.tit_parking'):
                        parking_info = section.select_one('.parking_wrap')
                        if parking_info:
                            parking = parking_info.text.strip()
                            break
            
            if parking == "정보 없음":
                basic_info = soup.select('.location_detail .location_present li')
                for info in basic_info:
                    if '주차' in info.text:
                        parking = info.text.strip()
                        break
        except Exception:
            pass
        
        return image_url, operation_hours, parking
        
    except Exception as e:
        print(f"상세 스크래핑 실패(ID: {place_id}): {e}")
        return "", "정보 없음", "정보 없음"

def extract_store_info(item, location):
    """가게 정보 추출"""
    place_name = item.get("place_name", "").strip()
    place_id = item.get("id", "").strip()
    
    print(f"수집 중: {place_name} (ID: {place_id})")
    
    # 상세 정보 스크래핑
    image_url, operation_hours, parking = scrape_place_details(place_id)
    
    # 주소 정보 처리
    road_address = item.get("road_address_name", "")
    address = item.get("address_name", "")
    location_info = road_address if road_address else address
    
    # 지역 정보 추출
    region = ""
    if road_address:
        region_parts = road_address.split()
        if len(region_parts) > 0:
            region = region_parts[0]
    elif address:
        region_parts = address.split()
        if len(region_parts) > 0:
            region = region_parts[0]
    
    if not region:
        region = location
    
    store_info = {
        "가게이름:[pk]": f"{place_name}:[{place_id}]",
        "가게사진": image_url,
        "위치 정보": location_info,
        "주차 여부": parking,
        "카테고리": item.get("category_name", ""),
        "영업시간": operation_hours,
        "전화번호": item.get("phone", ""),
        "지역": region,
        "#": place_id
    }
    
    return store_info

def main():
    """메인 함수"""
    # 사용자 입력 받기
    locations, max_stores = get_user_input()
    
    # 저장 폴더 만들기
    DATA_DIR.mkdir(exist_ok=True)
    
    # 저장할 리스트
    stores_data = []
    
    print("\n맛집 수집 시작...")
    total_collected = 0
    
    with tqdm(total=max_stores) as pbar:
        for location in locations:
            print(f"\n[{location}] 지역 검색 중...")
            
            # 첫 페이지 요청
            response_data = get_stores_by_keyword(location)
            if not response_data:
                continue
            
            stores = response_data.get("documents", [])
            
            # 첫 페이지 처리
            for store in stores:
                if total_collected >= max_stores:
                    break
                
                store_info = extract_store_info(store, location)
                
                # 중복 체크
                if not any(s.get("#") == store_info["#"] for s in stores_data):
                    stores_data.append(store_info)
                    total_collected += 1
                    pbar.update(1)
            
            # 추가 페이지 가져오기 (최대 3페이지)
            meta = response_data.get("meta", {})
            is_end = meta.get("is_end", True)
            current_page = 1
            
            while not is_end and current_page < 3 and total_collected < max_stores:
                current_page += 1
                print(f"  페이지 {current_page} 처리 중...")
                
                response_data = get_stores_by_keyword(location, page=current_page)
                if not response_data:
                    break
                
                stores = response_data.get("documents", [])
                for store in stores:
                    if total_collected >= max_stores:
                        break
                    
                    store_info = extract_store_info(store, location)
                    
                    if not any(s.get("#") == store_info["#"] for s in stores_data):
                        stores_data.append(store_info)
                        total_collected += 1
                        pbar.update(1)
                
                meta = response_data.get("meta", {})
                is_end = meta.get("is_end", True)
            
            if total_collected >= max_stores:
                break
    
    # DataFrame 저장
    stores_df = pd.DataFrame(stores_data)
    
    # 컬럼 순서 지정
    columns_order = [
        "가게이름:[pk]", "가게사진", "위치 정보", "주차 여부", 
        "카테고리", "영업시간", "전화번호", "지역", "#"
    ]
    
    # 존재하는 컬럼만 선택
    available_columns = [col for col in columns_order if col in stores_df.columns]
    stores_df = stores_df[available_columns]
    
    # CSV로 저장
    csv_path = DATA_DIR / "stores.csv"
    stores_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    print(f"\n✅ 총 {len(stores_df)}개 가게 수집 완료!")
    print(f"파일 저장: {csv_path}")
    
    # 수집된 데이터 미리보기
    print("\n=== 수집된 데이터 미리보기 ===")
    print(stores_df.head())
    
    return stores_df

if __name__ == "__main__":
    main()