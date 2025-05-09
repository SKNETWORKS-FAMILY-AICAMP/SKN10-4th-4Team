import pandas as pd
import re

# CSV 파일 불러오기
df = pd.read_csv("data/서울_문화시설_최신순_100개_1페이지.csv")

# 사용할 컬럼만 남기기
use_cols = ['명칭', '주소', '위도', '경도', '개요', '이용시간', '쉬는날', '상세정보']
df_clean = df[use_cols].copy()

# 🔥 컬럼명 통일 (쇼핑 데이터와 맞추기)
df_clean.rename(columns={'이용시간': '영업시간'}, inplace=True)

# 텍스트 정리 함수
def clean_text(text):
    if pd.isna(text):
        return ""
    # HTML 태그 제거
    text = re.sub(r'<.*?>', ' ', text)
    # 특수기호 제거
    text = re.sub(r'[※*\-•●◆▲▶■★☆▶→\n\t\r]+', ' ', text)
    # 다중 공백 제거
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# 텍스트 컬럼들 클린업
text_cols = ['명칭', '주소', '개요', '영업시간', '쉬는날', '상세정보']
for col in text_cols:
    df_clean[col] = df_clean[col].apply(clean_text)

# 카테고리 추가 (파일 이름에서 가져왔다고 가정)
df_clean['카테고리'] = '문화시설'

# 결과 확인
print(df_clean.head())

# 정리된 CSV로 저장 (선택)
df_clean.to_csv("서울_문화시설_정리본.csv", index=False)
