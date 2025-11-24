"""
박곰희TV 영상 추천 시스템 Streamlit UI
"""
import streamlit as st
import chromadb
from embedding_service import get_embedding_model
from chunk_subtitles import format_timestamp
import time

# 페이지 설정
st.set_page_config(
    page_title="박곰희TV 영상 추천 봇",
    page_icon="🐻",
    layout="wide"
)

# 스타일 설정
st.markdown("""
<style>
    .stTextInput > div > div > input {
        font-size: 1.2rem;
    }
    .video-card {
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 25px;
        overflow: hidden;
        transition: transform 0.2s;
    }
    .video-card:hover {
        transform: translateY(-5px);
    }
    .video-thumbnail-container {
        position: relative;
        width: 100%;
        padding-top: 56.25%; /* 16:9 Aspect Ratio */
        overflow: hidden;
    }
    .video-thumbnail {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .video-content {
        padding: 20px;
        display: flex;
        flex-direction: column;
    }
    .video-title {
        font-size: 1.3rem;
        font-weight: 700;
        margin-bottom: 10px;
        color: #1f1f1f;
        line-height: 1.4;
    }
    .timestamp-badge {
        background-color: #ff0000;
        color: white;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        align-self: flex-end;
        margin-bottom: 10px;
    }

    .watch-button, .watch-button:visited {
        display: block;
        width: 100%;
        background: linear-gradient(45deg, #FF512F, #DD2476);
        color: white !important;
        text-align: center;
        padding: 12px;
        border-radius: 10px;
        font-weight: bold;
        text-decoration: none;
        margin-top: 15px;
        box-shadow: 0 4px 15px rgba(221, 36, 118, 0.3);
        transition: transform 0.2s, box-shadow 0.2s;
        border: none;
    }
    .watch-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(221, 36, 118, 0.4);
        color: white !important;
        text-decoration: none;
    }
    
    /* 모바일 최적화 */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        .video-title {
            font-size: 1.1rem;
        }
        .video-content {
            padding: 15px;
        }
    }
</style>
""", unsafe_allow_html=True)

# 제목 및 설명
st.title("🐻 박곰희TV 영상 추천 봇")
st.markdown("궁금한 점을 물어보세요! 박곰희TV 영상 중에서 가장 관련 있는 부분을 찾아드립니다.")

# 기본 설정
model_type = "kosbert"
top_k = 2

# 리소스 로딩 (캐싱)
@st.cache_resource
def load_resources(model_type):
    # ChromaDB 로드
    client = chromadb.PersistentClient(path="data/chroma_db")
    collection = client.get_collection(name="gomhee_videos")
    
    # 임베딩 모델 로드
    embedding_model = get_embedding_model(model_type)
    
    return collection, embedding_model

try:
    collection, embedding_model = load_resources(model_type)
except Exception as e:
    st.error(f"리소스 로딩 중 오류 발생: {e}")
    st.stop()

# 검색 함수
def search_videos(query, top_k=3):
    # 쿼리 임베딩
    query_embedding = embedding_model.embed_query(query)
    
    # 검색
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )
    
    formatted_results = []
    for doc, metadata, distance in zip(
        results['documents'][0],
        results['metadatas'][0],
        results['distances'][0]
    ):
        start_seconds = int(metadata['start_time'])
        url = f"https://www.youtube.com/watch?v={metadata['video_id']}&t={start_seconds}s"
        # 고해상도 썸네일 사용 (hqdefault or maxresdefault)
        thumbnail_url = f"https://img.youtube.com/vi/{metadata['video_id']}/hqdefault.jpg"
        
        formatted_results.append({
            'title': metadata['title'],
            'video_id': metadata['video_id'],
            'start_time': metadata['start_time'],
            'end_time': metadata['end_time'],
            'timestamp': format_timestamp(metadata['start_time']),
            'url': url,
            'thumbnail': thumbnail_url,
            'snippet': doc,
            'similarity_score': 1 - distance
        })
    
    return formatted_results

# 세션 상태 초기화
if "query_input" not in st.session_state:
    st.session_state.query_input = ""

def set_query(q):
    st.session_state.query_input = q

# 메인 인터페이스
query = st.text_input("질문을 입력하세요", placeholder="예: ISA 계좌는 어떻게 활용하나요?", key="query_input")

if query:
    with st.spinner("관련 영상을 찾고 있습니다..."):
        start_time = time.time()
        results = search_videos(query, top_k)
        end_time = time.time()
        
    st.success(f"검색 완료! ({end_time - start_time:.2f}초)")
    
    for i, result in enumerate(results, 1):
        st.markdown(f"""
        <div class="video-card">
            <a href="{result['url']}" target="_blank">
                <div class="video-thumbnail-container">
                    <img src="{result['thumbnail']}" class="video-thumbnail">
                </div>
            </a>
            <div class="video-content">
                <div class="video-title">{i}. {result['title']}</div>
                <span class="timestamp-badge">⏱️ {result['timestamp']}부터 재생</span>
                <a href="{result['url']}" target="_blank" class="watch-button">
                    🎥 영상 보러가기
                </a>
            </div>
        </div>
        """, unsafe_allow_html=True)

# 추천 질문
st.markdown("### 💡 이런 질문은 어떠세요?")
col1, col2 = st.columns(2)
with col1:
    st.button("ISA 만기되면 연금으로 전환하는 게 좋을까요?", on_click=set_query, args=("ISA 만기되면 연금으로 전환하는 게 좋을까요?",))
with col2:
    st.button("사회초년생 투자 시작 방법 알려줘", on_click=set_query, args=("사회초년생 투자 시작 방법 알려줘",))
