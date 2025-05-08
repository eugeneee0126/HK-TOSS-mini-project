# 파일 위치: chatbot/memory_chain.py
# Description: 사용자 질문과 리뷰 벡터 DB 문맥을 바탕으로 툴 호출 및 응답을 처리하는 RAG 기반 챗봇 로직 구현 (메모리 기반 대화 포함)
# Author: 통합버전
# Date: 2025.04.29
# Requirements: openai, dotenv, json, 사용자 정의 툴 모듈 (tools.py), vectordb.retriever

from dotenv import load_dotenv
load_dotenv()  # .env 파일에 있는 환경변수들을 시스템 환경변수로 로드

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 상위 폴더 경로 추가

import os
import json
from openai import OpenAI
from chatbot.tools import (
    tools,
    get_menu_by_store_name,
    get_address_by_store_name,
    get_openhours_by_store_name,
    get_categories_by_store_name,
    get_facilities_by_store_name,
    get_hashtags_by_store_name,
    get_phone_by_store_name,
)

# retriever는 외부에서 import 해오거나 별도 모듈에서 정의되어 있어야 합니다.
from vectordb.load_retriever import get_retriever
retriever = get_retriever()

# 1. 대화 히스토리 초기화
chat_history = [
    {
        "role": "system",
        "content": """
            당신은 서울 충정로역 주변 맛집 정보를 제공합니다.
            정보를 바탕으로 맛집을 추천해주는 똑똑한 챗봇입니다.

            아래 기준에 따라 행동하세요:
            1. 사용자가 메뉴를 물으면 반드시 get_menu_by_store_name 툴을 호출하세요.
            2. 사용자가 주소를 물으면 반드시 get_address_by_store_name 툴을 호출하세요.
            3. 사용자가 영업시간을 물으면 반드시 get_openhours_by_store_name 툴을 호출하세요.
            4. 사용자가 전화번호를 물으면 반드시 get_phone_by_store_name 툴을 호출하세요.
            5. 사용자가 편의시설을 물으면 반드시 get_facilities_by_store_name 툴을 호출하세요.
            6. 사용자가 음식 종류(한식, 중식, 양식, 일식 등)를 물으면 반드시 get_categories_by_store_name 툴을 호출하세요.
            7. 사용자가 가게 분위기나 특징을 물으면 반드시 get_hashtags_by_store_name 툴을 호출하세요.
            8. 사용자가 맛/분위기/후기 등을 물으면 vector DB에서 리뷰 검색 후 답변하세요.
            9. 툴 호출 시 store_name이 불명확하면 다시 요청하세요.

            또한, 메뉴/가게 정보는 보기 좋게 목차처럼 정리해서 보여주세요.
            리뷰 정보는 말하듯 자연스럽게 풀어서 설명해주세요.
        """
    }
]

def reset_chat_history():
    """chat_history를 system prompt만 남기고 초기화합니다."""
    global chat_history
    chat_history = chat_history[:1]
    print("대화 히스토리가 초기화되었습니다.")

def run_chatbot_query_with_memory(query: str) -> str:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Step 1: 리뷰 검색 (RAG)
    docs = retriever.get_relevant_documents(query)
    context = "\n".join([doc.page_content for doc in docs])

    # Step 2: 히스토리에 질문 + context 추가
    chat_history.append({"role": "user", "content": query})
    chat_history.append({"role": "assistant", "content": f"다음은 관련 리뷰입니다:\n{context}"})

    # Step 3: GPT 호출 (1차)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=chat_history,
        tools=tools,
        tool_choice="auto"
    )

    tool_calls = response.choices[0].message.tool_calls
    if tool_calls:
        tool_messages = []

        for call in tool_calls:
            func_name = call.function.name
            args = json.loads(call.function.arguments)
            store_name = args.get("store_name", "")

            if func_name == "get_menu_by_store_name":
                tool_result = get_menu_by_store_name(store_name)
            elif func_name == "get_address_by_store_name":
                tool_result = get_address_by_store_name(store_name)
            elif func_name == "get_openhours_by_store_name":
                tool_result = get_openhours_by_store_name(store_name)
            elif func_name == "get_categories_by_store_name":
                tool_result = get_categories_by_store_name(store_name)
            elif func_name == "get_facilities_by_store_name":
                tool_result = get_facilities_by_store_name(store_name)
            elif func_name == "get_hashtags_by_store_name":
                tool_result = get_hashtags_by_store_name(store_name)
            elif func_name == "get_phone_by_store_name":
                tool_result = get_phone_by_store_name(store_name)
            else:
                tool_result = f"정의되지 않은 함수입니다: {func_name}"

            tool_messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": func_name,
                "content": tool_result
            })

        follow_up_messages = chat_history + [
            {"role": "assistant", "content": None, "tool_calls": tool_calls},
            *tool_messages
        ]

        final_response = client.chat.completions.create(
            model="gpt-4o",
            messages=follow_up_messages
        )

        final_content = final_response.choices[0].message.content
        chat_history.append({"role": "assistant", "content": final_content})
        return final_content

    # 툴 없이 응답했을 경우
    assistant_response = response.choices[0].message.content
    chat_history.append({"role": "assistant", "content": assistant_response})
    return assistant_response
