"""
5개 테스트 질문으로 검색 시스템 성능 평가
"""
import chromadb
from embedding_service import get_embedding_model
from chunk_subtitles import format_timestamp

# 테스트 질문 5개 (수집된 36개 영상 기반)
TEST_QUESTIONS = [
    "ISA 만기되면 연금으로 전환하는 게 좋을까요?",
    "커버드콜 ETF 투자는 어떤 경우에 하는 게 좋나요?",
    "주택연금은 누가 가입하면 유리한가요?",
    "사회초년생이 적은 돈으로 투자 시작하려면 어떻게 해야 하나요?",
    "은퇴 후 연금 수령은 어떻게 계획해야 하나요?"
]

def search_videos(query, collection, embedding_model, top_k=5):
    """
    쿼리에 대한 관련 영상 검색
    
    Args:
        query: 검색 쿼리
        collection: ChromaDB 컬렉션
        embedding_model: 임베딩 모델
        top_k: 반환할 결과 개수
    
    Returns:
        검색 결과 리스트
    """
    # 쿼리 임베딩
    query_embedding = embedding_model.embed_query(query)
    
    # 검색
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )
    
    # 결과 포맷팅
    formatted_results = []
    for doc, metadata, distance in zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    ):
        # YouTube URL with timestamp
        start_seconds = int(metadata['start_time'])
        url = f"https://www.youtube.com/watch?v={metadata['video_id']}&t={start_seconds}s"
        
        formatted_results.append({
            'title': metadata['title'],
            'video_id': metadata['video_id'],
            'start_time': metadata['start_time'],
            'end_time': metadata['end_time'],
            'timestamp': format_timestamp(metadata['start_time']),
            'url': url,
            'snippet': doc[:200] + "..." if len(doc) > 200 else doc,
            'similarity_score': 1 - distance,  # 거리를 유사도로 변환
            'distance': distance
        })
    
    return formatted_results

def run_tests(db_path="data/chroma_db", collection_name="gomhee_videos", model_type="kosbert"):
    """
    5개 테스트 질문으로 검색 성능 평가
    """
    print("="*80)
    print("박곰희TV 영상 추천 시스템 - 검색 성능 테스트")
    print("="*80)
    print()
    
    # ChromaDB 로드
    print(f"ChromaDB 로딩: {db_path}")
    client = chromadb.PersistentClient(path=db_path)
    collection = client.get_collection(name=collection_name)
    print(f"컬렉션 '{collection_name}' 로드됨 (문서 수: {collection.count()})")
    print()
    
    # 임베딩 모델 로드
    print(f"임베딩 모델 로딩: {model_type}")
    embedding_model = get_embedding_model(model_type)
    print()
    
    # 각 질문에 대해 검색 수행
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print("="*80)
        print(f"질문 {i}: {question}")
        print("="*80)
        print()
        
        results = search_videos(question, collection, embedding_model, top_k=5)
        
        print(f"Top-5 추천 영상:\n")
        for j, result in enumerate(results, 1):
            print(f"{j}. {result['title']}")
            print(f"   ⏰ 시간: {result['timestamp']} ({result['start_time']:.0f}s - {result['end_time']:.0f}s)")
            print(f"   📊 유사도: {result['similarity_score']:.4f}")
            print(f"   🔗 URL: {result['url']}")
            print(f"   📝 내용: {result['snippet']}")
            print()
        
        print()
    
    print("="*80)
    print("테스트 완료!")
    print("="*80)
    print()
    print("💡 다음 단계:")
    print("1. 각 질문의 Top-3 결과가 실제로 관련 있는지 수동으로 확인")
    print("2. Precision@3 계산 (Top-3 중 관련 영상 비율)")
    print("3. 정확도가 낮으면 OpenAI 모델로 교체 테스트")
    print()

if __name__ == "__main__":
    run_tests(
        db_path="data/chroma_db",
        collection_name="gomhee_videos",
        model_type="kosbert"
    )
