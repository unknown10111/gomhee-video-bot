"""
임베딩 모델 추상화 서비스
ko-sbert와 OpenAI 임베딩을 쉽게 교체할 수 있도록 설계
"""
from abc import ABC, abstractmethod
from typing import List
import numpy as np

class EmbeddingModel(ABC):
    """임베딩 모델 인터페이스"""
    
    @abstractmethod
    def embed(self, texts: List[str]) -> np.ndarray:
        """
        텍스트 리스트를 임베딩 벡터로 변환
        
        Args:
            texts: 임베딩할 텍스트 리스트
        
        Returns:
            임베딩 벡터 배열 (shape: [len(texts), embedding_dim])
        """
        pass
    
    @abstractmethod
    def embed_query(self, query: str) -> np.ndarray:
        """
        단일 쿼리를 임베딩 벡터로 변환
        
        Args:
            query: 임베딩할 쿼리 텍스트
        
        Returns:
            임베딩 벡터 (shape: [embedding_dim])
        """
        pass
    
    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """임베딩 차원 수"""
        pass


class KoSBERTEmbedding(EmbeddingModel):
    """한국어 SBERT 임베딩 모델"""
    
    def __init__(self, model_name="jhgan/ko-sbert-multitask"):
        """
        Args:
            model_name: 사용할 sentence-transformers 모델 이름
        """
        from sentence_transformers import SentenceTransformer
        
        print(f"Loading Korean SBERT model: {model_name}")
        self.model = SentenceTransformer(model_name)
        print(f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """텍스트 리스트를 임베딩으로 변환"""
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return np.array(embeddings)
    
    def embed_query(self, query: str) -> np.ndarray:
        """단일 쿼리를 임베딩으로 변환"""
        embedding = self.model.encode([query])[0]
        return np.array(embedding)
    
    @property
    def embedding_dim(self) -> int:
        """임베딩 차원 수"""
        return self.model.get_sentence_embedding_dimension()


class OpenAIEmbedding(EmbeddingModel):
    """OpenAI 임베딩 모델"""
    
    def __init__(self, model_name="text-embedding-3-large", api_key=None):
        """
        Args:
            model_name: OpenAI 임베딩 모델 이름
            api_key: OpenAI API 키 (None이면 환경변수에서 가져옴)
        """
        from openai import OpenAI
        import os
        
        self.model_name = model_name
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        
        # 모델별 차원 수
        self._embedding_dims = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }
        
        print(f"OpenAI Embedding model: {model_name}")
        print(f"Embedding dimension: {self.embedding_dim}")
    
    def embed(self, texts: List[str]) -> np.ndarray:
        """텍스트 리스트를 임베딩으로 변환"""
        from tqdm import tqdm
        
        embeddings = []
        batch_size = 100  # OpenAI API 배치 크기
        
        for i in tqdm(range(0, len(texts), batch_size), desc="OpenAI 임베딩 생성 중"):
            batch = texts[i:i+batch_size]
            response = self.client.embeddings.create(
                model=self.model_name,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
        
        return np.array(embeddings)
    
    def embed_query(self, query: str) -> np.ndarray:
        """단일 쿼리를 임베딩으로 변환"""
        response = self.client.embeddings.create(
            model=self.model_name,
            input=[query]
        )
        return np.array(response.data[0].embedding)
    
    @property
    def embedding_dim(self) -> int:
        """임베딩 차원 수"""
        return self._embedding_dims.get(self.model_name, 1536)


def get_embedding_model(model_type="kosbert", **kwargs) -> EmbeddingModel:
    """
    임베딩 모델 팩토리 함수
    
    Args:
        model_type: "kosbert" 또는 "openai"
        **kwargs: 모델별 추가 인자
    
    Returns:
        EmbeddingModel 인스턴스
    """
    if model_type.lower() == "kosbert":
        return KoSBERTEmbedding(**kwargs)
    elif model_type.lower() == "openai":
        return OpenAIEmbedding(**kwargs)
    else:
        raise ValueError(f"Unknown model type: {model_type}. Choose 'kosbert' or 'openai'")


if __name__ == "__main__":
    # 테스트
    print("=== KoSBERT 테스트 ===")
    model = get_embedding_model("kosbert")
    
    test_texts = [
        "ISA 계좌는 절세에 유리합니다.",
        "연금저축펀드로 세액공제를 받을 수 있습니다.",
        "ETF 투자는 분산투자 효과가 있습니다."
    ]
    
    embeddings = model.embed(test_texts)
    print(f"Embeddings shape: {embeddings.shape}")
    
    query = "ISA 활용법이 궁금해요"
    query_emb = model.embed_query(query)
    print(f"Query embedding shape: {query_emb.shape}")
    
    # 코사인 유사도 계산
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity([query_emb], embeddings)[0]
    print(f"\n쿼리와의 유사도:")
    for text, sim in zip(test_texts, similarities):
        print(f"  {sim:.4f} - {text}")
