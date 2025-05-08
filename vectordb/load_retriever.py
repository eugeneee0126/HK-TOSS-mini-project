# 파일: vectordb/load_retriever.py
# Description: ChromaDB에 저장된 벡터 데이터를 불러와 검색 가능한 Retriever 객체를 생성하는 스크립트
# Author: 통합버전
# Date: 2025.04.29
# Requirements: langchain, chromadb, huggingface_hub

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 상위 폴더 경로 추가

from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from config import CHROMA_DB_DIR

def get_retriever():
    embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    db = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embedding_model
    )
    retriever = db.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5}
    )
    print("Retriever가 성공적으로 로드되었습니다.")
    return retriever
