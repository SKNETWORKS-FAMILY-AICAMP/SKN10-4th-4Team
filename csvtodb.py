import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# 1️⃣ CSV 불러오기
df = pd.read_csv("서울_쇼핑_정리본.csv")

# 2️⃣ 임베딩 생성 모델 준비 (InstructorXL이나 MiniLM, OpenAI도 가능)
model = SentenceTransformer("all-MiniLM-L6-v2")  # 빠른 모델 (demo용)
# 나중에 Instructor XL 모델 쓰면 더 좋음!

# 3️⃣ 텍스트 만들기 (개요 + 상세정보 합치기)
df['내용'] = df['개요'].fillna('') + " " + df['상세정보'].fillna('')

# 4️⃣ 텍스트 → 임베딩
texts = df['내용'].tolist()
embeddings = model.encode(texts, show_progress_bar=True)

# 5️⃣ ChromaDB 초기화
chroma_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_db"  # 저장할 폴더
))

collection = chroma_client.get_or_create_collection(name="places")

# 6️⃣ VectorDB에 데이터 추가
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

# 7️⃣ 저장
chroma_client.persist()

print("✅ VectorDB 저장 완료!")
