import requests
import pandas as pd
import time

import requests

def search_places(keywords, rest_api_key, radius=1000, max_pages=3):
    """
    키워드 리스트를 받아서, 가게 id와 가게 이름 리스트를 수집하는 함수
    """
    headers = {"Authorization": f"KakaoAK {rest_api_key}"}
    search_url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    
    datas = []

    # 첫 번째 키워드만 사용
    search_word = keywords[0] + " 맛집"

    for page in range(1, max_pages + 1):
        params = {
            "query": search_word,
            "radius": radius,
            "page": page
        }
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            documents = response.json().get('documents', [])
            datas.extend(documents)
        else:
            print(f"⚠️ 검색 실패 (page {page}): {response.status_code}")
            break

    # 여기서 datas를 id_place_list로 변환해줘야 해!!!
    id_place_list = [{'id': data['id'], 'placename': data['place_name']} for data in datas]

    return id_place_list


def scrape_reviews(id_place_list):
    """
    가게 id 리스트를 받아 리뷰를 수집하는 함수
    """
    COMMENT_URL = "https://place.map.kakao.com/m/commentlist/v/{}/{}?order=USEFUL&onlyPhotoComment=false"
    all_comment_df_list = []
    total_places = len(id_place_list)

    for idx, id_with_placename in enumerate(id_place_list, 1):
        all_comment = []
        comment_id = 0
        has_next = True

        while has_next:
            try:
                scrap_url = COMMENT_URL.format(id_with_placename['id'], comment_id)
                response = requests.get(scrap_url, timeout=10)
                json_response = response.json()
            except Exception as e:
                print(f"⚠️ {id_with_placename['placename']} 요청 실패: {e}")
                break

            if 'comment' not in json_response:
                print(f"⚠️ {id_with_placename['placename']} 리뷰 없음, 스킵")
                break

            comment_datas = json_response['comment']
            comment_list = comment_datas.get('list', [])

            for comment in comment_list:
                all_comment.append({
                    '가게이름': id_with_placename['placename'],
                    '리뷰내용': comment.get('contents', '').strip(),
                    '리뷰별점': comment.get('point', None)
                })

            has_next = comment_datas.get('hasNext', False)
            if has_next and comment_list:
                comment_id = comment_list[-1]['commentid']
            else:
                has_next = False

        if all_comment:
            df = pd.DataFrame(all_comment)
            all_comment_df_list.append(df)

        time.sleep(1)
        print(f"가게 {total_places}개 중 {idx}번째 완료! 1초 쉽니당 💤")

    if all_comment_df_list:
        return pd.concat(all_comment_df_list, ignore_index=True)
    else:
        return pd.DataFrame(columns=["가게이름", "리뷰내용", "리뷰별점"])

def save_reviews_to_csv(final_df, filename):
    """
    최종 리뷰 데이터프레임을 CSV 파일로 저장하는 함수
    """
    final_df = final_df[final_df['리뷰내용'].str.strip() != '']
    final_df = final_df.dropna(subset=['리뷰내용'])
    final_df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"✅ CSV 저장 완료: {filename}")

def main():
    REST_API_KEY = "668977541fc5a5fd5c0d271902df39c5"
    keyword = input("역 이름을 입력하세요 (예: 충정로역): ")

    print("🔎 가게 검색 중...")
    id_place_list = search_places(keyword, REST_API_KEY)

    print("📝 리뷰 크롤링 시작...")
    final_df = scrape_reviews(id_place_list)

    output_filename = f"{keyword}_리뷰데이터.csv"
    save_reviews_to_csv(final_df, output_filename)

if __name__ == "__main__":
    main()
