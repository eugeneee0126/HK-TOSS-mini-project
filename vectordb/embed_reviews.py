# 파일: vectordb/embed_reviews.py
# Description: 전처리된 리뷰 데이터를 불러와 HuggingFace 임베딩 모델을 사용해 임베딩한 후 ChromaDB에 저장하는 스크립트
# Author: 통합버전
# Date: 2025.04.29
# Requirements: pandas, langchain, chromadb, huggingface_hub

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))  # 상위 폴더 경로 추가

import os
import pandas as pd
from langchain.schema import Document
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from config import REVIEW_FINAL_CSV, CHROMA_DB_DIR  # 경로 설정 불러오기

def load_reviews(csv_path: str) -> pd.DataFrame:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"{csv_path} 파일을 찾을 수 없습니다.")
    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["리뷰내용"])
    df["리뷰내용"] = df["리뷰내용"].str.strip()
    df = df[df["리뷰내용"] != ""]
    return df

def create_documents(df: pd.DataFrame) -> list[Document]:
    docs = []
    for _, row in df.iterrows():
        doc = Document(
            page_content=f"[{row['가게이름']}] {row['리뷰내용']}",
            metadata={
                "store_name": row['가게이름'],
                "rating": str(row.get('리뷰별점', 'None')),
                "sentiment": row.get('sentiment', 'unknown')
            }
        )
        docs.append(doc)
    return docs

def embed_and_save(documents: list[Document], save_dir: str):
    embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    db = Chroma.from_documents(documents, embedding=embedding_model, persist_directory=save_dir)
    db.persist()
    print(f"[INFO] ChromaDB에 {len(documents)}개 문서를 저장했습니다 → {save_dir}")

def main():
    print("[STEP] 전처리된 리뷰 데이터 불러오는 중...")
    df = load_reviews(REVIEW_FINAL_CSV)

    print("[STEP] 문서(Document) 객체 생성 중...")
    documents = create_documents(df)

    print("[STEP] 리뷰 임베딩 및 ChromaDB 저장 중...")
    embed_and_save(documents, CHROMA_DB_DIR)

if __name__ == "__main__":
    main()
