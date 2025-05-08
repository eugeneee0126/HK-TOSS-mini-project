# 파일: chatbot/tools.py
# Description: store_info.json 기반으로 가게 이름으로부터 메뉴, 주소, 영업시간, 전화번호, 편의시설, 음식 종류, 해시태그를 반환하는 Function Calling 유틸리티 함수 및 OpenAI Tool 스키마 정의
# Author: 통합버전
# Date: 2025.04.29
# Requirements: json, ast, langchain, store_info.json

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 상위 폴더 경로 추가

import os
import json
from typing import List
from ast import literal_eval
from langchain.tools import tool

# ----------------------------
# 1. 데이터 로드
# ----------------------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STORE_JSON_PATH = os.path.join(BASE_DIR, "data", "store_info.json")

with open(STORE_JSON_PATH, "r", encoding="utf-8") as f:
    store_info_json = json.load(f)

# ----------------------------
# 2. 공통 유틸 함수
# ----------------------------

def normalize(text: str) -> str:
    return text.replace(" ", "").lower().strip()

def find_store(store_name: str):
    query = normalize(store_name)
    for store in store_info_json:
        name = normalize(store["store_name"])
        if query in name or name in query:
            return store
    return None

# ----------------------------
# 3. Function Calling 함수들
# ----------------------------

def get_menu_by_store_name(store_name: str) -> str:
    store = find_store(store_name)
    if not store:
        return "해당 가게를 찾을 수 없습니다."

    menus = store.get("menus", [])
    if not menus:
        return "해당 가게의 메뉴 정보가 없습니다."

    return "\n".join([
        f"{m.get('menu_name', '메뉴명 없음')} ({m.get('price', '가격 정보 없음')})"
        for m in menus
    ])

def get_address_by_store_name(store_name: str) -> str:
    store = find_store(store_name)
    if not store:
        return "해당 가게를 찾을 수 없습니다."

    address = store.get("address", "").strip()
    return (
        f"{store['store_name']}의 주소는 다음과 같습니다: {address}"
        if address else f"{store['store_name']}의 주소 정보는 등록되어 있지 않습니다."
    )

def get_openhours_by_store_name(store_name: str) -> str:
    store = find_store(store_name)
    if not store:
        return "해당 가게를 찾을 수 없습니다."

    openhours = store.get("openhours", "").strip()
    return (
        f"{store['store_name']}의 영업시간은 {openhours}입니다."
        if openhours else f"{store['store_name']}의 영업시간 정보는 등록되어 있지 않습니다."
    )

def get_phone_by_store_name(store_name: str) -> str:
    store = find_store(store_name)
    if not store:
        return "해당 가게를 찾을 수 없습니다."

    phone = store.get("phone", "").strip()
    return (
        f"{store['store_name']}의 전화번호는 {phone}입니다."
        if phone else f"{store['store_name']}의 전화번호 정보는 등록되어 있지 않습니다."
    )

def get_facilities_by_store_name(store_name: str) -> str:
    store = find_store(store_name)
    if not store:
        return "해당 가게를 찾을 수 없습니다."

    raw = store.get("facilities", "")
    if not raw or raw in ("[]", "", None):
        return f"{store['store_name']}의 시설 정보는 등록되어 있지 않습니다."

    try:
        facilities = literal_eval(raw)
        if isinstance(facilities, list) and facilities:
            return f"{store['store_name']}에서는 다음 시설들을 이용할 수 있어요: {', '.join(facilities)}"
    except:
        return f"{store['store_name']}의 시설 정보 형식이 올바르지 않아 제공이 어렵습니다."

    return f"{store['store_name']}의 시설 정보는 등록되어 있지 않습니다."

def get_categories_by_store_name(store_name: str) -> str:
    store = find_store(store_name)
    if not store:
        return "해당 가게를 찾을 수 없습니다."

    raw = store.get("categories", "")
    if not raw or raw in ("[]", "", None):
        return f"{store['store_name']}의 음식 종류 정보는 등록되어 있지 않습니다."

    try:
        categories = literal_eval(raw)
        if isinstance(categories, list) and categories:
            return f"{store['store_name']}은(는) {', '.join(categories)}을(를) 전문으로 하는 음식점이에요."
    except:
        return f"{store['store_name']}의 음식 종류 정보 형식이 올바르지 않아 제공이 어렵습니다."

    return f"{store['store_name']}의 음식 종류 정보는 등록되어 있지 않습니다."

def get_hashtags_by_store_name(store_name: str) -> str:
    store = find_store(store_name)
    if not store:
        return "해당 가게를 찾을 수 없습니다."

    raw = store.get("hashtags", "")
    if not raw or raw in ("[]", "", None):
        return f"{store['store_name']}에 대한 분위기나 특징 정보는 등록되어 있지 않습니다."

    try:
        hashtags = literal_eval(raw)
        if isinstance(hashtags, list) and hashtags:
            return f"{store['store_name']}은(는) {', '.join(hashtags)} 등의 해시태그로 소개되는 곳이에요."
    except:
        return f"{store['store_name']}의 해시태그 정보 형식이 올바르지 않아 제공이 어렵습니다."

    return f"{store['store_name']}의 해시태그 정보는 등록되어 있지 않습니다."



# 3. Function Calling 스키마 정의

menu_lookup_tool = {
    "type": "function",
    "function": {
        "name": "get_menu_by_store_name",
        "description": "사용자가 언급한 가게 이름을 바탕으로 해당 가게의 메뉴와 가격 정보를 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "store_name": {
                    "type": "string",
                    "description": "조회할 가게 이름"
                }
            },
            "required": ["store_name"],
            "additionalProperties": False
        }
    }
}

# 주소 조회 툴
address_lookup_tool = {
    "type": "function",
    "function": {
        "name": "get_address_by_store_name",
        "description": """
        가게 이름(store_name)으로 해당 가게의 주소(address)를 알려주는 함수입니다.
        예시 : "이 가게의 위치는 어디야?", "해당 가게의 장소 알려줘" 등의 질문에 사용됩니다. 
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "store_name": {
                    "type": "string",
                    "description": "조회할 가게 이름"
                }
            },
            "required": ["store_name"]
        }
    }
}

# 영업시간 조회 툴
openhours_lookup_tool = {
    "type": "function",
    "function": {
        "name": "get_openhours_by_store_name",
        "description": "가게 이름으로 해당 가게의 영업시간을 알려주는 함수입니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "store_name": {
                    "type": "string",
                    "description": "조회할 가게 이름"
                }
            },
            "required": []
        }
    }
}

# 전화번호 툴
phone_lookup_tool = {
    "type": "function",
    "function": {
        "name": "get_phone_by_store_name",
        "description": """
        사용자가 특정 가게의 전화번호를 물어볼 때 호출되는 함수입니다.
        예시: 
        - "정원레스토랑 전화번호 알려줘"
        - "이 집 전화번호 뭐야?"
        - "예약 전화 어떻게 해?"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "store_name": {
                    "type": "string",
                    "description": "전화번호를 조회할 가게 이름"
                }
            },
            "required": ["store_name"],
            "additionalProperties": False
        }
    }
}

# 편의시설 툴
facilities_lookup_tool = {
    "type": "function",
    "function": {
        "name": "get_facilities_by_store_name",
        "description": """
        사용자가 특정 가게의 편의시설이나 제공 서비스(예: 예약, 포장 가능, 와이파이 등)를 물어볼 때 호출되는 함수입니다.
        예시:
        - "정원레스토랑 시설 뭐 있어?"
        - "이 가게 포장돼?"
        - "서울부띠끄 와이파이 있어?"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "store_name": {
                    "type": "string",
                    "description": "시설 정보를 조회할 가게 이름"
                }
            },
            "required": ["store_name"],
            "additionalProperties": False
        }
    }
}

# 카테고리 툴
categories_lookup_tool = {
    "type": "function",
    "function": {
        "name": "get_categories_by_store_name",
        "description": """
        사용자가 특정 가게의 음식 종류(한식, 양식, 중식 등)를 물어볼 때 호출되는 함수입니다.
        예시:
        - "정원레스토랑은 무슨 음식 파는 곳이야?"
        - "이 집 양식이야 한식이야?"
        - "서울부띠끄 어떤 음식 전문이야?"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "store_name": {
                    "type": "string",
                    "description": "음식 종류를 조회할 가게 이름"
                }
            },
            "required": ["store_name"],
            "additionalProperties": False
        }
    }
}

# 해시태그 툴
hashtags_lookup_tool = {
    "type": "function",
    "function": {
        "name": "get_hashtags_by_store_name",
        "description": """
        사용자가 특정 가게의 분위기나 특징을 묻는 경우 해시태그 기반으로 설명을 제공하는 함수입니다.
        예시:
        - "서울부띠끄 분위기 어때?"
        - "이 집 데이트하기 좋아?"
        - "정원레스토랑 어떤 분위기야?"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "store_name": {
                    "type": "string",
                    "description": "분위기 및 특징을 조회할 가게 이름"
                }
            },
            "required": ["store_name"],
            "additionalProperties": False
        }
    }
}

# 4. 모든 tool schema를 리스트로 export

tools = [
    menu_lookup_tool,
    address_lookup_tool,
    openhours_lookup_tool,
    phone_lookup_tool,
    facilities_lookup_tool,
    categories_lookup_tool,
    hashtags_lookup_tool
]
