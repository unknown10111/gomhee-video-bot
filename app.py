"""
박곰희TV 영상 추천 시스템 Streamlit UI
"""
# Streamlit Cloud용 SQLite 패치 (로컬에서는 무시됨)
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

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
    /* Google Fonts - Pretendard */
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css');
    
    * {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    }
    
    .stTextInput > div > div > input {
        font-size: 1.1rem;
        font-weight: 400;
    }
    .video-card {
        background-color: white;
        border-radius: 16px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
        overflow: hidden;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .video-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.12);
    }
    .video-thumbnail-container {
        position: relative;
        width: 100%;
        padding-top: 56.25%; /* 16:9 Aspect Ratio */
        overflow: hidden;
        background: #f5f5f5;
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
        padding: 18px;
        display: flex;
        flex-direction: column;
    }
    .video-title {
        font-size: 1.15rem;
        font-weight: 600;
        line-height: 1.5;
        color: #1a1a1a;
        margin-bottom: 10px;
        /* 2줄 제한 */
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .timestamp-badge {
        background: linear-gradient(135deg, #FF6B6B, #FF8E53);
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        align-self: flex-end;
        margin-bottom: 10px;
        box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);
    }

    .watch-button, .watch-button:visited {
        display: block;
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        text-align: center;
        padding: 14px;
        border-radius: 12px;
        font-weight: 600;
        font-size: 1rem;
        text-decoration: none;
        margin-top: 12px;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        transition: transform 0.2s, box-shadow 0.2s;
        border: none;
    }
    .watch-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        color: white !important;
        text-decoration: none;
    }
    
    /* 페이지 타이틀 개선 */
    h1 {
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        color: #1a1a1a !important;
    }
    
    /* 모바일 최적화 */
    @media (max-width: 768px) {
        .block-container {
            padding-top: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        .video-title {
            font-size: 1.05rem;
        }
        .video-content {
            padding: 14px;
        }
        h1 {
            font-size: 1.5rem !important;
        }
        .watch-button {
            font-size: 0.95rem;
            padding: 12px;
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
