# 충정로역 맛집 추천 챗봇 🍜🤖

서울 충정로역 주변의 음식점 데이터를 기반으로, 메뉴/주소/시설/분위기 등 다양한 정보를 질문할 수 있는 **Function Calling + RAG 기반 Gradio 챗봇**입니다.

---

## 📌 기능 요약

- ✅ 메뉴, 주소, 전화번호, 영업시간, 리뷰 등 정보를 자연스럽게 응답
- ✅ 리뷰 데이터 기반 유사도 검색 (RAG 구조)
- ✅ Function Calling 기반 툴 호출
- ✅ Gradio 인터페이스 제공
- ✅ 크롤링 → 전처리 → 벡터DB 생성 → 챗봇 실행까지 파이프라인 자동화

---

## 설치 및 실행 방법

```bash
# 1. 레포 클론
git clone [레포주소]
cd HK_TOSS_mini_project

# 2. 가상환경 설치 및 의존성 설치
conda activate hktoss   # 또는 python venv
pip install -r requirements.txt

# 3. .env 파일 생성
touch .env
# .env 안에 아래 내용 추가
OPENAI_API_KEY="sk-..."

# 4. 전체 파이프라인 실행 (크롤링 제외)
python run_pipeline.py
```
🔐 주의사항
- .env, reviews_final.csv, store_info.json, chroma_reviews/는 .gitignore에 포함되어 있습니다.

- 로컬에서 .env 파일과 raw CSV 파일만 있으면 전체 파이프라인을 실행할 수 있습니다.
---

## 폴더 구조

```
HK_TOSS_mini_project/
│
├── chatbot/                     # 챗봇 UI 및 체인 로직
│   ├── app.py                   # Gradio 앱 실행
│   ├── main_chain.py            # GPT + Function Calling + RAG
│   └── tools.py                 # 각종 툴 함수 및 스키마
│
├── crawler/
│   └── kakao_crawling.py        # (옵션) 카카오맵 크롤러
│
├── data/                        # 데이터 파일들
│   ├── menus.csv
│   ├── reviews.csv
│   ├── stores.csv
│   ├── reviews_final.csv        # 전처리된 리뷰
│   └── store_info.json          # 메뉴+가게 통합 json
│
├── preprocessing/
│   ├── reviews_to_clean.py      # 리뷰 전처리
│   └── stores_menus_to_json.py  # 메뉴+가게 json 생성
│
├── vectordb/
│   ├── embed_reviews.py         # 리뷰 임베딩 및 저장
│   ├── load_retriever.py        # Vector DB 로딩 함수
│   └── chroma_reviews/          # ChromaDB 저장 디렉토리
│
├── config.py                    # 전체 경로 설정 모듈
├── run_pipeline.py              # 전체 파이프라인 실행 스크립트
├── requirements.txt
└── .env                         # (gitignore 대상) OpenAI API Key 포함

```
---

## 전체 실행 흐름
```
CSV 불러오기
  ↓
리뷰 전처리 및 감성 분류 (reviews_to_clean.py)
  ↓
가게 + 메뉴 통합 JSON 생성 (stores_menus_to_json.py)
  ↓
리뷰 벡터 임베딩 + ChromaDB 저장 (embed_reviews.py)
  ↓
챗봇 실행 (Function Calling + RAG) (app.py)

```
---
```
---

## 🧩 사용 기술 스택

| 기술             | 설명                                      |
|------------------|-------------------------------------------|
| Python           | 메인 언어                                 |
| LangChain        | LLM 연결 및 툴/체인 구성                  |
| OpenAI GPT-4o    | LLM 기반 응답 생성                         |
| HuggingFace      | BAAI/bge-m3 임베딩 모델 사용              |
| ChromaDB         | 벡터 검색용 DB                             |
| Gradio           | 프론트엔드 챗봇 UI                         |
| Playwright       | 카카오맵 크롤링 자동화                    |
| dotenv           | 환경변수 관리                             |
| pandas / numpy   | 데이터 처리 및 정제                       |

---

## 📝 참고

- `run_pipeline.py`를 통해 전체 파이프라인이 자동 실행됩니다.  
- `.env` 파일은 반드시 프로젝트 루트에 위치해야 합니다.  
- `store_info.json`, `reviews_final.csv`, `chroma_reviews/`는 파이프라인 실행 시 자동 생성됩니다.
