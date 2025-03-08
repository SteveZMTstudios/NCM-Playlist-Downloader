import sys
import os
import json
import qrcode
import time
import pyncm
import requests
from pyncm.apis import playlist, track, login

def get_qrcode():
    # 生成用于二维码登录的唯一密钥
    uuid = login.LoginQrcodeUnikey()["unikey"]
    url = f"https://music.163.com/login?codekey={uuid}"
    img = qrcode.make(url)
    img.save('ncm.png')
    print("二维码已保存为'ncm.png'，请使用网易云音乐APP扫码登录。")
    while True:
        rsp = login.LoginQrcodeCheck(uuid)
        if rsp["code"] == 803:
            session = pyncm.GetCurrentSession()
            login.WriteLoginInfo(login.GetCurrentLoginStatus(), session)
            print("登录成功")
            return session
        elif rsp["code"] == 800:
            print("二维码已过期，请重新尝试。")
            break
        time.sleep(1)

def save_session_to_file(session, filename='session.json'):
    with open(filename, 'w') as f:
        session_data = pyncm.DumpSessionAsString(session)
        json.dump(session_data, f)
    print("会话已保存到文件。")

def get_playlist_tracks_and_save_info(playlist_id, level):
    try:
        tracks = playlist.GetPlaylistAllTracks(playlist_id)
        if not os.path.exists('downloads'):
            os.makedirs('downloads')
        # 将歌单信息保存到文件
        playlist_info_filename = f'downloads/playlist_{playlist_id}_info.txt'
        with open(playlist_info_filename, 'w', encoding='utf-8') as f:
            for track_info in tracks['songs']:
                track_id = track_info['id']
                track_name = track_info['name']
                artist_name = ', '.join(artist['name'] for artist in track_info['ar'])
                f.write(f"{track_id} - {track_name} - {artist_name}\n")
        print(f"歌单信息已保存到 {playlist_info_filename}")
        # 下载每首曲目
        for track_info in tracks['songs']:
            track_id = track_info['id']
            track_name = track_info['name']
            artist_name = ', '.join(artist['name'] for artist in track_info['ar'])
            download_and_save_track(track_id, track_name, artist_name, level)
        print("所有操作已完成，歌曲已下载并保存到 downloads 文件夹中。")
    except Exception as e:
        print(f"获取歌单列表或下载歌曲时出错: {e}")

def download_and_save_track(track_id, track_name, artist_name, level):
    try:
        url_info = track.GetTrackAudioV1(song_ids=[track_id], level=level, encodeType="flac")
        url = url_info['data'][0]['url']
        if url:
            response = requests.get(url, stream=True)
            # 检查响应状态码
            if response.status_code != 200:
                print(f"获取 URL 时出错: {response.status_code} - {response.text}")
                return
            content_disposition = response.headers.get('content-disposition')
            if content_disposition:
                filename = content_disposition.split('filename=')[-1].strip('"')
            else:
                filename = f"{track_id}.flac"
            # 创建包含曲名和艺术家的新文件名
            new_filename = f"downloads/{track_name} - {artist_name}{os.path.splitext(filename)[1]}"
            # 确保 downloads 目录存在
            os.makedirs(os.path.dirname(new_filename), exist_ok=True)
            # 将响应内容写入文件
            with open(new_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"已下载: {new_filename}")
        else:
            print(f"无法下载 {track_name} - {artist_name}，可能需要更高的VIP。")
    except (KeyError, IndexError) as e:
        print(f"访问曲目 {track_name} - {artist_name} 的URL信息时出错: {e}")
    except Exception as e:
        print(f"下载歌曲时出错: {e}")

def load_session_from_file(filename='session.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            session_data = json.load(f)
        session = pyncm.LoadSessionFromString(session_data)
        pyncm.SetCurrentSession(session)
        print("会话已从文件加载。")
        return session
    else:
        return None

if __name__ == "__main__":
    session = load_session_from_file()
    if session:
        print("使用保存的会话登录。")
    else:
        try:
            session = get_qrcode()
            if session:
                save_session_to_file(session)
        except Exception as e:
            print(e)
            sys.exit(1)
    playlist_id = input("请输入歌单 ID: ")
    # 询问用户选择音质
    level_input = input("请选择音质：exhigh(极高) / lossless(无损) / hires(高清) / jymaster(超清)，默认是 lossless: ")
    level = level_input if level_input in ['exhigh', 'lossless', 'hires', 'jymaster'] else 'lossless'
    print(f"使用音质: {level}，正在使用听歌API，不消耗VIP下载额度")
    get_playlist_tracks_and_save_info(playlist_id, level)
    # 在程序结束前添加暂停效果
    input("按 Enter 键退出...")
