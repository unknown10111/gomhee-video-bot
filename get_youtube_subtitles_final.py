"""
youtube-transcript-api 라이브러리를 사용하여 YouTube 자막 가져오기
올바른 API 사용법을 적용한 버전
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
        # API 인스턴스 생성
        api = YouTubeTranscriptApi()
        
        # 사용 가능한 자막 목록 가져오기
        transcript_list = api.list(video_id)
        
        print("Available transcripts:")
        for lang_code, transcript in transcript_list._manually_created_transcripts.items():
            print(f"  - {transcript.language} ({transcript.language_code}) [Manual]")
        for lang_code, transcript in transcript_list._generated_transcripts.items():
            print(f"  - {transcript.language} ({transcript.language_code}) [Auto-generated]")
        
        # 한국어 자막 찾기
        try:
            transcript = transcript_list.find_transcript(['ko'])
            print(f"\nFetching: {transcript.language} ({transcript.language_code})")
        except NoTranscriptFound:
            print("\n한국어 자막을 찾을 수 없습니다. 첫 번째 사용 가능한 자막을 사용합니다.")
            # 수동 자막 우선, 없으면 자동 생성 자막
            if transcript_list._manually_created_transcripts:
                lang_code = list(transcript_list._manually_created_transcripts.keys())[0]
                transcript = transcript_list._manually_created_transcripts[lang_code]
            else:
                lang_code = list(transcript_list._generated_transcripts.keys())[0]
                transcript = transcript_list._generated_transcripts[lang_code]
            print(f"Fetching: {transcript.language} ({transcript.language_code})")
        
        # 자막 데이터 가져오기
        subtitle_data = transcript.fetch()
        
        return subtitle_data
        
    except TranscriptsDisabled:
        print("이 동영상은 자막이 비활성화되어 있습니다.")
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
        
        # 자막 출력 (객체 속성 접근)
        for i, entry in enumerate(subtitle_data, 1):
            text = entry.text
            start = entry.start
            duration = entry.duration
            print(f"{i:4d}. [{start:>7.2f}s] {text}")
        
        # 자막을 파일로 저장 (시간 정보 포함)
        output_file_with_time = f"subtitles_{video_id}_with_time.txt"
        with open(output_file_with_time, 'w', encoding='utf-8') as f:
            for entry in subtitle_data:
                text = entry.text
                start = entry.start
                duration = entry.duration
                f.write(f"[{start:.2f}s - {start+duration:.2f}s] {text}\n")
        
        # 자막만 저장 (시간 정보 없이)
        output_file = f"subtitles_{video_id}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in subtitle_data:
                f.write(entry.text + '\n')
        
        print(f"\n{'='*60}")
        print(f"Subtitles saved to:")
        print(f"  - {output_file} (text only)")
        print(f"  - {output_file_with_time} (with timestamps)")
        print(f"{'='*60}")
    else:
        print("Failed to fetch subtitles")
