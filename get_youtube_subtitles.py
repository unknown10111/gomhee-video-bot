import requests
import re
import json
from urllib.parse import unquote
from xml.etree import ElementTree as ET

def get_youtube_subtitles(video_id):
    """
    YouTube 비디오의 자막을 가져옵니다.
    youtube-dl을 사용하지 않고 직접 YouTube API를 호출합니다.
    """
    # YouTube 페이지 HTML 가져오기
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching video page: {response.status_code}")
        return None
    
    html = response.text
    
    # ytInitialPlayerResponse에서 자막 정보 찾기
    patterns = [
        r'ytInitialPlayerResponse\s*=\s*({.+?});',
        r'"captions":\s*({.+?"playerCaptionsTracklistRenderer".+?})',
    ]
    
    player_response = None
    for pattern in patterns:
        match = re.search(pattern, html, re.DOTALL)
        if match:
            try:
                data = match.group(1)
                player_response = json.loads(data)
                break
            except json.JSONDecodeError as e:
                print(f"JSON decode error with pattern {pattern}: {e}")
                continue
    
    if not player_response:
        print("Could not find player response in page")
        return None
    
    # captions 정보 추출
    try:
        if 'captions' in player_response:
            captions_data = player_response['captions']
        else:
            # ytInitialPlayerResponse 전체를 파싱했을 경우
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
        
        # 한국어 자막 찾기 (우선순위: ko, ko-KR 등)
        korean_track = None
        for track in caption_tracks:
            if track.get('languageCode', '').startswith('ko'):
                korean_track = track
                break
        
        # 한국어가 없으면 첫 번째 자막 사용
        if not korean_track:
            korean_track = caption_tracks[0]
        
        base_url = korean_track.get('baseUrl')
        if not base_url:
            print("No subtitle URL found")
            return None
        
        lang_name = korean_track.get('name', {}).get('simpleText', 'Unknown')
        print(f"\nFetching subtitles: {lang_name}")
        print(f"Subtitle URL: {base_url[:100]}...")
        
        # 자막 XML 가져오기
        subtitle_response = requests.get(base_url, headers=headers)
        if subtitle_response.status_code != 200:
            print(f"Error fetching subtitles: {subtitle_response.status_code}")
            return None
        
        return subtitle_response.text
        
    except Exception as e:
        print(f"Error extracting captions: {e}")
        import traceback
        traceback.print_exc()
        return None

def parse_subtitle_xml(xml_content):
    """
    XML 형식의 자막을 파싱하여 텍스트로 변환합니다.
    """
    # <text> 태그에서 텍스트 추출
    text_pattern = r'<text[^>]*>(.*?)</text>'
    matches = re.findall(text_pattern, xml_content, re.DOTALL)
    
    subtitles = []
    for match in matches:
        # HTML 엔티티 디코딩
        text = match.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
        # 줄바꿈 태그 처리
        text = text.replace('\n', ' ').strip()
        if text:
            subtitles.append(text)
    
    return subtitles

if __name__ == "__main__":
    video_id = "REC2H8j2Bno"
    
    print(f"Fetching subtitles for video: {video_id}")
    xml_content = get_youtube_subtitles(video_id)
    
    if xml_content:
        subtitles = parse_subtitle_xml(xml_content)
        
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
