import pandas as pd
import re

# 🔥 XLSX 파일 불러오기
xlsx_file = "data/dataset.xlsx"
df = pd.read_excel(xlsx_file, sheet_name=0)  # 첫 번째 시트 사용

# 사용할 컬럼만 남기기
use_cols = ["명칭","주소","개요","쉬는날","이용시간","상세정보","시트이름"]
df_clean = df[use_cols].copy()
df_clean.rename(columns={"시트이름": "카테고리"}, inplace=True)
# 주소에서 시/도 단위 지역명 추출
def extract_region(address):
    if pd.isna(address):
        return ""
    tokens = str(address).split()
    for token in tokens:
        if any(x in token for x in ["시", "도", "특별자치"]):
            return token
    return tokens[0] if tokens else ""

df_clean["지역"] = df_clean["주소"].apply(extract_region)

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
text_cols = ["명칭","주소","개요","쉬는날","이용시간","상세정보","카테고리"]
for col in text_cols:
    df_clean[col] = df_clean[col].apply(clean_text)


# 결과 확인
print(df_clean.head())

# 정리된 CSV로 저장 (선택)
df_clean.to_csv("최종정리본1.csv", index=False)
