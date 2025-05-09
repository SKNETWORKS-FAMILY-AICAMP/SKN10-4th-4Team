import pandas as pd

# 엑셀 파일 로드
file_path = "visitkorea_full_dataset_parallel.xlsx"  # 실제 파일 경로로 수정
df = pd.read_excel(file_path)

# 중요도가 높은 컬럼 목록 (순서 중요)
priority_columns = [
    "contentid", "title", "areacode", "sigungucode", "cat1_name", "cat2_name", "cat3_name",
    "contenttypeid", "mapx", "mapy", "firstimage", "image_1", "opentime", "restdate",
    "parking", "reservation", "discountinfo", "scale", "spendtime", "accomcount"
]

# 실제 컬럼에 존재하는 것만 필터링
priority_columns = [col for col in priority_columns if col in df.columns]

# 나머지 컬럼
remaining_columns = [col for col in df.columns if col not in priority_columns]

# 정렬된 컬럼 리스트
sorted_columns = priority_columns + remaining_columns

# 컬럼 순서 재배치
df_sorted = df[sorted_columns]

# 저장
output_path = "sorted_by_priority.xlsx"
df_sorted.to_excel(output_path, index=False)

print(f"✅ 완료: {output_path}")
