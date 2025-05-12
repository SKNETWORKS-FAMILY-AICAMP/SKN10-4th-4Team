import pandas as pd
import re
from sentence_transformers import SentenceTransformer
import chromadb

### ✅ 새로 넣을 CSV 파일명 & 소스 이름만 바꾸면 됨!!
csv_file = "data/최종정리본.csv"


### 🔥 데이터 불러오기
df = pd.read_csv(csv_file)

df['내용'] = df['개요'].fillna('') + " " + df['상세정보'].fillna('')

def clean_text(text):
    if pd.isna(text):
        return ""
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'[※*\-•●◆▲▶■★☆▶→\n\t\r]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['내용'] = df['내용'].apply(clean_text)

### 🔥 e5-large-v2 모델 준비
model = SentenceTransformer("intfloat/e5-large-v2")

texts = df['내용'].tolist()
embeddings = model.encode(
    ["passage: " + text for text in texts],
    show_progress_bar=True
)

### 🔥 ChromaDB 연결
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="places")

### 🔥 데이터 추가 (기존 데이터 유지됨!!)
for idx, row in df.iterrows():
    collection.add(
        embeddings=[embeddings[idx]],
        documents=[row['내용']],
        metadatas=[{
            "name": row['명칭'],
            "region": row['주소'],
            "description": row['개요'],
            "category": row['카테고리'],
            "open_time": row['이용시간'],
            "closed_day": row['쉬는날'],
            "detail": row['상세정보'],
            "location": row['지역'],
        }]
    )

print(f"✅ {csv_file} 데이터 임베딩 & ChromaDB 추가 완료!")
print("총 데이터 개수:", collection.count())
