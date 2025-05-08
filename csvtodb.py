import pandas as pd
import re
from sentence_transformers import SentenceTransformer
import chromadb

# 🔥 CSV 불러오기
df = pd.read_csv("서울_쇼핑_정리본.csv")

df['내용'] = df['개요'].fillna('') + " " + df['상세정보'].fillna('')

def clean_text(text):
    if pd.isna(text):
        return ""
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'[※*\-•●◆▲▶■★☆▶→\n\t\r]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

df['내용'] = df['내용'].apply(clean_text)

# 🔥 e5-large-v2 모델 불러오기
model = SentenceTransformer("intfloat/e5-large-v2")

# 🔥 장소 설명 임베딩 (e5 형식 → "passage: ..." 로 해야 성능 극대화!)
texts = df['내용'].tolist()
embeddings = model.encode(
    ["passage: " + text for text in texts],
    show_progress_bar=True
)

# 🔥 ChromaDB 연결
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="places")

# 🔥 기존 데이터 있으면 삭제 (중복 방지!)
try:
    chroma_client.delete_collection("places")
    collection = chroma_client.get_or_create_collection(name="places")
except:
    pass

# 🔥 데이터 추가
for idx, row in df.iterrows():
    collection.add(
        ids=[str(row['명칭']) + "_" + str(idx)],
        embeddings=[embeddings[idx]],
        documents=[row['내용']],
        metadatas=[{
            "name": row['명칭'],
            "region": row['주소'],
            "category": row['카테고리'],
            "latitude": row['위도'],
            "longitude": row['경도'],
            "open_time": row['영업시간'],
            "closed_day": row['쉬는날']
        }]
    )

print("✅ e5 임베딩 완료 & ChromaDB 저장 완료!")
