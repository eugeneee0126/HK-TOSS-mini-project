import time
from playwright.sync_api import sync_playwright
import pandas as pd

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # 1. 카카오맵 접속
        page.goto('https://map.kakao.com/')
        print("✅ 카카오맵 접속 완료")

        # 2. 검색창에 "충정로역 맛집" 입력
        page.wait_for_selector('input#search\\.keyword\\.query')
        page.fill('input#search\\.keyword\\.query', '충정로역 맛집')
        page.keyboard.press('Enter')
        print("✅ 충정로역 맛집 검색 완료")

        # 3. 검색 결과 기다리기
        page.wait_for_selector('ul#info\\.search\\.place\\.list')

        # 4. dimmedLayer 닫기 (선택 사항)
        try:
            page.wait_for_selector('div#dimmedLayer', timeout=3000)
            page.click('div#dimmedLayer')
            print("✅ dimmedLayer 닫음")
        except:
            print("✅ dimmedLayer 없음")

        all_store_menu_data = []
        num_stores_to_crawl = 50
        crawled_stores_count = 0
        more_button_clicked = False

        while crawled_stores_count < num_stores_to_crawl:
            print(f"\n--- 현재까지 {crawled_stores_count}개 가게 크롤링 완료 ---")

            store_list_selector = 'ul#info\\.search\\.place\\.list li'
            page.wait_for_selector(store_list_selector)
            store_items = page.query_selector_all(store_list_selector)
            print(f"✅ 현재 페이지에 {len(store_items)}개의 가게 발견")

            for i, store_item in enumerate(store_items):
                if crawled_stores_count >= num_stores_to_crawl:
                    break

                store_index_on_page = i + 1
                print(f"\n--- {crawled_stores_count + 1}번째 가게 (현재 페이지 순번 {store_index_on_page}) 크롤링 시작 ---")
                new_page = None
                try:
                    more_view_button = store_item.query_selector('a.moreview')
                    if more_view_button:
                        with context.expect_page() as new_page_info:
                            more_view_button.click()
                        new_page = new_page_info.value
                        print("✅ 상세보기 페이지 열림")

                        new_page.wait_for_selector('h3.tit_place', timeout=10000)

                        try:
                            store_name_raw = new_page.inner_text('h3.tit_place')
                            store_name = store_name_raw.replace("장소명", "").strip()
                            print(f"🏢 가게 이름: {store_name}")

                            store_menu_data = []
                            menu_tab = new_page.query_selector('a[role="tab"]:has-text("메뉴")')
                            if menu_tab:
                                menu_tab.click()
                                new_page.wait_for_selector('ul.list_goods > li', timeout=10000)
                                menu_items = new_page.query_selector_all('ul.list_goods > li')
                                print("✅ 메뉴 탭 클릭 및 메뉴 정보 로딩 완료")

                                for item in menu_items:
                                    try:
                                        title_element = item.query_selector('strong.tit_item')
                                        price_element = item.query_selector('p.desc_item')

                                        title = title_element.inner_text().strip() if title_element else None
                                        price = price_element.inner_text().strip() if price_element else None

                                        if title:
                                            store_menu_data.append({'가게이름': store_name, '메뉴명': title, '가격': price})
                                    except Exception as e:
                                        print(f"⚠️ 메뉴 정보 추출 실패: {e}")
                            else:
                                print("⚠️ 메뉴 탭을 찾을 수 없습니다.")

                            all_store_menu_data.extend(store_menu_data)
                            crawled_stores_count += 1
                            if new_page and not new_page.is_closed():
                                new_page.close()

                        except Exception as e:
                            print(f"❌ 가게 정보 가져오기 실패: {e}")
                            if new_page and not new_page.is_closed():
                                new_page.close()
                    else:
                        print("⚠️ 상세보기 버튼을 찾을 수 없습니다.")

                except Exception as e:
                    print(f"❌ 가게 상세보기 페이지 이동 실패 (현재 페이지 순번 {store_index_on_page}): {e}")
                    if new_page and not new_page.is_closed():
                        new_page.close()

                if crawled_stores_count >= num_stores_to_crawl:
                    break

                time.sleep(1)  # 잠시 대기

            if crawled_stores_count < num_stores_to_crawl:
                if not more_button_clicked:
                    try:
                        more_button_selector = '#info\\.search\\.place\\.more'
                        page.wait_for_selector(more_button_selector, timeout=5000)
                        page.click(more_button_selector)
                        print("➡️ '장소 더보기' 버튼 클릭")
                        page.wait_for_selector('ul#info\\.search\\.place\\.list', timeout=10000)  # 다음 페이지 로딩 대기
                        time.sleep(2)  # 페이지 로딩 후 잠시 대기
                        more_button_clicked = True
                    except Exception as e:
                        print(f"⚠️ '장소 더보기' 버튼 없음 또는 클릭 실패: {e}")
                        # '장소 더보기' 버튼이 없으면 페이지 번호로 이동 시도
                        break
                else:
                    # 페이지 번호로 이동
                    try:
                        next_page_num = (crawled_stores_count // 15) + 2  # 다음 페이지 번호 계산 (15개씩 로드 가정)
                        next_page_selector = f'#info\\.search\\.page\\.no{next_page_num}'
                        page.wait_for_selector(next_page_selector, timeout=5000)
                        page.click(next_page_selector)
                        print(f"➡️ 페이지 {next_page_num} 클릭")
                        page.wait_for_selector('ul#info\\.search\\.place\\.list', timeout=10000)  # 다음 페이지 로딩 대기
                        time.sleep(2)  # 페이지 로딩 후 잠시 대기
                    except Exception as e:
                        print(f"⚠️ 페이지 {next_page_num} 버튼 없음 또는 클릭 실패: {e}")
                        break  # 더 이상 페이지 버튼이 없으면 종료

    

        # 9. 크롤링된 데이터를 DataFrame으로 변환 및 CSV 저장
        if all_store_menu_data:
            df = pd.DataFrame(all_store_menu_data)
            print("\n📊 크롤링된 전체 데이터프레임:")
            print(df)
            csv_filename = "chungjeongno_top50_restaurants_menu.csv"
            try:
                df.to_csv(csv_filename, encoding='utf-8-sig', index=False)
                print(f"\n💾 데이터를 '{csv_filename}'으로 저장했습니다.")
            except Exception as e:
                print(f"❌ CSV 파일 저장 실패: {e}")
        else:
            print("\n⚠️ 크롤링된 메뉴 데이터가 없습니다.")

if __name__ == "__main__":
    main()