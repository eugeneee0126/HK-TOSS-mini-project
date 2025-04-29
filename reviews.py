import requests
import pandas as pd
import time

def search_places(keyword, rest_api_key, radius=1000, max_pages=4):
    headers = {"Authorization": f"KakaoAK {rest_api_key}"}
    search_url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    datas = []

    search_word = keyword + " 맛집"

    for page in range(1, max_pages + 1):
        params = {
            "query": search_word,
            "radius": radius,
            "page": page
        }
        response = requests.get(search_url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            documents = response.json().get('documents', [])
            datas.extend(documents)
        else:
            print(f"⚠️ 검색 실패 (page {page}): {response.status_code}")
            break

    id_place_list = [{'id': data['id'], 'placename': data['place_name']} for data in datas]
    return id_place_list

def scrape_reviews(id_place_list):
    COMMENT_URL = "https://place.map.kakao.com/m/commentlist/v/{}/{}?order=USEFUL&onlyPhotoComment=false"
    all_comment = []

    for idx, id_with_placename in enumerate(id_place_list, 1):
        place_name = id_with_placename['placename']
        place_id = id_with_placename['id']
        comment_id = 0
        has_next = True

        while has_next:
            try:
                scrap_url = COMMENT_URL.format(place_id, comment_id)
                response = requests.get(scrap_url, timeout=15)
                json_response = response.json()
            except Exception as e:
                print(f"⚠️ {place_name} 요청 실패: {e}")
                break

            if 'comment' not in json_response:
                print(f"⚠️ {place_name} 리뷰 없음, 스킵")
                break

            comment_datas = json_response['comment']
            comment_list = comment_datas.get('list', [])

            for comment in comment_list:
                content = comment.get('contents', '').strip()
                point = comment.get('point', None)

                if content:  # 빈 문자열 거르기
                    all_comment.append({
                        '가게이름': place_name,
                        '리뷰내용': content,
                        '리뷰별점': point
                    })

            has_next = comment_datas.get('hasNext', False)
            if has_next and comment_list:
                comment_id = comment_list[-1]['commentid']
            else:
                has_next = False

        time.sleep(1)
        print(f"{place_name} ({idx}/{len(id_place_list)}) 완료! 1초 쉬어요 💤")

    df = pd.DataFrame(all_comment)
    return df

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
    REST_API_KEY = "668977541fc5a5fd5c0d271902df39c5"
    keyword = input("역 이름을 입력하세요 (예: 충정로역): ").strip()

    print("🔎 가게 검색 중...")
    id_place_list = search_places(keyword, REST_API_KEY)

    print("📝 리뷰 크롤링 시작...")
    final_df = scrape_reviews(id_place_list)

    output_filename = f"{keyword}_리뷰데이터.csv"
    save_reviews_to_csv(final_df, output_filename)

if __name__ == "__main__":
    main()