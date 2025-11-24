"""
YouTube 자막을 가져오는 개선된 버전
requests 세션을 사용하고 쿠키를 포함하여 더 실제 브라우저처럼 동작
"""
import requests
import re
import json
from urllib.parse import unquote, parse_qs, urlparse

def get_youtube_subtitles(video_id):
    """
    YouTube 비디오의 자막을 가져옵니다.
    """
    session = requests.Session()
    
    # 먼저 메인 페이지 방문하여 쿠키 설정
    session.get('https://www.youtube.com')
    
    # YouTube 페이지 HTML 가져오기
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching video page: {response.status_code}")
        return None
    
    html = response.text
    
    # ytInitialPlayerResponse 찾기
    match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?});', html, re.DOTALL)
    
    if not match:
        print("Could not find player response")
        # HTML을 파일로 저장하여 디버깅
        with open('youtube_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Saved page HTML to youtube_page.html for debugging")
        return None
    
    try:
        player_response = json.loads(match.group(1))
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return None
    
    # captions 정보 추출
    try:
        captions_data = player_response.get('captions', {})
        caption_tracks = captions_data.get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
        
        if not caption_tracks:
            print("No caption tracks available")
            return None
        
        print(f"\nAvailable captions:")
        for i, track in enumerate(caption_tracks):
            lang_code = track.get('languageCode', 'unknown')
            lang_name = track.get('name', {}).get('simpleText', 'Unknown')
            print(f"{i}: {lang_name} ({lang_code})")
        
        # 한국어 자막 찾기
        korean_track = None
        for track in caption_tracks:
            if track.get('languageCode', '').startswith('ko'):
                korean_track = track
                break
        
        if not korean_track:
            korean_track = caption_tracks[0]
        
        base_url = korean_track.get('baseUrl')
        if not base_url:
            print("No subtitle URL found")
            return None
        
        # URL에 fmt=json3 파라미터 추가 (JSON 형식으로 가져오기)
        if '?' in base_url:
            subtitle_url = base_url + '&fmt=json3'
        else:
            subtitle_url = base_url + '?fmt=json3'
        
        lang_name = korean_track.get('name', {}).get('simpleText', 'Unknown')
        print(f"\nFetching subtitles: {lang_name}")
        print(f"Subtitle URL: {subtitle_url[:150]}...")
        
        # 자막 데이터 가져오기
        subtitle_response = session.get(subtitle_url, headers=headers)
        if subtitle_response.status_code != 200:
            print(f"Error fetching subtitles: {subtitle_response.status_code}")
            print(f"Response: {subtitle_response.text[:200]}")
            return None
        
        return subtitle_response.json()
        
    except Exception as e:
        print(f"Error extracting captions: {e}")
        import traceback
        traceback.print_exc()
        return None

def parse_subtitle_json(json_data):
    """
    JSON 형식의 자막을 파싱하여 텍스트로 변환합니다.
    """
    events = json_data.get('events', [])
    
    subtitles = []
    for event in events:
        segs = event.get('segs', [])
        if segs:
            text = ''.join([seg.get('utf8', '') for seg in segs])
            text = text.strip()
            if text:
                subtitles.append(text)
    
    return subtitles

if __name__ == "__main__":
    video_id = "REC2H8j2Bno"
    
    print(f"Fetching subtitles for video: {video_id}")
    json_data = get_youtube_subtitles(video_id)
    
    if json_data:
        subtitles = parse_subtitle_json(json_data)
        
        print(f"\n{'='*60}")
        print(f"Total subtitle lines: {len(subtitles)}")
        print(f"{'='*60}\n")
        
        # 자막 출력
        for i, text in enumerate(subtitles, 1):
            print(f"{i:4d}. {text}")
        
        # 자막을 파일로 저장
        output_file = f"subtitles_{video_id}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            for text in subtitles:
                f.write(text + '\n')
        
        print(f"\n{'='*60}")
        print(f"Subtitles saved to: {output_file}")
        print(f"{'='*60}")
    else:
        print("Failed to fetch subtitles")
