# 홍보 영상 / 프로필 사진 만드는 도구

- `rec.html` : 녹화용 게임 사본 (자막 칸과 마지막 화면 포함, 순위는 오프라인)
- `record.py` : 게임을 가상 시계로 돌리며 1080x1920 30fps로 녹화 (`python3 record.py full`)
- `audio.py` : 녹화 때 기록한 이벤트 시각에 맞춰 배경음/효과음 합성
- `endcard.py` : 마지막 화면만 다시 찍기

필요한 것: Python 3, playwright, Pillow, numpy, ffmpeg, Chrome
합치기: `ffmpeg -i out/promo_silent.mp4 -i out/music.wav -map 0:v -map 1:a -c:v copy -c:a aac out/SPACE_XXX_shorts.mp4`
