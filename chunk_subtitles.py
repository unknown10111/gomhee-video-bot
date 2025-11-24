"""
자막을 청킹(chunking)하는 모듈
긴 영상의 자막을 2분 단위로 나누어 더 정확한 검색 가능
"""
import json
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

def chunk_subtitle(subtitle_data: Dict, chunk_duration: float = 120.0) -> List[Dict]:
    """
    자막 데이터를 시간 단위로 청킹합니다.
    
    Args:
        subtitle_data: 자막 데이터 (video_id, title, subtitles 포함)
        chunk_duration: 청크 길이 (초 단위, 기본 120초 = 2분)
    
    Returns:
        청크 리스트
    """
    video_id = subtitle_data['video_id']
    title = subtitle_data['title']
    subtitles = subtitle_data['subtitles']
    
    if not subtitles:
        return []
    
    chunks = []
    current_chunk = {
        'texts': [],
        'start_time': 0.0,
        'end_time': 0.0
    }
    
    for sub in subtitles:
        start = sub['start']
        duration = sub['duration']
        text = sub['text']
        end = start + duration
        
        # 첫 번째 자막이거나 현재 청크 범위 내인 경우
        if not current_chunk['texts'] or start < current_chunk['start_time'] + chunk_duration:
            current_chunk['texts'].append(text)
            if not current_chunk['start_time']:
                current_chunk['start_time'] = start
            current_chunk['end_time'] = end
        else:
            # 현재 청크 저장
            if current_chunk['texts']:
                chunks.append({
                    'video_id': video_id,
                    'title': title,
                    'chunk_id': len(chunks),
                    'start_time': current_chunk['start_time'],
                    'end_time': current_chunk['end_time'],
                    'text': ' '.join(current_chunk['texts']),
                    'duration': current_chunk['end_time'] - current_chunk['start_time']
                })
            
            # 새 청크 시작
            current_chunk = {
                'texts': [text],
                'start_time': start,
                'end_time': end
            }
    
    # 마지막 청크 저장
    if current_chunk['texts']:
        chunks.append({
            'video_id': video_id,
            'title': title,
            'chunk_id': len(chunks),
            'start_time': current_chunk['start_time'],
            'end_time': current_chunk['end_time'],
            'text': ' '.join(current_chunk['texts']),
            'duration': current_chunk['end_time'] - current_chunk['start_time']
        })
    
    return chunks


def process_all_subtitles(subtitles_dir="data/subtitles", output_file="data/chunks.json", chunk_duration=120.0):
    """
    모든 자막 파일을 청킹하여 하나의 파일로 저장합니다.
    
    Args:
        subtitles_dir: 자막 파일들이 있는 디렉토리
        output_file: 출력 파일 경로
        chunk_duration: 청크 길이 (초)
    
    Returns:
        전체 청크 리스트
    """
    subtitles_path = Path(subtitles_dir)
    
    if not subtitles_path.exists():
        print(f"자막 디렉토리가 없습니다: {subtitles_dir}")
        return []
    
    # 모든 자막 파일 찾기
    subtitle_files = list(subtitles_path.glob("*.json"))
    
    if not subtitle_files:
        print(f"자막 파일이 없습니다: {subtitles_dir}")
        return []
    
    print(f"총 {len(subtitle_files)}개의 자막 파일을 처리합니다.")
    print(f"청크 길이: {chunk_duration}초 ({chunk_duration/60:.1f}분)")
    
    all_chunks = []
    
    for subtitle_file in tqdm(subtitle_files, desc="자막 청킹 중"):
        try:
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                subtitle_data = json.load(f)
            
            chunks = chunk_subtitle(subtitle_data, chunk_duration)
            all_chunks.extend(chunks)
            
        except Exception as e:
            print(f"오류 발생 ({subtitle_file.name}): {e}")
            continue
    
    print(f"\n총 {len(all_chunks)}개의 청크가 생성되었습니다.")
    
    # 각 청크에 전체 텍스트 추가 (제목 + 자막)
    for chunk in all_chunks:
        chunk['full_text'] = f"제목: {chunk['title']}\n\n{chunk['text']}"
    
    # JSON 파일로 저장
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)
    
    print(f"청크 데이터 저장 완료: {output_path}")
    
    # 통계 출력
    avg_chunk_duration = sum(c['duration'] for c in all_chunks) / len(all_chunks) if all_chunks else 0
    print(f"\n=== 청킹 통계 ===")
    print(f"평균 청크 길이: {avg_chunk_duration:.1f}초 ({avg_chunk_duration/60:.1f}분)")
    print(f"평균 청크당 글자 수: {sum(len(c['text']) for c in all_chunks) / len(all_chunks):.0f}자")
    
    return all_chunks


def format_timestamp(seconds: float) -> str:
    """
    초를 YouTube 타임스탬프 형식으로 변환
    
    Args:
        seconds: 초 단위 시간
    
    Returns:
        "HH:MM:SS" 또는 "MM:SS" 형식의 문자열
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


if __name__ == "__main__":
    # 테스트
    chunks = process_all_subtitles(
        subtitles_dir="data/subtitles",
        output_file="data/chunks.json",
        chunk_duration=120.0  # 2분
    )
    
    if chunks:
        print(f"\n=== 첫 번째 청크 예시 ===")
        first_chunk = chunks[0]
        print(f"영상: {first_chunk['title']}")
        print(f"시간: {format_timestamp(first_chunk['start_time'])} - {format_timestamp(first_chunk['end_time'])}")
        print(f"내용: {first_chunk['text'][:200]}...")
