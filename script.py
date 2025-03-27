import sys, os, json, qrcode, time, pyncm, requests, re, platform, subprocess
from pyncm.apis import playlist, track, login

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=False)
    COLORAMA_INSTALLED = True
except ImportError:
    COLORAMA_INSTALLED = False
    if platform.system() == 'Windows':
        os.system('pip install colorama')
if platform.system() == 'Windows':
        os.system('') # init cmd
import mutagen
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TRCK, TDRC
from mutagen.flac import FLAC, Picture
from PIL import Image
from io import BytesIO
MUTAGEN_INSTALLED = True

def get_qrcode():
    uuid = login.LoginQrcodeUnikey()["unikey"]
    url = f"https://music.163.com/login?codekey={uuid}"
    img = qrcode.make(url)
    img.save('ncm.png')
    print("\033[32m✓ \033[0m二维码已保存为'ncm.png'，请使用网易云音乐APP扫码登录。")
    
    try:
        open_image('ncm.png')
    except Exception as e:
        print(f"{e}，请手动打开ncm.png文件")
    
    while True:
        rsp = login.LoginQrcodeCheck(uuid)
        if rsp["code"] == 803:
            session = pyncm.GetCurrentSession()
            login.WriteLoginInfo(login.GetCurrentLoginStatus(), session)
            print("\033[32m✓ \033[0m登录成功")
            return session
        elif rsp["code"] == 800:
            print("  二维码已过期，请重新尝试。")
            break
        time.sleep(1)

def open_image(image_path):
    system = platform.system()
    
    if system == 'Windows':
        os.startfile(image_path)
    elif system == 'Darwin':  # macOS
        subprocess.call(['open', image_path])
    else:  # Linux和其他系统
        viewers = ['xdg-open', 'display', 'eog', 'ristretto', 'feh', 'gpicview']
        for viewer in viewers:
            try:
                subprocess.call([viewer, image_path])
                return  
            except (FileNotFoundError, subprocess.SubprocessError):
                continue
        raise Exception("找不到合适的图片查看器")

def save_session_to_file(session, filename='session.json'):
    with open(filename, 'w') as f:
        session_data = pyncm.DumpSessionAsString(session)
        json.dump(session_data, f)
    print("\033[32m✓ \033[0m会话已保存。")

def parse_lrc(lrc_content):
    if not lrc_content:
        return []
    
    # 匹配时间戳和歌词内容
    pattern = r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)'
    lyrics = []
    
    for line in lrc_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            minutes, seconds, milliseconds, text = match.groups()
            # 将时间转换为秒
            time_seconds = int(minutes) * 60 + int(seconds) + int(milliseconds.ljust(3, '0')) / 1000
            lyrics.append((time_seconds, text))
    
    return sorted(lyrics, key=lambda x: x[0])

def merge_lyrics(original_lyrics, translated_lyrics, song_duration=None):
    if not translated_lyrics:
        return original_lyrics
    
    trans_dict = {time: text for time, text in translated_lyrics}
    
    merged = []
    for i, (time, text) in enumerate(original_lyrics):
        merged.append((time, text))
        
        if time in trans_dict and trans_dict[time].strip():
            if i + 1 >= len(original_lyrics) and song_duration:
                trans_time = song_duration + 0.5
            elif i + 1 < len(original_lyrics):
                next_time = original_lyrics[i + 1][0]
                trans_time = next_time - 0.01
            else:
                trans_time = time + 0.5
            
            merged.append((trans_time, trans_dict[time]))
    
    return sorted(merged, key=lambda x: x[0])

def format_lrc_line(time_seconds, text):
    minutes = int(time_seconds // 60)
    seconds = int(time_seconds % 60)
    milliseconds = int((time_seconds % 1) * 100)
    
    return f"[{minutes:02d}:{seconds:02d}.{milliseconds:02d}]{text}"

def save_lyrics_as_lrc(lyrics, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        for time, text in lyrics:
            f.write(format_lrc_line(time, text) + '\n')
    return file_path

def process_lyrics(track_id, track_name, artist_name, output_option, download_path, audio_file_path=None):
    try:
        # 获取歌词信息
        lyric_data = track.GetTrackLyrics(track_id)
        
        if lyric_data['code'] != 200 or 'lrc' not in lyric_data:
            print(f"\033[33m! 无法获取歌词: {track_name}\033[0m\x1b[K")
            return False, None
        
        track_detail = track.GetTrackDetail([track_id])
        song_duration = None
        if track_detail and 'songs' in track_detail and track_detail['songs']:
            song_duration = track_detail['songs'][0].get('dt', 0) / 1000
        original_lyrics = parse_lrc(lyric_data['lrc']['lyric'])
        translated_lyrics = []
        if 'tlyric' in lyric_data and lyric_data['tlyric']['lyric']:
            translated_lyrics = parse_lrc(lyric_data['tlyric']['lyric'])
        
        merged_lyrics = merge_lyrics(original_lyrics, translated_lyrics, song_duration)
        
        if not merged_lyrics:
            print(f"\033[33m! 未找到有效歌词: {track_name}\033[0m\x1b[K")
            return False, None
        
        # 根据用户选择，输出歌词
        if output_option == 'lrc' or (output_option == 'both' and download_path):
            safe_artist_name = re.sub(r'[\\/*?:"<>|]', "-", artist_name)
            safe_track_name = re.sub(r'[\\/*?:"<>|]', "-", track_name)
            lrc_path = os.path.join(download_path, f"{safe_track_name} - {safe_artist_name}.lrc")
            save_lyrics_as_lrc(merged_lyrics, lrc_path)
            print(f"\033[32m✓ \033[0m歌词已保存到 {lrc_path}\x1b[K")
        
        if (output_option == 'metadata' or output_option == 'both') and audio_file_path:
            lrc_content = '\n'.join([format_lrc_line(time, text) for time, text in merged_lyrics])
            
            return True, lrc_content
        
        return True, None
        
    except Exception as e:
        print(f"\033[33m! 处理歌词时出错: {e}\033[0m\x1b[K")
        return False, None

def add_metadata_to_audio(file_path, track_info, lyrics_content=None):
    if not MUTAGEN_INSTALLED:
        print("\033[33m! 未安装mutagen库，跳过添加元数据\033[0m")
        return
    
    try:
        file_ext = os.path.splitext(file_path)[1].lower()
        
        album_pic_url = track_info.get('al', {}).get('picUrl')
        album_pic_data = None
        if album_pic_url:
            response = requests.get(album_pic_url)
            if response.status_code == 200:
                album_pic_data = response.content
        
        title = track_info.get('name', '')
        artist = ', '.join(artist['name'] for artist in track_info.get('ar', []))
        album = track_info.get('al', {}).get('name', '')
        track_number = str(track_info.get('no', '0'))
        release_time = track_info.get('publishTime', 0)
        if release_time > 0:
            # 转换时间戳为年份
            release_year = time.strftime('%Y', time.localtime(release_time / 1000))
        else:
            release_year = ''
        
        if file_ext == '.mp3':
            try:
                audio = ID3(file_path)
            except:
                audio = ID3()
            
            # 标题
            audio['TIT2'] = TIT2(encoding=3, text=title)
            # 艺术家
            audio['TPE1'] = TPE1(encoding=3, text=artist)
            # 专辑
            audio['TALB'] = TALB(encoding=3, text=album)
            # 曲目号
            audio['TRCK'] = TRCK(encoding=3, text=track_number)
            # 年份
            if release_year:
                audio['TDRC'] = TDRC(encoding=3, text=release_year)
            
            # 专辑封面
            if album_pic_data:
                audio['APIC'] = APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,  # 封面图片
                    desc='Cover',
                    data=album_pic_data
                )
            
            # 歌词
            if lyrics_content:
                from mutagen.id3 import USLT
                audio['USLT'] = USLT(encoding=3, lang='eng', desc='', text=lyrics_content)
            
            audio.save(file_path)
            
        elif file_ext == '.flac':
            audio = FLAC(file_path)
            
            audio['TITLE'] = title
            audio['ARTIST'] = artist
            audio['ALBUM'] = album
            audio['TRACKNUMBER'] = track_number
            if release_year:
                audio['DATE'] = release_year
            
            # 歌词
            if lyrics_content:
                audio['LYRICS'] = lyrics_content
            
            # 专辑封面
            if album_pic_data:
                image = Picture()
                image.type = 3  # 封面图片
                image.mime = 'image/jpeg'
                image.desc = 'Cover'
                image.data = album_pic_data
                
                img = Image.open(BytesIO(album_pic_data))
                image.width, image.height = img.size
                image.depth = 24  # 位彩色
                
                audio.add_picture(image)
            
            audio.save()

        print(f"\033[32m✓ \033[0m已为 {os.path.basename(file_path)} 添加元数据\x1b[K")
    except Exception as e:
        print(f"\033[33m! 添加元数据时出错: {e}\033[0m\x1b[K")

def normalize_path(path):
    expanded_path = os.path.expanduser(path)
    normalized_path = os.path.normpath(expanded_path)
    if not os.path.exists(normalized_path):
        try:
            os.makedirs(normalized_path)
            print(f"\033[32m✓ \033[0m创建目录: {normalized_path}")
        except Exception as e:
            print(f"\033[31m× 创建目录失败: {e}\033[0m")
            default_path = os.path.join(os.getcwd(), "downloads")
            os.makedirs(default_path, exist_ok=True)
            print(f"\033[33m! 将使用默认下载路径: {default_path}\033[0m")
            return default_path
    return normalized_path

def get_playlist_tracks_and_save_info(playlist_id, level, download_path):
    try:
        tracks = playlist.GetPlaylistAllTracks(playlist_id)
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        playlist_info_filename = os.path.join(download_path, f'playlist_{playlist_id}_info.txt')
        with open(playlist_info_filename, 'w', encoding='utf-8') as f:
            for track_info in tracks['songs']:
                track_id = track_info['id']
                track_name = track_info['name']
                artist_name = ', '.join(artist['name'] for artist in track_info['ar'])
                f.write(f"{track_id} - {track_name} - {artist_name}\n")
        print(f"\033[32m✓ \033[0m歌单信息已保存到 {playlist_info_filename}")
        total_tracks = len(tracks['songs'])
        for index, track_info in enumerate(tracks['songs'], start=1):
            track_id = track_info['id']
            track_name = track_info['name']
            artist_name = ', '.join(artist['name'] for artist in track_info['ar'])
            download_and_save_track(track_id, track_name, artist_name, level, download_path, track_info, index, total_tracks)
        print("==========================================================================\x1b[K")
        print(f"\033[32m✓ 操作已完成，歌曲已下载并保存到 \033[34m{download_path}\033[32m 文件夹中。\033[0m\x1b[K")
    except Exception as e:
        print(f"\033[31m× 获取歌单列表或下载歌曲时出错: {e}\033[0m")

def get_track_info(track_id, level, download_path):
    try:
        track_info_rsp = track.GetTrackDetail([track_id])
        track_info = track_info_rsp['songs'][0]
        track_id = track_info['id']
        track_name = track_info['name']
        artist_name = ', '.join(artist['name'] for artist in track_info['ar'])
        download_and_save_track(track_id, track_name, artist_name, level, download_path, track_info, 1, 1)
        print(f"\033[32m✓ \033[0m歌曲 {track_name} 已保存到 {download_path} 文件夹中。\x1b[K")
    except Exception as e:
        print(f"\033[31m! 获取歌曲信息时出错: {e}\033[0m")

def download_and_save_track(track_id, track_name, artist_name, level, download_path, track_info=None, index=None, total=None):
    def make_safe_filename(filename):
        return re.sub(r'[\\/*?:"<>|]', "-", filename)

    try:
        url_info = track.GetTrackAudioV1(song_ids=[track_id], level=level, encodeType="flac")
        url = url_info['data'][0]['url']
        if url:
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                print(f"\033[31m×获取 URL 时出错: {response.status_code} - {response.text}\033[0m")
                write_to_failed_list(track_id, track_name, artist_name, f"HTTP错误: {response.status_code}", download_path)
                return

            content_disposition = response.headers.get('content-disposition')
            if content_disposition:
                filename = content_disposition.split('filename=')[-1].strip('"')
            else:
                filename = f"{track_id}.flac"
            os.makedirs(download_path, exist_ok=True)

            safe_filename = make_safe_filename(f"{track_name} - {artist_name}{os.path.splitext(filename)[1]}")
            safe_filepath = os.path.join(download_path, safe_filename)
            
            file_size = int(response.headers.get('content-length', 0))
            progress_status = ""
            if index is not None and total is not None:
                progress_status = f"[{index}/{total}] "
            print("==========================================================================\x1b[K" + f"\n\033[34m  {progress_status}正在下载: {safe_filename}\033[0m\x1b[K")
            
            downloaded = 0
            progress_bar_length = 35
            speed = 0  
            
            with open(safe_filepath, 'wb') as f:
                start_time = time.time()
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if file_size > 0:
                            percent = downloaded / file_size
                            bar_filled = int(progress_bar_length * percent)
                            bar = '\033[32m█' * bar_filled + '\033[0m░' * (progress_bar_length - bar_filled)
                            
                            elapsed_time = time.time() - start_time
                            if elapsed_time > 0:
                                speed = downloaded / elapsed_time / 1024  # KB/s
                            
                            sys.stdout.write(f"\r|{bar}| {percent*100:.1f}% {downloaded/1024/1024:.2f}MB/{file_size/1024/1024:.2f}MB {speed:.1f}KB/s")
                            sys.stdout.flush()
            
            sys.stdout.write("\r\033[2A\033[K")  
            print(f"\033[32m✓ 已下载: \033[0m{safe_filename}\x1b[K")
            
            if not track_info and url_info['data'][0].get('id'):
                try:
                    track_detail = track.GetTrackDetail([url_info['data'][0]['id']])
                    if track_detail and 'songs' in track_detail and track_detail['songs']:
                        track_info = track_detail['songs'][0]
                except Exception as e:
                    print(f"\033[33m! 获取曲目详情失败: {e}\033[0m\x1b[K")
            
            # 处理歌词
            lyrics_success, lyrics_content = process_lyrics(
                track_id, track_name, artist_name, 
                lyrics_option, download_path, safe_filepath
            )
            
            # 添加元数据
            if track_info:
                add_metadata_to_audio(safe_filepath, track_info, lyrics_content if lyrics_success else None)
            else:
                print("\033[33m! 无法添加元数据: 缺少曲目信息\033[0m\x1b[K")
                
        else:
            sys.stdout.write("\r\033[1A\033[K")  
            write_to_failed_list(track_id, track_name, artist_name, "无可用下载链接", download_path)
            print(f"\033[31m! 无法下载 {track_name} - {artist_name}, 详情请查看failed_list.txt\033[0m\x1b[K")
    except (KeyError, IndexError) as e:
        sys.stdout.write("\r\033[1A\033[K")  
        write_to_failed_list(track_id, track_name, artist_name, f"URL信息错误: {e}", download_path)
        print(f"\033[31m! 访问曲目 {track_name} - {artist_name} 的URL信息时出错: {e}\033[0m\x1b[K")
    except Exception as e:
        sys.stdout.write("\r\033[1A\033[K")  
        write_to_failed_list(track_id, track_name, artist_name, f"下载错误: {e}", download_path)
        print(f"\033[31m! 下载歌曲时出错: {e}\033[0m\x1b[K")

def write_to_failed_list(track_id, track_name, artist_name, reason, download_path):
    failed_list_path = os.path.join(download_path, "failed_list.txt")
    if not os.path.exists(failed_list_path):
        with open(failed_list_path, 'w', encoding='utf-8') as f:
            f.write("此处列举了下载失败的歌曲\n可能的原因：\n1.歌曲为单曲付费曲目 \n2.歌曲已下架 \n3.地区限制（如VPN） \n4.网络问题 \n5.VIP曲目但账号无VIP权限\n=== === === === === === === === === === === ===\n\n")
    
    with open(failed_list_path, 'a', encoding='utf-8') as f:
        f.write(f"ID: {track_id} - 歌曲: {track_name} - 艺术家: {artist_name} - 原因: {reason}\n")

def load_session_from_file(filename='session.json'):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            session_data = json.load(f)
        session = pyncm.LoadSessionFromString(session_data)
        pyncm.SetCurrentSession(session)
        print("\033[32m✓ \033[0m会话已从文件加载。")
        return session
    else:
        return None

if __name__ == "__main__":
    print(r""" __  __  ____                 ____    ___                     ___               __      
/\ \/\ \/\  _`\   /'\_/`\    /\  _`\ /\_ \                   /\_ \   __        /\ \__   
\ \ `\\ \ \ \/\_\/\      \   \ \ \L\ \//\ \      __    __  __\//\ \ /\_\    ___\ \ ,_\  
 \ \ , ` \ \ \/_/\ \ \__\ \   \ \ ,__/ \ \ \   /'__`\ /\ \/\ \ \ \ \\/\ \  /',__\ \ \/  
  \ \ \`\ \ \ \L\ \ \ \_/\ \   \ \ \/   \_\ \_/\ \L\.\\ \ \_\ \ \_\ \\ \ \/\__, `\ \ \_ 
   \ \_\ \_\ \____/\ \_\\ \_\   \ \_\   /\____\ \__/.\_\/`____ \/\____\ \_\/\____/\ \__\
    \/_/\/_/\/___/  \/_/ \/_/    \/_/   \/____/\/__/\/_/`/___/> \/____/\/_/\/___/  \/__/
                                                           /\___/                       
                                                           \/__/                        
 ____                              ___                       __                         
/\  _`\                           /\_ \                     /\ \                        
\ \ \/\ \   ___   __  __  __   ___\//\ \     ___     __     \_\ \     __  _ __          
 \ \ \ \ \ / __`\/\ \/\ \/\ \/' _ `\\ \ \   / __`\ /'__`\   /'_` \  /'__`/\`'__\        
  \ \ \_\ /\ \L\ \ \ \_/ \_/ /\ \/\ \\_\ \_/\ \L\ /\ \L\.\_/\ \L\ \/\  __\ \ \/         
   \ \____\ \____/\ \___x___/\ \_\ \_/\____\ \____\ \__/.\_\ \___,_\ \____\ \_\         
    \/___/ \/___/  \/__//__/  \/_/\/_\/____/\/___/ \/__/\/_/\/__,_ /\/____/\/_/         
                                                  Netease Cloud Music Playlist Downloader""")
     
    session = load_session_from_file()
    if session:
        print("  使用保存的会话登录。")
    else:
        try:
            session = get_qrcode()
            if session:
                save_session_to_file(session)
        except Exception as e:
            print(e)
            sys.exit(1)

    default_path = os.path.join(os.getcwd(), "downloads")
    download_path_input = input(f"  请输入下载路径或拖拽文件夹至此 (默认: {default_path}) \033[32m> \033[0m\033[94m")
    download_path = normalize_path(download_path_input) if download_path_input else default_path
    print(f"\033[0m  下载路径: \033[94m{download_path}\033[0m")
    
    print("\033[94mi 有关于歌单 ID 和单曲 ID 的说明，请参阅 https://github.com/padoru233/NCM-Playlist-Downloader/blob/main/README.md\033[0m")

    playlist_id = input("  请输入歌单 ID (直接回车则输入单曲 ID) \033[32m> \033[0m\033[94m")
    if not playlist_id:
        track_id = input("\033[0m  请输入歌曲 ID \033[32m> \033[0m\033[94m")
    lyrics_input = input("  请选择歌词处理方式: lrc(保存为lrc文件) / metadata(嵌入元数据) / both(两者都要) / none(不要歌词)，默认是 lrc \033[32m> \033[0m\033[94m")
    lyrics_option = lyrics_input if lyrics_input in ['lrc', 'metadata', 'both', 'none'] else 'lrc'
    print(f"\033[0m  歌词处理方式: \033[94m{lyrics_option}")
    level_input = input("\033[0m  请选择音质：exhigh(极高) / lossless(无损) / hires(高清) / jymaster(超清)，默认是 lossless \033[32m> \033[0m\033[94m")
    level = level_input if level_input in ['exhigh', 'lossless', 'hires', 'jymaster'] else 'lossless'
    print(f"\033[0m  使用音质: \033[94m{level}\033[0m==========================================================================\n\033[94m  开始下载...\n\033[32m✓ 正在使用听歌API，不消耗VIP下载额度\033[0m")
    if playlist_id:
        get_playlist_tracks_and_save_info(playlist_id, level, download_path)
    else:
        get_track_info(track_id, level, download_path)

