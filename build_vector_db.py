"""
청크 데이터를 임베딩하여 ChromaDB에 저장하는 스크립트
"""
import json
from pathlib import Path
import chromadb
from chromadb.config import Settings
from embedding_service import get_embedding_model
from tqdm import tqdm

def build_vector_db(
    chunks_file="data/chunks.json",
    db_path="data/chroma_db",
    collection_name="gomhee_videos",
    model_type="kosbert",
    batch_size=32
):
    """
    청크 데이터를 임베딩하여 ChromaDB에 저장합니다.
    
    Args:
        chunks_file: 청크 데이터 JSON 파일
        db_path: ChromaDB 저장 경로
        collection_name: 컬렉션 이름
        model_type: 임베딩 모델 타입 ("kosbert" 또는 "openai")
        batch_size: 배치 크기
    """
    # 청크 데이터 로드
    print(f"청크 데이터 로딩: {chunks_file}")
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"총 {len(chunks)}개의 청크를 처리합니다.\n")
    
    # 임베딩 모델 로드
    print(f"임베딩 모델 로딩: {model_type}")
    embedding_model = get_embedding_model(model_type)
    print()
    
    # ChromaDB 클라이언트 생성
    print(f"ChromaDB 초기화: {db_path}")
    db_path_obj = Path(db_path)
    db_path_obj.mkdir(parents=True, exist_ok=True)
    
    client = chromadb.PersistentClient(path=str(db_path_obj))
    
    # 기존 컬렉션 삭제 (있다면)
    try:
        client.delete_collection(name=collection_name)
        print(f"기존 컬렉션 '{collection_name}' 삭제됨")
    except:
        pass
    
    # 새 컬렉션 생성
    collection = client.create_collection(
        name=collection_name,
        metadata={"description": "박곰희TV 영상 자막 청크"}
    )
    print(f"컬렉션 '{collection_name}' 생성됨\n")
    
    # 배치 단위로 임베딩 및 저장
    print("임베딩 생성 및 저장 중...")
    
    for i in tqdm(range(0, len(chunks), batch_size), desc="배치 처리"):
        batch_chunks = chunks[i:i+batch_size]
        
        # 텍스트 추출
        texts = [chunk['full_text'] for chunk in batch_chunks]
        
        # 임베딩 생성
        embeddings = embedding_model.embed(texts)
        
        # ChromaDB에 저장
        ids = [f"chunk_{i+j}" for j in range(len(batch_chunks))]
        metadatas = [
            {
                'video_id': chunk['video_id'],
                'title': chunk['title'],
                'chunk_id': chunk['chunk_id'],
                'start_time': chunk['start_time'],
                'end_time': chunk['end_time'],
                'duration': chunk['duration']
            }
            for chunk in batch_chunks
        ]
        documents = [chunk['text'] for chunk in batch_chunks]  # 자막 텍스트만 (제목 제외)
        
        collection.add(
            ids=ids,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            documents=documents
        )
    
    print(f"\n{'='*60}")
    print(f"벡터 DB 구축 완료!")
    print(f"{'='*60}")
    print(f"총 청크 수: {len(chunks)}")
    print(f"임베딩 차원: {embedding_model.embedding_dim}")
    print(f"저장 경로: {db_path}")
    print(f"컬렉션 이름: {collection_name}")
    
    # 컬렉션 통계
    count = collection.count()
    print(f"저장된 문서 수: {count}")
    
    return collection

if __name__ == "__main__":
    # 벡터 DB 구축
    collection = build_vector_db(
        chunks_file="data/chunks.json",
        db_path="data/chroma_db",
        collection_name="gomhee_videos",
        model_type="kosbert",  # 또는 "openai"
        batch_size=32
    )
    
    print("\n=== 테스트 검색 ===")
    # 간단한 테스트 검색
    test_query = "ISA 계좌 활용법"
    print(f"테스트 쿼리: {test_query}")
    
    from embedding_service import get_embedding_model
    model = get_embedding_model("kosbert")
    query_embedding = model.embed_query(test_query)
    
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=3
    )
    
    print("\nTop-3 결과:")
    for i, (doc, metadata, distance) in enumerate(zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    ), 1):
        print(f"\n{i}. {metadata['title']}")
        print(f"   시간: {metadata['start_time']:.0f}s - {metadata['end_time']:.0f}s")
        print(f"   유사도: {1 - distance:.4f}")
        print(f"   내용: {doc[:100]}...")
