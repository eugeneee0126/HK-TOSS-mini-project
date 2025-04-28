# 🍽️ 맛집 탐험대 챗봇 프로젝트 🍽️
당신의 미식 여정을 위한 스마트 가이드, 맛집 탐험대 챗봇!

키오스크 환경에서 사용자의 음성 또는 텍스트 입력을 통해 쉽고 빠르게 원하는 맛집 정보를 제공하는 챗봇 프로젝트입니다. 
특히 디지털 기기에 익숙하지 않은 사용자층을 고려하여 직관적이고 편리한 사용 경험을 목표로 합니다.

## 🌟 1. 프로젝트 개요
### 목표: 
텍스트 기반 맛집 검색을 지원하여 모든 사용자가 편리하게 주변 맛집 정보를 얻을 수 있도록 합니다.
### 주요 기능:
텍스트 검색: 지도api 활용해 위치 기반 맛집 정보 수집
다양한 검색 조건: 지역, 음식 종류, 분위기, 가격대 등 상세 검색 지원
상세 정보 제공: 맛집 이름, 종류, 평점, 설명, 주소, 연락처, 메뉴, 리뷰 등 풍부한 정보 제공

## 🧑‍💻 2. 참여자
- [🔗](https://github.com/)오은수
- [🔗](https://github.com/)윤태원
- [🔗](https://github.com/)최민주

## 🛠️ 3. 개발 프로세스
본 프로젝트는 효율적인 협업과 체계적인 개발을 위해 Gitflow 워크플로우를 기반으로 진행됩니다.

```bash
# 1 최신 develop 브랜치 동기화
git checkout develop
git pull origin develop

# 2 새로운 기능 브랜치 생성
git checkout -b <feature_branch>

# 3 작업 후 변경 사항 저장
git add .
git commit -m "커밋 메시지"

# 4 develop 브랜치 병합 (충돌 확인 필수)
git checkout develop
git pull origin develop
git merge <feature_branch>

# 5 원격 저장소 반영
git push origin develop
```
