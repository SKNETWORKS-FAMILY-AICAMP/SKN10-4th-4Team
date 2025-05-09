import pandas as pd

# 파일 경로
data_file = "mapping data.xlsx"
code_file = "한국관광공사_국문_서비스분류코드_v4.2.xlsx"
output_file = "mapping_data_cat_translated_fixed.xlsx"

# 서비스 분류코드 로드
code_df = pd.read_excel(code_file, engine='openpyxl')
code_df.columns = code_df.columns.str.strip()

# 컬럼명 통일 (추정)
code_df.rename(columns={
    code_df.columns[0]: "cat1",
    code_df.columns[1]: "cat2",
    code_df.columns[2]: "cat3",
    code_df.columns[3]: "cat1_name",
    code_df.columns[4]: "cat2_name",
    code_df.columns[5]: "cat3_name"
}, inplace=True)

# 공백 제거
for col in ["cat1", "cat2", "cat3"]:
    code_df[col] = code_df[col].astype(str).str.strip()

# 매핑 딕셔너리
cat1_map = code_df.dropna(subset=["cat1", "cat1_name"]).drop_duplicates("cat1").set_index("cat1")["cat1_name"].to_dict()
cat2_map = code_df.dropna(subset=["cat2", "cat2_name"]).drop_duplicates("cat2").set_index("cat2")["cat2_name"].to_dict()
cat3_map = code_df.dropna(subset=["cat3", "cat3_name"]).drop_duplicates("cat3").set_index("cat3")["cat3_name"].to_dict()

# 매핑할 데이터 로드
df = pd.read_excel(data_file, engine="openpyxl")
for col in ["cat1", "cat2", "cat3"]:
    df[col] = df[col].astype(str).str.strip()

# 매핑 적용
df["cat1_name"] = df["cat1"].map(cat1_map)
df["cat2_name"] = df["cat2"].map(cat2_map)
df["cat3_name"] = df["cat3"].map(cat3_map)

# 확인용 출력
print("📌 매핑된 고유 cat1_name:", df["cat1_name"].dropna().unique())
print("📌 매핑된 고유 cat2_name:", df["cat2_name"].dropna().unique())
print("📌 매핑된 고유 cat3_name:", df["cat3_name"].dropna().unique())

# 결과 저장
df.to_excel(output_file, index=False)
print(f"✅ 저장 완료: {output_file}")
