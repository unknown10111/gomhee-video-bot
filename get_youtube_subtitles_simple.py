"""
youtube-transcript-api 라이브러리를 사용하여 YouTube 자막 가져오기
이 라이브러리는 공식적으로 YouTube 자막을 가져오는데 사용됩니다.
"""
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
except ImportError:
    print("youtube-transcript-api 라이브러리가 설치되지 않았습니다.")
    print("다음 명령어로 설치하세요: pip install youtube-transcript-api")
    exit(1)

def get_youtube_subtitles(video_id):
    """
    YouTube 비디오의 자막을 가져옵니다.
    """
    try:
        # 한국어 자막 가져오기 시도
        try:
            subtitle_data = YouTubeTranscriptApi.fetch(video_id, ['ko'])
            print(f"Fetching: Korean subtitles")
        except:
            # 한국어 자막이 없으면 사용 가능한 첫 번째 자막 가져오기
            print("Korean subtitles not found, trying to fetch available transcripts...")
            # 사용 가능한 자막 목록 가져오기
            available = YouTubeTranscriptApi.list(video_id)
            print(f"Available transcripts: {available}")
            subtitle_data = YouTubeTranscriptApi.fetch(video_id)
            print(f"Fetching: Default subtitles")
        
        return subtitle_data
        
    except TranscriptsDisabled:
        print("이 동영상은 자막이 비활성화되어 있습니다.")
        return None
    except NoTranscriptFound:
        print("이 동영상에는 자막이 없습니다.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    video_id = "REC2H8j2Bno"
    
    print(f"Fetching subtitles for video: {video_id}\n")
    subtitle_data = get_youtube_subtitles(video_id)
    
    if subtitle_data:
        print(f"\n{'='*60}")
        print(f"Total subtitle entries: {len(subtitle_data)}")
        print(f"{'='*60}\n")
        
        # 자막 출력
        for i, entry in enumerate(subtitle_data, 1):
            text = entry['text']
            start = entry['start']
            duration = entry['duration']
            print(f"{i:4d}. [{start:>7.2f}s] {text}")
        
        # 자막을 파일로 저장 (시간 정보 포함)
        output_file_with_time = f"subtitles_{video_id}_with_time.txt"
        with open(output_file_with_time, 'w', encoding='utf-8') as f:
            for entry in subtitle_data:
                text = entry['text']
                start = entry['start']
                duration = entry['duration']
                f.write(f"[{start:.2f}s - {start+duration:.2f}s] {text}\n")
        
        # 자막만 저장 (시간 정보 없이)
        output_file = f"subtitles_{video_id}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in subtitle_data:
                f.write(entry['text'] + '\n')
        
        print(f"\n{'='*60}")
        print(f"Subtitles saved to:")
        print(f"  - {output_file} (text only)")
        print(f"  - {output_file_with_time} (with timestamps)")
        print(f"{'='*60}")
    else:
        print("Failed to fetch subtitles")
