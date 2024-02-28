import asyncio
import re
from json import loads as loadjson
from pathlib import Path
from sys import version_info
from urllib.parse import unquote, urlparse
import streamlit as st
import aiohttp

# 사용자에게 상태 메시지를 표시하기 위한 Streamlit 컴포넌트 추가
progress_bar = st.progress(0)
status_text = st.empty()

async def queue_downloads(url):
    try:
        title = urlparse(url).query.split('volumeNo=')[1].split('&')[0]
        desired_path = Path.cwd() / title
        desired_path.mkdir(parents=False, exist_ok=True)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0'}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                text = await response.text()
                total_images = len(re.findall("data-linkdata=\'", text))  # 전체 이미지 수 계산
                current_image = 0  # 현재 다운로드된 이미지 수 초기화
                for item in text.split("data-linkdata=\'")[1:]:
                    linkdata = loadjson(item.split("\'>\n")[0])
                    if 'src' in linkdata:
                        picture_url = linkdata['src']
                        picture_id = unquote(urlparse(picture_url).path.split('/')[-1])
                        picture_name = re.sub('[<>:\"/|?*]', ' ', picture_id).strip()
                        picture_path = desired_path / picture_name
                        if not picture_path.is_file():
                            await download(session, picture_url, picture_path)
                            current_image += 1  # 이미지 다운로드 시 카운트 증가
                            # 다운로드 진행 상황 업데이트
                            progress_bar.progress(current_image / total_images)
                            status_text.text(f'Downloading... ({current_image}/{total_images})')
                    else:
                        # 사용자에게 오류 메시지 표시
                        status_text.text(f"Error: 'src' not found in link data: {linkdata}")
    except Exception as e:
        # 사용자에게 예외 처리 메시지 표시
        status_text.text(f"An error occurred: {str(e)}")

async def download(session, picture_url, picture_path):
    try:
        async with session.get(picture_url) as r:
            if r.status == 200:
                # 이미지 다운로드 및 파일 저장
                picture_path.write_bytes(await r.read())
                # st.write(f'Downloaded {picture_url}')  # 사용자에게 다운로드 완료 메시지 표시
            else:
                # 사용자에게 오류 메시지 표시
                st.write(f'Error {r.status} while getting request for {picture_url}')
    except Exception as e:
        # 사용자에게 예외 처리 메시지 표시
        st.write(f"An error occurred while downloading {picture_url}: {str(e)}")

def main():
    st.title("NAVER POST DOWNLOADER")
    post_url = st.text_input("네이버 포스트 URL을 입력하세요")
    if post_url:
        if st.button("다운로드"):
            # 다운로드가 시작되면 진행 상황을 리셋하고 메시지를 업데이트
            progress_bar.progress(0)
            status_text.text("Downloading...")
            asyncio.run(queue_downloads(post_url))

if __name__ == '__main__':
    assert version_info >= (3, 7), 'Script requires Python 3.7+.'
    main()
