# stores+menus.py
# Description: 카카오맵 웹사이트에서 검색 키워드(예: 충정로역 맛집)를 기반으로 가게 정보를 크롤링합니다.
#              - 장소 더보기 버튼과 페이지 넘김 로직을 통해 최대 200개까지 가게 정보를 수집하며,
#              - 각 가게에 대해 기본 정보, 영업시간, 편의시설, 해시태그, 카테고리, 대표 이미지, 메뉴 정보를 포함합니다.
#              - 크롤링된 결과는 'stores.csv'와 'menus.csv'로 저장됩니다.
# Author: 통합버전
# Date: 2025.04.29
# Requirements: playwright, pandas


import time
import pandas as pd
from playwright.sync_api import sync_playwright
import sys

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # 1. 카카오맵 접속
        page.goto('https://map.kakao.com/')
        page.wait_for_selector('input#search\\.keyword\\.query')
        
        # 2. 검색어 입력
        if len(sys.argv) < 2:
            print("❌ 역 이름이 전달되지 않았습니다.")
            return

        keyword = sys.argv[1]
        
        # 2-1. 크롤링할 가게 수 입력 받기
        if len(sys.argv) < 3:
            print("❌ 크롤링할 가게 수가 전달되지 않았습니다.")
            return

        try:
            input_store_count = int(sys.argv[2])
            if input_store_count <= 0:
                print("❌ 1개 이상의 양수를 입력해야 합니다.")
                return
            elif input_store_count > 200:
                print("⚠️ 최대 35개까지만 크롤링할 수 있습니다. 200개로 제한합니다.")
                max_store_id = 200
            else:
                max_store_id = input_store_count
        except ValueError:
            print("❌ 유효한 숫자를 입력해주세요.")
            return

        search_keyword = f"{keyword} 맛집"
        page.fill('input#search\\.keyword\\.query', search_keyword)
        page.keyboard.press('Enter')
        page.wait_for_selector('ul#info\\.search\\.place\\.list')
        print(f"✅ {search_keyword} 검색 완료")
        
        # 3. dimmedLayer 닫기 (선택 사항)
        try:
            page.wait_for_selector('div#dimmedLayer', timeout=3000)
            page.click('div#dimmedLayer')
            print("✅ dimmedLayer 클릭해서 닫음")
        except:
            print("✅ dimmedLayer 없음")
        
        # 데이터 저장용 리스트
        stores_data = []
        menus_data = []
        store_id = 1                # 가게 고유 번호
        more_button_clicked = False # 장소 더보기 버튼 클릭 여부
        current_page = 1    # 현재 페이지 번호
        crawled_stores_count = 0 # 크롤링 완료한 가게 수
        
        while crawled_stores_count < max_store_id:
            print(f"\n--- 현재까지 {crawled_stores_count}개 가게 크롤링 완료 (현재 페이지: {current_page}) ---")
            
            # 현재 페이지의 모든 가게 목록 가져오기
            page.wait_for_selector('ul#info\\.search\\.place\\.list li')
            store_items = page.query_selector_all('ul#info\\.search\\.place\\.list li')
            print(f"✅ 현재 페이지에 {len(store_items)}개의 가게 발견")
            
            # 현재 페이지의 각 가게 크롤링
            for i, store_item in enumerate(store_items):
                if crawled_stores_count >= max_store_id:
                    break
                    
                store_index_on_page = i + 1
                print(f"\n--- {crawled_stores_count + 1}번째 가게 (현재 페이지 순번 {store_index_on_page}) 크롤링 시작 ---")
                
                new_page = None
                try:
                    # 상세보기 링크 클릭
                    more_view_button = store_item.query_selector('a.moreview')
                    if more_view_button:
                        with context.expect_page() as new_page_info:
                            more_view_button.click()
                        new_page = new_page_info.value
                        print("✅ 상세보기 페이지 열림")
                        
                        # 상세 페이지 로딩 대기
                        new_page.wait_for_selector('h3.tit_place', timeout=10000)
                        
                        # 가게 이름
                        try:
                            store_name_raw = new_page.inner_text('h3.tit_place')
                            store_name = store_name_raw.replace("장소명", "").strip()
                            print(f"🏢 가게 이름: {store_name}")
                        except:
                            store_name = None
                            print("❌ 가게 이름 추출 실패")
                            
                        # 가게 주소
                        try:
                            address = new_page.inner_text('div.row_detail span.txt_detail')
                            print(f"📍 주소: {address}")
                        except:
                            address = None
                            print("❌ 주소 추출 실패")
                            
                        # 전화번호
                        try:
                            phone = new_page.inner_text('div.detail_info.info_suggest span.txt_detail')
                            print(f"☎️ 전화번호: {phone}")
                        except:
                            phone = None
                            print("❌ 전화번호 추출 실패")
                            
                        # 영업시간
                        openhours = {}
                        try:
                            elements = new_page.query_selector_all('div#foldDetail2 div.line_fold')
                            for elem in elements:
                                day_span = elem.query_selector('span.tit_fold')
                                if not day_span:
                                    continue
                                    
                                day = day_span.inner_text().strip()
                                open_info = {'영업시간': None, '라스트오더': None, '브레이크타임': None}
                                
                                detail_fold = elem.query_selector('div.detail_fold')
                                if detail_fold:
                                    details = detail_fold.query_selector_all('span.txt_detail')
                                    for idx2, detail in enumerate(details):
                                        text = detail.inner_text().strip()
                                        if idx2 == 0:
                                            open_info['영업시간'] = text
                                        else:
                                            if '라스트오더' in text:
                                                open_info['라스트오더'] = text.replace('라스트오더', '').replace('~', '').strip()
                                            elif '브레이크타임' in text:
                                                open_info['브레이크타임'] = text.replace('브레이크타임', '').strip()
                                else:
                                    open_info['영업시간'] = '정보 없음'
                                    
                                openhours[day] = open_info
                            print(f"🕒 영업시간 정보 추출 완료")
                        except:
                            openhours = {}
                            print("❌ 영업시간 정보 추출 실패")
                            
                        # 부가정보, 해시태그, 카테고리
                        facilities, hashtags, categories, main_image_url = [], [], [], None
                        
                        try:
                            # 정보 탭 클릭
                            info_tab = new_page.query_selector('a.link_tab[role="tab"]:has-text("정보")')
                            if info_tab:
                                info_tab.click()
                                new_page.wait_for_selector('div.default_info.type_descinfo', timeout=3000)
                                print("✅ 정보 탭 클릭 완료")
                        except:
                            print("❌ 정보 탭 클릭 실패")
                            
                        # 시설정보
                        try:
                            unit_defaults = new_page.query_selector_all('div.unit_default')
                            for unit in unit_defaults:
                                title = unit.query_selector('span.ico_mapdesc.ico_facilities')
                                if title:
                                    detail_area = unit.query_selector('div.row_detail.aligntype_gap')
                                    if detail_area:
                                        badges = detail_area.query_selector_all('span.badge_label')
                                        facilities = [badge.inner_text().strip() for badge in badges]
                                    break
                            print(f"🏢 시설정보: {facilities}")
                        except:
                            print("❌ 시설정보 추출 실패")
                            
                        # 해시태그
                        try:
                            for unit in unit_defaults:
                                title = unit.query_selector('span.ico_mapdesc.ico_hashtag')
                                if title:
                                    detail_area = unit.query_selector('div.row_detail')
                                    if detail_area:
                                        tags = detail_area.query_selector_all('a.txt_detail')
                                        hashtags = [tag.inner_text().strip() for tag in tags]
                                    break
                            print(f"# 해시태그: {hashtags}")
                        except:
                            print("❌ 해시태그 추출 실패")
                            
                        # 카테고리
                        try:
                            category_span = new_page.query_selector('span.info_cate')
                            if category_span:
                                screen_out_span = category_span.query_selector('span.screen_out')
                                screen_out_text = screen_out_span.inner_text().strip() if screen_out_span else ''
                                full_text = category_span.inner_text().strip()
                                category_text = full_text.replace(screen_out_text, '').strip()
                                if category_text:
                                    categories = [cat.strip() for cat in category_text.split(',')]
                            print(f"🏷️ 카테고리: {categories}")
                        except:
                            print("❌ 카테고리 추출 실패")
                            
                        # 대표 사진
                        try:
                            photo_tab = new_page.query_selector('a[role="tab"]:has-text("사진")')
                            if photo_tab:
                                photo_tab.click()
                                new_page.wait_for_timeout(2000)
                                print("✅ 사진 탭 클릭 완료")
                                
                            first_photo = new_page.query_selector('div.view_photolist ul.list_photo li a img')
                            if first_photo:
                                src = first_photo.get_attribute('src')
                                if src:
                                    main_image_url = src
                                    print(f"🖼️ 대표 사진 URL 추출 완료")
                        except:
                            print("❌ 대표 사진 추출 실패")
                            
                        # 메뉴
                        store_menu_data = []
                        try:
                            menu_tab = new_page.query_selector('a[role="tab"]:has-text("메뉴")')
                            if menu_tab:
                                menu_tab.click()
                                new_page.wait_for_timeout(2000)
                                print("✅ 메뉴 탭 클릭 완료")
                                
                            menu_items = new_page.query_selector_all('ul.list_goods > li')
                            for item in menu_items:
                                img_tag = item.query_selector('a.link_thumb img')
                                image_url = img_tag.get_attribute('src') if img_tag else None
                                
                                title_tag = item.query_selector('strong.tit_item')
                                title = title_tag.inner_text().strip() if title_tag else None
                                
                                price_tag = item.query_selector('p.desc_item')
                                price = price_tag.inner_text().strip() if price_tag else None
                                
                                desc_tag = item.query_selector('p.desc_item2')
                                description = desc_tag.inner_text().strip() if desc_tag else None
                                
                                menus_data.append({
                                    'store_id': store_id,
                                    'menu_name': title,
                                    'price': price,
                                    'description': description,
                                    'image_url': image_url
                                })
                                
                                # 두 번째 코드의 형식에 맞게 데이터도 추가
                                store_menu_data.append({
                                    '가게이름': store_name,
                                    '메뉴명': title,
                                    '가격': price
                                })
                                
                            print(f"🍽️ {len(store_menu_data)}개 메뉴 정보 추출 완료")
                        except:
                            print("❌ 메뉴 추출 실패")
                            
                        # 가게 데이터 저장
                        stores_data.append({
                            'store_id': store_id,
                            'store_name': store_name,
                            'address': address,
                            'phone': phone,
                            'openhours': openhours,
                            'facilities': facilities,
                            'hashtags': hashtags,
                            'categories': categories,
                            'main_image_url': main_image_url
                        })
                        
                        store_id += 1
                        crawled_stores_count += 1
                        
                        # 새 페이지 닫기
                        new_page.close()
                        print(f"✅ {crawled_stores_count}번째 가게 크롤링 완료")
                        
                    else:
                        print("⚠️ 상세보기 버튼을 찾을 수 없습니다.")
                        
                except Exception as e:
                    print(f"❌ 가게 크롤링 실패: {e}")
                    if new_page and not new_page.is_closed():
                        new_page.close()
                
                # 잠시 대기
                time.sleep(1)
            
            # 모든 가게를 크롤링했으면 종료
            if crawled_stores_count >= max_store_id:
                break
                
            # 페이징 처리
            # 3페이지까지는 첫번째 로직, 그 이후는 두번째 로직 사용
            if current_page < 3:
                # 첫번째 로직
                if not more_button_clicked:
                    try:
                        more_button_selector = '#info\\.search\\.place\\.more'
                        page.wait_for_selector(more_button_selector, timeout=5000)
                        page.click(more_button_selector)
                        print("➡️ '장소 더보기' 버튼 클릭")
                        page.wait_for_selector('ul#info\\.search\\.place\\.list', timeout=10000)
                        time.sleep(2)
                        more_button_clicked = True
                        current_page = 2
                    except Exception as e:
                        print(f"⚠️ '장소 더보기' 버튼 없음 또는 클릭 실패: {e}")
                        break
                else:
                    current_page += 1
                    try:
                        next_page_selector = f'#info\\.search\\.page\\.no{current_page}'
                        page.wait_for_selector(next_page_selector, timeout=5000)
                        page.click(next_page_selector)
                        print(f"➡️ 페이지 {current_page} 클릭 (첫번째 로직)")
                        page.wait_for_selector('ul#info\\.search\\.place\\.list', timeout=10000)
                        time.sleep(2)
                    except Exception as e:
                        print(f"⚠️ {current_page} 페이지 버튼 없음 또는 클릭 실패: {e}")
                        break
            else:
                current_page += 1
                try:
                    next_page_selector = f'#info\\.search\\.page\\.no{current_page}'
                    next_button = page.locator(next_page_selector)
                    if next_button.is_visible():
                        next_button.click()
                        print(f"➡️ 페이지 {current_page} 클릭 성공")
                        page.wait_for_selector('ul#info\\.search\\.place\\.list', timeout=10000)
                        time.sleep(2)
                    else:
                        raise Exception("다음 페이지 버튼이 숨겨져 있음")
                except Exception as e:
                    print(f"⚠️ 페이지 {current_page} 버튼 실패: {e}")
                    # '다음' 버튼 시도
                    try:
                        next_btn_selector = '#info\\.search\\.page\\.next'
                        page.click(next_btn_selector)
                        print("➡️ '다음' 버튼 클릭")
                        page.wait_for_selector('ul#info\\.search\\.place\\.list', timeout=10000)
                        time.sleep(2)
                        current_page = 1  # 다음 버튼 누른 후 페이지 번호 초기화
                    except Exception as e2:
                        print(f"❌ '다음' 버튼도 실패: {e2}")
                        break

        
        # 크롤링 완료 - 데이터 저장
        print("\n--- 크롤링 완료 ---")
        print(f"총 {crawled_stores_count}개 가게 크롤링 성공")
        
        # 저장 파일명
        stores_csv = "data/stores.csv"
        menus_csv = "data/menus.csv"
        
        # 저장
        try:
            pd.DataFrame(stores_data).to_csv(stores_csv, encoding='utf-8-sig', index=False)
            print(f"💾 가게 정보를 '{stores_csv}'로 저장했습니다.")
            
            pd.DataFrame(menus_data).to_csv(menus_csv, encoding='utf-8-sig', index=False)
            print(f"💾 메뉴 정보를 '{menus_csv}'로 저장했습니다.")
        except Exception as e:
            print(f"❌ CSV 파일 저장 실패: {e}")
        
        # 브라우저 닫기
        browser.close()

if __name__ == "__main__":
    main()

# 터미널에서 python kakao_search.py 으로 실행. or Run 파일 눌러서 실행.
# 이 파일이 있는 위치에서 실행해주세요.
