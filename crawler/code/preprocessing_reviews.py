# preprocessing_reviews.py ( 리뷰 전처리 파이프라인 모듈화 )

import pandas as pd
# import re : 우린 정규식처리 안 해도 될 거 같 

def load_data(filepath):
    """
    CSV 파일을 불러오는 함수.

    Args:
        filepath (str): 불러올 CSV 파일의 경로
    Returns:
        pd.DataFrame: 불러온 데이터프레임
    """
    return pd.read_csv(filepath)

def clean_text(df):
    """
    리뷰 텍스트에서 줄바꿈, 탭 문자를 제거하고 양쪽 공백을 정리하는 함수.

    Args:
        df (pd.DataFrame): 원본 데이터프레임
    Returns:
        pd.DataFrame: 텍스트가 정리된 데이터프레임
    """
    df['리뷰내용'] = df['리뷰내용'].astype(str).str.replace('\n', ' ').str.replace('\r', ' ').str.strip()
    return df

def remove_short_reviews(df, min_length=4):
    """
    너무 짧은 리뷰(기본 4자 미만)를 제거하는 함수.

    Args:
        df (pd.DataFrame): 원본 데이터프레임
        min_length (int, optional): 유지할 최소 리뷰 길이 (기본값 4)
    Returns:
        pd.DataFrame: 짧은 리뷰가 제거된 데이터프레임
    """
    df = df[df['리뷰내용'].str.len() >= min_length]
    return df

def remove_long_reviews(df, max_length=1000):
    """
    너무 긴 리뷰(기본 1000자 초과)를 제거하는 함수.

    Args:
        df (pd.DataFrame): 원본 데이터프레임
        max_length (int, optional): 유지할 최대 리뷰 길이 (기본값 1000)
    Returns:
        pd.DataFrame: 긴 리뷰가 제거된 데이터프레임
    """
    df = df[df['리뷰내용'].str.len() <= max_length]
    return df

def classify_sentiment(score):
    """
    별점을 기반으로 sentiment를 분류하는 함수.

    Args:
        score (float or int): 리뷰 별점 (1~5)
    Returns:
        str: 'positive', 'neutral', 'negative' 중 하나
    """
    if score >= 4:
        return 'positive'
    elif score <= 2:
        return 'negative'
    else:
        return 'neutral'

def add_sentiment_column(df):
    """
    리뷰 데이터에 sentiment 컬럼을 추가하는 함수.

    Args:
        df (pd.DataFrame): 원본 데이터프레임
    Returns:
        pd.DataFrame: sentiment 컬럼이 추가된 데이터프레임
    """
    df['sentiment'] = df['리뷰별점'].apply(classify_sentiment)
    return df

def drop_missing_values(df):
    """
    리뷰내용 또는 리뷰별점이 결측(NaN)인 행을 제거하는 함수.

    Args:
        df (pd.DataFrame): 원본 데이터프레임
    Returns:
        pd.DataFrame: 결측치가 제거된 데이터프레임
    """
    df = df.dropna(subset=['리뷰내용', '리뷰별점'])
    return df

def preprocess_reviews(filepath):
    """
    전체 리뷰 전처리 과정을 수행하는 메인 파이프라인 함수.

    Args:
        filepath (str): 불러올 CSV 파일 경로
    Returns:
        pd.DataFrame: 전처리가 완료된 최종 데이터프레임
    """
    df = load_data(filepath)
    df = clean_text(df)
    df = remove_short_reviews(df)
    df = remove_long_reviews(df)
    df = add_sentiment_column(df)
    df = drop_missing_values(df)
    return df

"""
# analysis.py 파일은 preprocessing_reviews.py를 실행시켜서 csv까지 저장합니다.
file_path에는 각자 전처리가 필요한 리뷰데이터의 파일 경로를 넣어주면 됩니다.

from preprocessing_reviews import preprocess_reviews

file_path = "/Users/user/HK-TOSS-mini-project/crawler/data/reviews.csv"
df_processed = preprocess_reviews(file_path)

# 현재 디렉토리에 저장
df_processed.to_csv("reviews_final.csv", index=False, encoding="utf-8-sig")

"""