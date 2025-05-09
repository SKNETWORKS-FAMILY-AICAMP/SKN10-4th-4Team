
import pandas as pd
import os

# 📌 엑셀 파일 경로 설정
INPUT_FILE = "visitkorea_full_dataset_parallel.xlsx"
OUTPUT_FILE = "visitkorea_grouped_by_category.xlsx"

# 📌 컬럼 → 그룹 분류 매핑
column_group_mapping = {
    "addr1": "기본정보", "addr2": "기본정보", "areacode": "기본정보", "sigungucode": "기본정보",
    "mapx": "기본정보", "mapy": "기본정보", "mlevel": "기본정보", "zipcode": "기본정보",
    "title": "기본정보", "tel": "기본정보", "contentid": "기본정보", "contenttypeid": "기본정보",
    "firstimage": "기본정보", "firstimage2": "기본정보", "cpyrhtDivCd": "기본정보",
    "cat1": "카테고리", "cat2": "카테고리", "cat3": "카테고리",
    "image_1": "이미지", "image_2": "이미지", "image_3": "이미지",
    "roomcount": "숙박", "roomtype": "숙박", "checkintime": "숙박", "checkouttime": "숙박",
    "parkinglodging": "숙박", "infocenterlodging": "숙박", "reservationlodging": "숙박",
    "scalelodging": "숙박", "accomcountlodging": "숙박", "openperiod": "숙박",
    "goodstay": "숙박", "benikia": "숙박", "hanok": "숙박", "chkcooking": "숙박",
    "firstmenu": "음식", "treatmenu": "음식", "smoking": "음식", "packing": "음식",
    "infocenterfood": "음식", "scalefood": "음식", "parkingfood": "음식", "opendatefood": "음식",
    "opentimefood": "음식", "restdatefood": "음식", "discountinfofood": "음식",
    "chkcreditcardfood": "음식", "reservationfood": "음식", "lcnsno": "음식",
    "overview": "개요", "homepage": "개요"
}

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"❌ 파일을 찾을 수 없습니다: {INPUT_FILE}")
        return

    print("📦 엑셀 파일 로딩 중...")
    df = pd.read_excel(INPUT_FILE, engine="openpyxl")

    # 실제 존재하는 컬럼만 추출
    valid_mapping = {col: grp for col, grp in column_group_mapping.items() if col in df.columns}

    print("📁 그룹별로 시트 분리 저장 중...")
    with pd.ExcelWriter(OUTPUT_FILE, engine="xlsxwriter") as writer:
        for group in set(valid_mapping.values()):
            cols = [col for col, g in valid_mapping.items() if g == group]
            df[cols].to_excel(writer, sheet_name=group[:31], index=False)

    print(f"✅ 저장 완료: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
