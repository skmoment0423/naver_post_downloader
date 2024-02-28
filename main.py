import asyncio
import re
from json import loads as loadjson
from pathlib import Path
from sys import version_info
from urllib.parse import unquote, urlparse
import streamlit as st
import aiohttp

async def queue_downloads(url, download_folder):
    try:
        title = urlparse(url).query.split('volumeNo=')[1].split('&')[0]
        desired_path = Path(download_folder) / title  # 다운로드 폴더를 사용자가 지정한 폴더로 변경
        desired_path.mkdir(parents=False, exist_ok=True)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:70.0) Gecko/20100101 Firefox/70.0'}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                text = await response.text()
                for item in text.split("data-linkdata=\'")[1:]:
                    linkdata = loadjson(item.split("\'>\n")[0])
                    if 'src' in linkdata:
                        picture_url = linkdata['src']
                        picture_id = unquote(urlparse(picture_url).path.split('/')[-1])
                        picture_name = re.sub('[<>:\"/|?*]', ' ', picture_id).strip()
                        picture_path = desired_path / picture_name
                        if not picture_path.is_file():
                            await download(session, picture_url, picture_path)
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")

async def download(session, picture_url, picture_path):
    try:
        async with session.get(picture_url) as r:
            if r.status == 200:
                # 이미지를 사용자의 로컬 PC의 Downloads 폴더에 저장
                with open(picture_path, 'wb') as f:
                    f.write(await r.read())
            else:
                st.error(f'Error {r.status} while getting request for {picture_url}')
    except Exception as e:
        st.error(f"An error occurred while downloading {picture_url}: {str(e)}")

def main():
    st.title("NAVER POST DOWNLOADER")
    post_url = st.text_input("네이버 포스트 URL을 입력하세요")
    download_folder = st.text_input("다운로드할 폴더 경로를 입력하세요", value=str(Path.home() / "Downloads"))
    if post_url and st.button("다운로드"):
        asyncio.run(queue_downloads(post_url, download_folder))

if __name__ == '__main__':
    assert version_info >= (3, 7), 'Script requires Python 3.7+.'
    main()
