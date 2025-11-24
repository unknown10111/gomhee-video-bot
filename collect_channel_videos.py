"""
박곰희TV 채널에서 영상 목록을 수집하는 스크립트
yt-dlp를 사용하여 채널의 영상 메타데이터를 가져옵니다.
"""
import subprocess
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

def collect_channel_videos(channel_url, days_limit=365, max_videos=None):
    """
    YouTube 채널에서 영상 목록을 수집합니다.
    
    Args:
        channel_url: YouTube 채널 URL
        days_limit: 최근 며칠 이내의 영상만 수집 (기본: 365일)
        max_videos: 최대 수집 영상 개수 (None이면 제한 없음)
    
    Returns:
        영상 메타데이터 리스트
    """
    # 데이터 디렉토리 생성
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # yt-dlp 명령어 구성
    cmd = [
        "yt-dlp",
        "--flat-playlist",  # 영상을 다운로드하지 않고 메타데이터만 가져오기
        "--dump-json",      # JSON 형식으로 출력
        "--skip-download",  # 다운로드 스킵
        channel_url
    ]
    
    if max_videos:
        cmd.extend(["--playlist-end", str(max_videos)])
    
    print(f"채널에서 영상 목록을 수집합니다: {channel_url}")
    print(f"최근 {days_limit}일 이내의 영상만 수집합니다.")
    
    try:
        # yt-dlp 실행
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # 각 줄이 하나의 JSON 객체
        videos = []
        cutoff_date = datetime.now() - timedelta(days=days_limit)
        
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            try:
                video_data = json.loads(line)
                
                # 업로드 날짜 확인
                upload_date_str = video_data.get('upload_date')
                if upload_date_str:
                    upload_date = datetime.strptime(upload_date_str, '%Y%m%d')
                    
                    # 기간 필터링
                    if upload_date < cutoff_date:
                        continue
                
                # 필요한 정보만 추출
                video_info = {
                    'video_id': video_data.get('id'),
                    'title': video_data.get('title'),
                    'description': video_data.get('description', ''),
                    'upload_date': upload_date_str,
                    'url': f"https://www.youtube.com/watch?v={video_data.get('id')}",
                    'duration': video_data.get('duration'),
                    'view_count': video_data.get('view_count'),
                    'like_count': video_data.get('like_count'),
                }
                
                videos.append(video_info)
                print(f"✓ {video_info['title'][:50]}... ({upload_date_str})")
                
            except json.JSONDecodeError as e:
                print(f"JSON 파싱 오류: {e}")
                continue
        
        print(f"\n총 {len(videos)}개의 영상을 수집했습니다.")
        
        # JSON 파일로 저장
        output_file = data_dir / "videos_metadata.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)
        
        print(f"메타데이터 저장 완료: {output_file}")
        
        return videos
        
    except subprocess.CalledProcessError as e:
        print(f"yt-dlp 실행 오류: {e}")
        print(f"stderr: {e.stderr}")
        return []
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    # 박곰희TV 채널 URL
    channel_url = "https://www.youtube.com/@gomhee/videos"
    
    # 1년치 영상 수집
    videos = collect_channel_videos(
        channel_url=channel_url,
        days_limit=365,
        max_videos=None  # 제한 없음
    )
    
    if videos:
        print(f"\n{'='*60}")
        print(f"수집 완료!")
        print(f"총 영상 개수: {len(videos)}")
        print(f"첫 번째 영상: {videos[0]['title']}")
        print(f"마지막 영상: {videos[-1]['title']}")
        print(f"{'='*60}")
