# reviews.py
# Description: 'stores.csv'에서 가게 이름 목록을 불러와, 각 가게 이름으로 카카오맵 API를 호출해 place_id를 찾고,
#              해당 가게의 리뷰를 최대 50개까지 수집하여 'reviews.csv'로 저장하는 스크립트입니다.
# Author: 통합버전
# Date: 2025.04.29
# Requirements: requests, pandas


import requests
import pandas as pd
import time
import sys
import os

def search_place_id(store_name, rest_api_key):
    """가게 이름으로 place_id를 검색 (가장 일치율 높은 결과 1건)"""
    headers = {"Authorization": f"KakaoAK {rest_api_key}"}
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    params = {"query": store_name, "size": 1}

    response = requests.get(url, headers=headers, params=params, timeout=10)
    if response.status_code == 200:
        documents = response.json().get("documents", [])
        if documents:
            return documents[0]["id"]
    return None

def scrape_reviews_by_storelist(store_names, rest_api_key):
    COMMENT_URL = "https://place.map.kakao.com/m/commentlist/v/{}/{}?order=USEFUL&onlyPhotoComment=false"
    all_comment = []

    for idx, store_name in enumerate(store_names, 1):
        place_id = search_place_id(store_name, rest_api_key)
        if not place_id:
            print(f"❌ {store_name}의 place_id를 찾을 수 없습니다.")
            continue

        comment_id = 0
        has_next = True
        max_reviews = 50
        review_count = 0

        while has_next:
            try:
                scrap_url = COMMENT_URL.format(place_id, comment_id)
                response = requests.get(scrap_url, timeout=10)
                data = response.json()
            except Exception as e:
                print(f"⚠️ {store_name} 요청 실패: {e}")
                break

            if 'comment' not in data:
                print(f"⚠️ {store_name} 리뷰 없음, 스킵")
                break

            comment_datas = data['comment']
            comment_list = comment_datas.get('list', [])

            for comment in comment_list:
                content = comment.get('contents', '').strip()
                point = comment.get('point', None)

                if content:
                    all_comment.append({
                        '가게이름': store_name,
                        '리뷰내용': content,
                        '리뷰별점': point
                    })
                    review_count += 1
                    if review_count >= max_reviews:
                        has_next = False
                        break

            has_next = comment_datas.get('hasNext', False)
            if has_next and comment_list:
                comment_id = comment_list[-1]['commentid']
            else:
                has_next = False

        time.sleep(1)
        print(f"{store_name} ({idx}/{len(store_names)}) 완료! 1초 쉬어요 💤")

    return pd.DataFrame(all_comment)

def save_reviews_to_csv(final_df, filename):
    if final_df.empty:
        print("⚠️ 저장할 데이터가 없습니다.")
        return
    final_df = final_df.dropna(subset=['리뷰내용'])
    final_df = final_df[final_df['리뷰내용'].str.strip() != '']
    final_df = final_df.sort_values(by=['가게이름']).reset_index(drop=True)
    final_df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"✅ CSV 저장 완료: {filename}")

def main():
    if len(sys.argv) < 2:
        print("❌ 역 이름이 전달되지 않았습니다.")
        return

    REST_API_KEY = "668977541fc5a5fd5c0d271902df39c5"
    stores_csv_path = "data/stores.csv"

    if not os.path.exists(stores_csv_path):
        print("❌ stores.csv 파일이 존재하지 않습니다.")
        return

    store_df = pd.read_csv(stores_csv_path)
    store_names = store_df["store_name"].dropna().unique().tolist()

    print("📝 리뷰 크롤링 시작...")
    final_df = scrape_reviews_by_storelist(store_names, REST_API_KEY)

    save_reviews_to_csv(final_df, "data/reviews.csv")

if __name__ == "__main__":
    main()
