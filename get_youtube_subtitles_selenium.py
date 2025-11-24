"""
브라우저 자동화를 사용하여 YouTube 자막 가져오기
Selenium을 사용하여 실제 브라우저로 페이지에 접근
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
import re

def get_youtube_subtitles_with_browser(video_id):
    """
    Selenium을 사용하여 YouTube 비디오의 자막을 가져옵니다.
    """
    # Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 헤드리스 모드
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--lang=ko-KR')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 드라이버 초기화
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # YouTube 페이지 열기
        url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"Opening URL: {url}")
        driver.get(url)
        
        # 페이지 로딩 대기
        time.sleep(3)
        
        # 페이지 소스 가져오기
        page_source = driver.page_source
        
        # ytInitialPlayerResponse 찾기
        match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?});', page_source, re.DOTALL)
        
        if not match:
            print("Could not find player response")
            return None
        
        player_response = json.loads(match.group(1))
        
        # captions 정보 추출
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
        
        # URL에 fmt=json3 파라미터 추가
        if '?' in base_url:
            subtitle_url = base_url + '&fmt=json3'
        else:
            subtitle_url = base_url + '?fmt=json3'
        
        lang_name = korean_track.get('name', {}).get('simpleText', 'Unknown')
        print(f"\nFetching subtitles: {lang_name}")
        
        # 자막 URL로 이동
        driver.get(subtitle_url)
        time.sleep(2)
        
        # 페이지 본문 가져오기 (JSON 데이터)
        body = driver.find_element(By.TAG_NAME, 'body')
        json_text = body.text
        
        if not json_text:
            # pre 태그 시도
            try:
                pre = driver.find_element(By.TAG_NAME, 'pre')
                json_text = pre.text
            except:
                pass
        
        if json_text:
            return json.loads(json_text)
        else:
            print("Could not retrieve subtitle data")
            return None
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        driver.quit()

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
    json_data = get_youtube_subtitles_with_browser(video_id)
    
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
