# 파일: chatbot/app.py
# Description: Gradio UI를 통해 충정로역 맛집 추천 챗봇을 실행하고 사용자 질문에 응답하는 인터페이스를 제공합니다.
# Author: 통합버전
# Date: 2025.04.29
# Requirements: gradio, dotenv, os, sys

import sys
import os
import gradio as gr
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# .env 로드
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError("OPENAI_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인하세요.")

from chatbot.main_chain import run_chatbot_query_with_memory, reset_chat_history

# 사용자 질문에 응답
def respond(message, chat_ui_history):
    try:
        answer = run_chatbot_query_with_memory(message)
    except Exception as e:
        answer = f"죄송합니다. 오류가 발생했어요: {str(e)}"
    chat_ui_history.append((message, answer))
    return "", chat_ui_history

# 초기화 버튼 동작
def reset():
    reset_chat_history()
    return []  # 말풍선도 제거

# Gradio UI 구성
with gr.Blocks() as demo:
    chatbot = gr.Chatbot(label="충정로역 맛집 추천 챗봇", value=[])  # ✅ 초기 메시지 제거
    msg = gr.Textbox(label="질문해주세요!")
    clear = gr.Button("대화 초기화")

    msg.submit(respond, [msg, chatbot], [msg, chatbot])
    clear.click(reset, None, chatbot, queue=False)

if __name__ == "__main__":
    demo.launch(share=True, debug=True)
