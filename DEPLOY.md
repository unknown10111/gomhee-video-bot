# 🚀 박곰희TV 영상 추천 봇 배포 가이드

가장 쉽고 무료로 사용할 수 있는 **Streamlit Cloud**를 이용한 배포 방법입니다.

## 1. 준비물
- GitHub 계정
- Streamlit Cloud 계정 (GitHub으로 로그인)

## 2. GitHub에 코드 올리기
1. GitHub에 새로운 Repository(저장소)를 만듭니다 (예: `gomhee-video-bot`).
2. 현재 프로젝트 폴더의 파일들을 해당 저장소에 업로드합니다.
   - **필수 파일**:
     - `app.py`
     - `requirements.txt`
     - `embedding_service.py`
     - `chunk_subtitles.py`
     - `data/` 폴더 전체 (특히 `chroma_db` 폴더가 꼭 있어야 검색이 됩니다!)

   > **주의**: `data/chroma_db` 폴더가 `.gitignore`에 포함되어 있다면 제거하고 올려주세요. 데이터베이스 파일이 있어야 배포된 곳에서도 검색이 가능합니다.

## 3. Streamlit Cloud 배포
1. [Streamlit Cloud](https://streamlit.io/cloud)에 접속하여 로그인합니다.
2. **"New app"** 버튼을 클릭합니다.
3. **"Use existing repo"**를 선택하고, 방금 만든 GitHub 저장소를 선택합니다.
4. 설정 확인:
   - **Repository**: `사용자ID/gomhee-video-bot`
   - **Branch**: `main` (또는 `master`)
   - **Main file path**: `app.py`
5. **"Deploy!"** 버튼을 클릭합니다.

## 4. 배포 완료
- 잠시 기다리면(약 2~3분) 배포가 완료되고, 전 세계 어디서나 접속 가능한 URL이 생성됩니다.
- 이제 스마트폰으로 접속해서 모바일 UI가 잘 나오는지 확인해보세요!

## 💡 팁
- **데이터 업데이트**: 새로운 영상을 추가하려면 로컬에서 데이터를 수집/임베딩한 후, `data/` 폴더를 다시 GitHub에 푸시(Push)하면 자동으로 재배포됩니다.
- **비공개 배포**: GitHub 저장소를 Private으로 만들면 앱도 특정 사용자에게만 공개할 수 있습니다.
