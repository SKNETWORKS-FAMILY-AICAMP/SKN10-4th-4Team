import chromadb

### 🔥 ChromaDB 연결
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="places")

### 🔥 컬렉션 안에 몇 개 들어있는지 먼저 확인
print("총 데이터 개수:", collection.count())

### 🔥 ID 목록 가져오기 (최대 1000개까지만 예시로)
results = collection.get(include=["ids", "metadatas"], limit=1000)

ids = results["ids"]
metadatas = results["metadatas"]

print("\n=== 데이터 ID 목록 ===")
for i, id in enumerate(ids):
    print(f"{i+1}: {id}")

print("\n=== 메타데이터 샘플 ===")
for i, meta in enumerate(metadatas[:5]):  # 메타데이터 5개만 샘플 출력
    print(f"ID: {ids[i]}")
    print(meta)
    print("------")
