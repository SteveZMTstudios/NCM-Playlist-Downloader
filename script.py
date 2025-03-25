import sys, os, json, qrcode, time, pyncm, requests, re
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

def get_track_info(track_id, level):
    try:
        track_info_rsp = track.GetTrackDetail([track_id])
        track_info = track_info_rsp['songs'][0]
        track_id = track_info['id']
        track_name = track_info['name']
        artist_name = ', '.join(artist['name'] for artist in track_info['ar'])
        download_and_save_track(track_id, track_name, artist_name, level)
        print(f"歌曲 {track_name} 已保存到 downloads 文件夹中。")
    except Exception as e:
        print(f"获取歌曲信息时出错: {e}")

def download_and_save_track(track_id, track_name, artist_name, level):
    def make_safe_filename(filename):
        return re.sub(r'[\\/*?:"<>|]', "-", filename)

    try:
        url_info = track.GetTrackAudioV1(song_ids=[track_id], level=level, encodeType="flac")
        url = url_info['data'][0]['url']
        if url:
            response = requests.get(url, stream=True)
            # 检查响应状态码
            if response.status_code != 200:
                print(f"获取 URL 时出错: {response.status_code} - {response.text}")
                write_to_failed_list(track_id, track_name, artist_name, f"HTTP错误: {response.status_code}")
                return

            content_disposition = response.headers.get('content-disposition')
            if content_disposition:
                filename = content_disposition.split('filename=')[-1].strip('"')
            else:
                filename = f"{track_id}.flac"
            download_dir = "downloads"
            os.makedirs(download_dir, exist_ok=True)

            # 对文件名部分进行安全处理
            safe_filename = make_safe_filename(f"{track_name} - {artist_name}{os.path.splitext(filename)[1]}")
            safe_filepath = os.path.join(download_dir, safe_filename)
            with open(safe_filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"已下载: {safe_filename}")
        else:
            write_to_failed_list(track_id, track_name, artist_name, "无可用下载链接")
            print(f"无法下载 {track_name} - {artist_name}, 详情请查看failed_list.txt")
    except (KeyError, IndexError) as e:
        write_to_failed_list(track_id, track_name, artist_name, f"URL信息错误: {e}")
        print(f"访问曲目 {track_name} - {artist_name} 的URL信息时出错: {e}")
    except Exception as e:
        write_to_failed_list(track_id, track_name, artist_name, f"下载错误: {e}")
        print(f"下载歌曲时出错: {e}")

def write_to_failed_list(track_id, track_name, artist_name, reason):
    failed_list_path = "failed_list.txt"
    if not os.path.exists(failed_list_path):
        with open(failed_list_path, 'w', encoding='utf-8') as f:
            f.write("此处列举了下载失败的歌曲\n可能的原因：\n1.歌曲为单曲付费曲目 \n2.歌曲已下架 \n3.地区限制（如VPN） \n4.网络问题 \n5.VIP曲目但账号无VIP权限\n=== === === === === === === === === === === ===\n\n")
    
    # 追加失败信息
    with open(failed_list_path, 'a', encoding='utf-8') as f:
        f.write(f"ID: {track_id} - 歌曲: {track_name} - 艺术家: {artist_name} - 原因: {reason}\n")

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
    playlist_id = input("请输入歌单 ID (直接回车则输入单曲 ID): ")
    if not playlist_id:
        track_id = input("请输入歌曲 ID: ")

    # 询问用户选择音质
    level_input = input("请选择音质：exhigh(极高) / lossless(无损) / hires(高清) / jymaster(超清)，默认是 lossless: ")
    level = level_input if level_input in ['exhigh', 'lossless', 'hires', 'jymaster'] else 'lossless'
    print(f"使用音质: {level}，正在使用听歌API，不消耗VIP下载额度")
    if playlist_id:
        get_playlist_tracks_and_save_info(playlist_id, level)
    else:
        get_track_info(track_id, level)
    # 在程序结束前添加暂停效果
    input("按 Enter 键退出...")
