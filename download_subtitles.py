"""
수집된 영상들의 자막을 다운로드하는 스크립트
youtube-transcript-api를 사용하여 각 영상의 한국어 자막을 다운로드합니다.
"""
import json
import os
from pathlib import Path
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from tqdm import tqdm
import time

def download_subtitles(videos_metadata_file="data/videos_metadata.json", output_dir="data/subtitles"):
    """
    영상 메타데이터 파일을 읽어서 각 영상의 자막을 다운로드합니다.
    
    Args:
        videos_metadata_file: 영상 메타데이터 JSON 파일 경로
        output_dir: 자막을 저장할 디렉토리
    """
    # 출력 디렉토리 생성
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 메타데이터 로드
    with open(videos_metadata_file, 'r', encoding='utf-8') as f:
        videos = json.load(f)
    
    print(f"총 {len(videos)}개의 영상에서 자막을 다운로드합니다.\n")
    
    # API 인스턴스 생성
    api = YouTubeTranscriptApi()
    
    # 통계
    success_count = 0
    failed_count = 0
    no_subtitle_count = 0
    failed_videos = []
    
    # 각 영상에 대해 자막 다운로드
    for video in tqdm(videos, desc="자막 다운로드 중"):
        video_id = video['video_id']
        title = video['title']
        
        try:
            # 자막 목록 가져오기
            transcript_list = api.list(video_id)
            
            # 한국어 자막 찾기
            try:
                transcript = transcript_list.find_transcript(['ko'])
            except NoTranscriptFound:
                # 한국어 자막이 없으면 첫 번째 사용 가능한 자막
                if transcript_list._manually_created_transcripts:
                    lang_code = list(transcript_list._manually_created_transcripts.keys())[0]
                    transcript = transcript_list._manually_created_transcripts[lang_code]
                elif transcript_list._generated_transcripts:
                    lang_code = list(transcript_list._generated_transcripts.keys())[0]
                    transcript = transcript_list._generated_transcripts[lang_code]
                else:
                    raise NoTranscriptFound("No transcripts available")
            
            # 자막 데이터 가져오기
            subtitle_data = transcript.fetch()
            
            # 자막을 텍스트로 변환
            subtitle_text = []
            for entry in subtitle_data:
                subtitle_text.append({
                    'start': entry.start,
                    'duration': entry.duration,
                    'text': entry.text
                })
            
            # JSON 파일로 저장
            output_file = output_path / f"{video_id}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'video_id': video_id,
                    'title': title,
                    'language': transcript.language_code,
                    'subtitles': subtitle_text
                }, f, ensure_ascii=False, indent=2)
            
            # 메타데이터에 자막 파일 경로 추가
            video['subtitle_file'] = str(output_file)
            video['has_subtitle'] = True
            
            success_count += 1
            
        except TranscriptsDisabled:
            video['has_subtitle'] = False
            video['subtitle_error'] = 'Transcripts disabled'
            no_subtitle_count += 1
            failed_videos.append({'video_id': video_id, 'title': title, 'reason': 'Transcripts disabled'})
            
        except NoTranscriptFound:
            video['has_subtitle'] = False
            video['subtitle_error'] = 'No transcript found'
            no_subtitle_count += 1
            failed_videos.append({'video_id': video_id, 'title': title, 'reason': 'No transcript found'})
            
        except Exception as e:
            video['has_subtitle'] = False
            video['subtitle_error'] = str(e)
            failed_count += 1
            failed_videos.append({'video_id': video_id, 'title': title, 'reason': str(e)})
        
        # API 제한 방지를 위한 짧은 대기
        time.sleep(0.1)
    
    # 업데이트된 메타데이터 저장
    with open(videos_metadata_file, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)
    
    # 결과 출력
    print(f"\n{'='*60}")
    print(f"자막 다운로드 완료!")
    print(f"{'='*60}")
    print(f"✅ 성공: {success_count}개")
    print(f"❌ 자막 없음: {no_subtitle_count}개")
    print(f"⚠️  오류: {failed_count}개")
    print(f"총 처리: {len(videos)}개")
    print(f"성공률: {success_count/len(videos)*100:.1f}%")
    
    if failed_videos:
        print(f"\n실패한 영상 목록:")
        for i, failed in enumerate(failed_videos[:10], 1):  # 처음 10개만 표시
            print(f"{i}. {failed['title'][:50]}... - {failed['reason']}")
        if len(failed_videos) > 10:
            print(f"... 외 {len(failed_videos)-10}개")
    
    # 실패 로그 저장
    if failed_videos:
        log_file = output_path / "failed_videos.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(failed_videos, f, ensure_ascii=False, indent=2)
        print(f"\n실패 로그 저장: {log_file}")
    
    return success_count, no_subtitle_count, failed_count

if __name__ == "__main__":
    success, no_sub, failed = download_subtitles()
