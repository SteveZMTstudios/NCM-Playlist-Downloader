import sys, os, json, qrcode, time, pyncm, requests, re, platform, subprocess, shutil
from pyncm.apis import playlist, track, login
import functools
import threading
from requests.exceptions import Timeout, ConnectionError, RequestException
import time
DEBUG = False
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
from mutagen import File as MutagenFile
from PIL import Image
from io import BytesIO
MUTAGEN_INSTALLED = True
USER_INFO_CACHE = {'nickname': None, 'user_id': None, 'vip': None}

def get_terminal_size():
    try:
        columns, lines = shutil.get_terminal_size()
        return columns, lines
    except shutil.Error:
        try:
            size = os.get_terminal_size()
            return size.columns, size.lines
        except (AttributeError, ImportError):
            raise
    except (AttributeError, ImportError, OSError):
        # 尝试其他方法
        try:
            # Unix/Linux/MacOS
            if platform.system() != 'Windows':
                import fcntl, termios, struct
                fd = sys.stdin.fileno()
                hw = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
                return hw[1], hw[0]
            else:
                # Windows
                from ctypes import windll, create_string_buffer
                h = windll.kernel32.GetStdHandle(-12)  # stderr
                buf = create_string_buffer(22)
                windll.kernel32.GetConsoleScreenBufferInfo(h, buf)
                left, top, right, bottom = struct.unpack('hhhhHhhhhhh', buf.raw)[5:9]
                return right - left + 1, bottom - top + 1
        except:
            # 默认值
            return 80, 24

def retry_with_timeout(timeout=30, retry_times=2, operation_name="操作"):
    """通用超时重试装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            last_error = None
            while retries <= retry_times:
                try:
                    result = func(*args, **kwargs)
                    return result, None
                except (Timeout, ConnectionError, RequestException) as e:
                    retries += 1
                    last_error = e
                    if retries <= retry_times:
                        print(f"\33[33m! {operation_name}超时，正在重试 ({retries}/{retry_times})...\33[0m\x1b[K")
                    else:
                        print(f"\33[31m× {operation_name}多次超时，放弃尝试。\33[0m\x1b[K")
                        break
            return None, last_error
        return wrapper
    return decorator

def get_qrcode():
    """
    提供三种登录方式选择：
    1) pyncm 直接扫码（复用原实现）
    2) 打开浏览器扫码登录（占位，未实现）
    3) 手机短信/账号密码登录
    返回已登录的 session 或 None。
    """
    try:
        print("\n  请选择登录方式：")
        print("  \33[36m[1]\33[0m \33[9mpyncm 直接扫码登录\33[0m \t\33[2m上游接口已失效，无法使用\33[0m")
        print("  \33[36m[2]\33[0m \33[1m打开浏览器扫码登录\33[0m \t\33[2m适用于桌面设备，需要外部浏览器（推荐）\33[0m")
        print("  \33[36m[3]\33[0m 手机短信/账号密码登录 \t\33[2m本地终端实现\33[0m" )
        print("  \33[36m[4]\33[0m 匿名登录 \t\t\t\33[2m创建随机凭据，不推荐\33[0m")
        choice = input("  请选择 (默认 2)\33[36m > \33[0m").strip() or "2"

        if choice == "1":
            # 复用原有 pyncm 扫码登录逻辑（简化并带轮询与超时）
            try:
                print("\33[33m! 使用 pyncm 直接扫码登录已确认因接口过时封堵，您仍要尝试吗？\33[0m")
                print("  [0] 取消  [9] 继续")
                confirm = input("  请输入您的选择 > ").strip()
                if confirm == "9":
                    print("\33[33m! 正在尝试 pyncm 直接扫码登录...\33[0m")
                else:
                    print("\33[31m× 已取消 pyncm 直接扫码登录。\33[0m")
                    return get_qrcode()
                    
                uuid_rsp = login.LoginQrcodeUnikey()
                uuid = uuid_rsp.get("unikey") if isinstance(uuid_rsp, dict) else None
                if not uuid:
                    print("\33[31m× 无法获取二维码unikey\33[0m\x1b[K")
                    return get_qrcode()

                url = f"https://music.163.com/login?codekey={uuid}"
                img = qrcode.make(url)
                img_path = 'ncm.png'
                img.save(img_path)
                print("\33[32m✓ \33[0m二维码已保存为 'ncm.png'，请使用网易云音乐APP扫码登录。")
                try:
                    open_image(img_path)
                except Exception as e:
                    print(f"{e}，请手动打开 ncm.png 文件进行扫码登录")

                # 轮询检查登录状态，带最大轮询次数（例如 180 次，每次间隔 1 秒）
                max_polls = 180
                for attempt in range(max_polls):
                    try:
                        rsp = login.LoginQrcodeCheck(uuid)
                        if DEBUG:
                            print(f"DEBUG: 二维码检查响应: {rsp}")
                        code = rsp.get("code") if isinstance(rsp, dict) else None
                        if code == 803:
                            session = pyncm.GetCurrentSession()
                            try:
                                login.WriteLoginInfo(login.GetCurrentLoginStatus(), session)
                            except Exception:
                                pass
                            print("\33[32m✓ \33[0m登录成功")
                            try:
                                display_user_info(session)
                            except Exception:
                                pass
                            return session
                        elif code == 8821:
                            print("\33[33m! 接口已失效(8821)\33[0m\x1b[K")
                            raise RuntimeError("登录二维码接口已失效")
                        elif code == 800:
                            print("  二维码已过期，请重新尝试。")
                            break
                        elif code == 802:
                            print(f"\33[33m  用户扫码成功，请在手机端确认登录。\33[0m\x1b[K")
                        elif code != 801:
                            # 未知情况，打印信息但继续轮询直到超时或明确失败
                            msg = rsp.get('message') if isinstance(rsp, dict) else None
                            print(f"\33[31m× 二维码检查失败，出现未知错误: {msg}\33[0m\x1b[K")
                        time.sleep(1)
                    except (Timeout, ConnectionError, RequestException) as e:
                        # 网络层面可重试若干次，再退出
                        print(f"\33[33m! 二维码检查遇到网络错误: {e}，正在重试...\33[0m\x1b[K")
                        time.sleep(1)
                        continue

                print("\33[31m× 二维码登录超时或已过期\33[0m\x1b[K")
                return get_qrcode()

            except Exception as e:
                print(f"\33[31m× 验证出错: {e}\33[0m\x1b[K")
                raise

        elif choice == "2":
            '''
            加载 https://music.163.com/#/login, 在用户扫码登录后获取 cookie 并关闭窗口.

            监测 cookie 的添加, 经实验可知在 https://music.163.com/#/login 登陆后会自动跳转到 https://music.163.com/#/discover, 并且监测 url 的变化, 所以实际上可以先记录所有添加的 cookie, 然后在 url 变化的时候返回所有被记录的 cookie 并关闭窗口(可以直接将 cookie 注入一个新的 session, 然后返回这个 session )
            '''
            print("\33[33m! 打开浏览器扫码登录，请在提示\"正由自动测试软件控制\"的浏览器窗口扫码登录。\33[0m")
            try:
                session = browser_qr_login_via_selenium()
                if session:
                    # 将会话设置为 pyncm 当前会话，便于后续 API 使用
                    pyncm.SetCurrentSession(session)
                    try:
                        # 尝试写入登录信息（容错）
                        login.WriteLoginInfo(login.GetCurrentLoginStatus(), session)
                    except Exception:
                        pass
                    print(f"\33[32m✓ \33[0m浏览器登录成功")
                    try:
                        display_user_info(session)
                    except Exception:
                        pass
                    return session
                else:
                    print("\33[31m× 浏览器登录失败或超时\33[0m")
                    return get_qrcode()
            except ImportError:
                print("\33[31m× 未安装 selenium，请先安装: pip install selenium\33[0m")
                return get_qrcode()
            except Exception as e:
                print(f"\33[31m× 浏览器登录出错: {e}\33[0m")
                return get_qrcode()

        elif choice == "3":
            '''
            参考 手机登录测试.py，实现两种方式：
            - 短信验证码登录
            - 账号（手机）+密码登录
            '''
            print("\33[33m! 手机短信/账号密码登录。\33[0m")
            try:
                ct_inp = input("  请输入国家代码(默认 86) > ").strip()
                phone = input("  请输入手机号 > ").strip()
                
                try:
                    ctcode = int(ct_inp) if ct_inp else 86
                except Exception:
                    ctcode = 86

                print("  选择登录方式：\n  [1] 短信验证码\n  [2] 账号密码")
                m = input("  请选择 (默认 1) > ").strip() or "1"

                if m == "2":
                    # 密码登录
                    try:
                        import getpass
                        password = getpass.getpass("  输入密码: ")
                    except Exception:
                        password = input("  输入密码: ")
                    rsp = login.LoginViaCellphone(phone, password=password, ctcode=ctcode)
                    code = rsp.get('code') if isinstance(rsp, dict) else None
                    if code == 200:
                        session = pyncm.GetCurrentSession()
                        try:
                            login.WriteLoginInfo(login.GetCurrentLoginStatus(), session)
                        except Exception:
                            pass
                        print("\33[32m✓ \33[0m登录成功（密码）")
                        try:
                            display_user_info(session)
                        except Exception:
                            pass
                        return session
                    else:
                        msg = rsp.get('message') if isinstance(rsp, dict) else None
                        print(f"\33[31m× 登录失败: {msg}\33[0m")
                        return get_qrcode()
                else:
                    # 短信验证码登录
                    send_rsp = login.SetSendRegisterVerifcationCodeViaCellphone(phone, ctcode)
                    scode = send_rsp.get('code') if isinstance(send_rsp, dict) else None
                    if scode != 200:
                        print(f"\33[31m× 发送验证码失败: {send_rsp}\33[0m")
                        return get_qrcode()
                    print("\33[32m✓ \33[0m已发送验证码，请查收短信。")
                    # 验证循环
                    while True:
                        captcha = input("  输入短信验证码 > ").strip()
                        if not captcha:
                            print("\33[33m! 验证码不能为空\33[0m")
                            continue
                        v = login.GetRegisterVerifcationStatusViaCellphone(phone, captcha, ctcode)
                        vcode = v.get('code') if isinstance(v, dict) else None
                        if vcode == 200:
                            print("\33[32m✓ \33[0m验证成功")
                            break
                        else:
                            print(f"\33[33m! 验证失败，请重试。响应: {v}\33[0m")
                    # 使用验证码完成登录
                    rsp = login.LoginViaCellphone(phone, captcha=captcha, ctcode=ctcode)
                    code = rsp.get('code') if isinstance(rsp, dict) else None
                    if code == 200:
                        session = pyncm.GetCurrentSession()
                        try:
                            login.WriteLoginInfo(login.GetCurrentLoginStatus(), session)
                        except Exception:
                            pass
                        print("\33[32m✓ \33[0m登录成功（短信）")
                        try:
                            display_user_info(session)
                        except Exception:
                            pass
                        return session
                    else:
                        msg = rsp.get('message') if isinstance(rsp, dict) else None
                        print(f"\33[31m× 登录失败: {msg}\33[0m")
                        return get_qrcode()
            except Exception as e:
                print(f"\33[31m× 手机登录出错: {e}\33[0m")
                return get_qrcode()

        elif choice == "4":
            # 匿名登录
            try:
                rsp = login.LoginViaAnonymousAccount()
                code = None
                nickname = None
                user_id = None
                if isinstance(rsp, dict):
                    content = rsp.get('content') or rsp
                    code = content.get('code') if isinstance(content, dict) else None
                    prof = (content.get('profile') if isinstance(content, dict) else None) or {}
                    nickname = prof.get('nickname') or prof.get('nickName')
                    user_id = content.get('userId') or (prof.get('userId') if isinstance(prof, dict) else None)
                if code == 200:
                    session = pyncm.GetCurrentSession()
                    try:
                        login.WriteLoginInfo(login.GetCurrentLoginStatus(), session)
                    except Exception:
                        pass
                    print(f"\33[32m✓ 匿名登录成功\33[0m")
                    try:
                        display_user_info(session)
                    except Exception:
                        pass
                    return session
                else:
                    print("\33[31m× 匿名登录失败\33[0m")
                    return get_qrcode()
            except Exception as e:
                print(f"\33[31m× 匿名登录出错: {e}\33[0m")
                return get_qrcode()

        else:
            print("\33[33m! 无效选择。\33[0m")
            return get_qrcode()

    except Exception as e:
        print(f"\33[31m× get_qrcode 出现错误: {e}\33[0m\x1b[K")
        raise

def browser_qr_login_via_selenium(timeout_seconds: int = 180):
    """使用本机浏览器打开网易云登录页，扫码后抓取 Cookie 并构建可用的 pyncm 会话。

    成功条件：
    - 浏览器地址从 #/login 跳转到 #/discover 等页面，或
    - 出现关键登录 Cookie：MUSIC_U

    返回：
    - requests.Session（已注入 cookies 和 headers），失败返回 None
    """
    # 尽量静默 Selenium / webdriver-manager 的 Python 层日志输出
    try:
        import logging as _logging, os as _os
        # webdriver_manager / selenium manager 减少下载/诊断输出
        _os.environ.setdefault('WDM_LOG_LEVEL', '0')
        _os.environ.setdefault('WDM_PRINT_FIRST_LINE', '0')
        _logging.getLogger('selenium').setLevel(_logging.CRITICAL)
        _logging.getLogger('urllib3').setLevel(_logging.CRITICAL)
        _logging.getLogger('selenium.webdriver.remote').setLevel(_logging.CRITICAL)
    except Exception:
        pass

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.edge.options import Options as EdgeOptions
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
    except ImportError:
        raise

    driver = None
    last_err = None

    def try_new_driver():
        nonlocal last_err
        # 依次尝试 Edge / Chrome / Firefox，尽量把子进程日志定向到 os.devnull 并关闭一些日志开关
        import os as _os, subprocess as _subprocess
        try:
            from selenium.webdriver.chrome.service import Service as ChromeService
        except Exception:
            ChromeService = None
        try:
            from selenium.webdriver.edge.service import Service as EdgeService
        except Exception:
            EdgeService = None
        try:
            from selenium.webdriver.firefox.service import Service as FirefoxService
        except Exception:
            FirefoxService = None

        creationflags = 0
        if platform.system() == 'Windows' and hasattr(_subprocess, 'CREATE_NO_WINDOW'):
            creationflags = _subprocess.CREATE_NO_WINDOW

        # 设置浏览器相关环境变量，尽量让底层二进制少输出
        try:
            _os.environ.setdefault('CHROME_LOG_FILE', _os.devnull)
        except Exception:
            pass
        try:
            _os.environ.setdefault('MOZ_LOG', '')
        except Exception:
            pass

        # Edge
        try:
            edge_opts = EdgeOptions()
            edge_opts.add_argument("--disable-gpu")
            edge_opts.add_argument("--start-maximized")
            edge_opts.add_experimental_option('excludeSwitches', ['enable-logging'])
            edge_opts.add_experimental_option('useAutomationExtension', False)
            edge_opts.add_argument('--disable-breakpad')
            edge_opts.add_argument('--disable-dev-shm-usage')
            edge_opts.add_argument('--disable-extensions')
            edge_opts.add_argument('--disable-crash-reporter')
            if EdgeService:
                svc = EdgeService(log_path=_os.devnull, creationflags=creationflags)
                return webdriver.Edge(service=svc, options=edge_opts)
            else:
                return webdriver.Edge(options=edge_opts)
        except Exception as e:
            last_err = e

        # Chrome
        try:
            ch_opts = ChromeOptions()
            ch_opts.add_argument("--disable-gpu")
            ch_opts.add_argument("--start-maximized")
            ch_opts.add_experimental_option('excludeSwitches', ['enable-logging'])
            ch_opts.add_experimental_option('useAutomationExtension', False)
            ch_opts.add_argument('--log-level=3')
            ch_opts.add_argument('--disable-extensions')
            ch_opts.add_argument('--disable-breakpad')
            ch_opts.add_argument('--disable-dev-shm-usage')
            ch_opts.add_argument('--disable-crash-reporter')
            ch_opts.add_argument('--disable-software-rasterizer')
            if ChromeService:
                svc = ChromeService(log_path=_os.devnull, creationflags=creationflags)
                return webdriver.Chrome(service=svc, options=ch_opts)
            else:
                return webdriver.Chrome(options=ch_opts)
        except Exception as e:
            last_err = e

        # Firefox
        try:
            ff_opts = FirefoxOptions()
            ff_opts.set_preference("dom.webdriver.enabled", True)
            # 尽量降低 firefox 日志
            ff_opts.set_preference('log', '{"level": "fatal"}')
            # firefox service
            if FirefoxService:
                svc = FirefoxService(log_path=_os.devnull, service_args=None)
                return webdriver.Firefox(service=svc, options=ff_opts)
            else:
                return webdriver.Firefox(options=ff_opts)
        except Exception as e:
            last_err = e
        return None

    driver = try_new_driver()
    if not driver:
        raise RuntimeError(f"无法启动浏览器: {last_err}")

    login_url = "https://music.163.com/#/login"
    target_domains = {"music.163.com", ".music.163.com", ".163.com"}
    start = time.time()
    try:
        driver.get(login_url)
        print("  已打开登录页面，请使用手机网易云音乐扫码并确认...")

        logged_in = False
        music_u = None
        csrf = None

        # 轮询检测 URL 与 Cookie
        while time.time() - start < timeout_seconds:
            current_url = driver.current_url or ""
            # 抓取 cookies
            cookies = driver.get_cookies() or []
            for c in cookies:
                if c.get("name") == "MUSIC_U" and c.get("value"):
                    music_u = c.get("value")
                if c.get("name") in ("__csrf", "csrf_token") and c.get("value"):
                    csrf = c.get("value")

            if music_u and ("#/discover" in current_url or "#/my" in current_url or "#/home" in current_url or "music.163.com/" in current_url):
                logged_in = True
                break

            # 有 MUSIC_U 也认为登录成功（有些情况下 URL 不跳）
            if music_u:
                logged_in = True
                break

            time.sleep(1)

        if not logged_in:
            print("\33[33m! 等待登录超时\33[0m")
            return None

        # 使用 pyncm 的全局会话对象并注入 Cookie
        s = pyncm.GetCurrentSession()
        # 设置 UA，尽量与浏览器一致
        try:
            ua = driver.execute_script("return navigator.userAgent")
        except Exception:
            ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari"
        s.headers.update({
            "User-Agent": ua,
            "Referer": "https://music.163.com/",
            "Origin": "https://music.163.com"
        })

        for c in driver.get_cookies() or []:
            name = c.get("name")
            value = c.get("value")
            domain = c.get("domain") or "music.163.com"
            path = c.get("path") or "/"
            if not name or value is None:
                continue
            # 仅保留相关域名的 cookie，避免污染
            if not any(domain.endswith(td) for td in target_domains):
                continue
            s.cookies.set(name, value, domain=domain, path=path)

        # 补齐 csrf_token（有时需要）
        if csrf and not s.cookies.get("csrf_token"):
            s.cookies.set("csrf_token", csrf, domain=".music.163.com", path="/")

        # 直接返回 pyncm 的 Session，会被调用方设置为当前会话
        return s

    finally:
        try:
            driver.quit()
        except Exception:
            pass
def open_image(image_path):
    system = platform.system()
    
    if system == 'Windows':
        os.startfile(image_path)
    elif system == 'Darwin':  # macOS
        subprocess.call(['open', image_path])
    else:  # Linux etc
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
    print("\33[32m✓ \33[0m会话已保存。")

def parse_lrc(lrc_content):
    if not lrc_content:
        return []
    
    # 匹配时间戳和歌词
    pattern = r'\[(\d{2}):(\d{2})\.(\d{2,3})\](.*)'
    lyrics = []
    
    for line in lrc_content.split('\n'):
        match = re.match(pattern, line)
        if match:
            minutes, seconds, milliseconds, text = match.groups()
            # 转换为秒
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

@retry_with_timeout(timeout=30, retry_times=2, operation_name="获取歌词")
def get_track_lyrics(track_id):
    return track.GetTrackLyrics(track_id)

@retry_with_timeout(timeout=30, retry_times=2, operation_name="获取曲目详情")
def get_track_detail(track_ids):
    return track.GetTrackDetail(track_ids)

@retry_with_timeout(timeout=30, retry_times=2, operation_name="获取歌曲下载链接")
def get_track_audio(song_ids, level, encode_type):
    return track.GetTrackAudioV1(song_ids=song_ids, level=level, encodeType=encode_type)

@retry_with_timeout(timeout=30, retry_times=2, operation_name="获取播放列表")
def get_playlist_all_tracks(playlist_id):
    return playlist.GetPlaylistAllTracks(playlist_id)

def process_lyrics(track_id, track_name, artist_name, output_option, download_path, audio_file_path=None):
    try:
        lyric_data, error = get_track_lyrics(track_id)
        if error or not lyric_data or lyric_data.get('code') != 200 or 'lrc' not in lyric_data:
            print(f"\33[33m! 无法获取歌词: {track_name}\33[0m\x1b[K")
            return False, None
        
        track_detail, error = get_track_detail([track_id])
        song_duration = None
        if not error and track_detail and 'songs' in track_detail and track_detail['songs']:
            song_duration = track_detail['songs'][0].get('dt', 0) / 1000
        original_lyrics = parse_lrc(lyric_data['lrc']['lyric'])
        translated_lyrics = []
        if 'tlyric' in lyric_data and lyric_data['tlyric']['lyric']:
            translated_lyrics = parse_lrc(lyric_data['tlyric']['lyric'])
        
        merged_lyrics = merge_lyrics(original_lyrics, translated_lyrics, song_duration)
        
        if not merged_lyrics:
            print(f"\33[33m! 未找到有效歌词: {track_name}\33[0m\x1b[K")
            return False, None
        
        # 根据用户选择，输出歌词
        if output_option == 'lrc' or (output_option == 'both' and download_path):
            safe_artist_name = re.sub(r'[\\/*?:"<>|]', "-", artist_name)
            safe_track_name = re.sub(r'[\\/*?:"<>|]', "-", track_name)
            lrc_path = os.path.join(download_path, f"{safe_track_name} - {safe_artist_name}.lrc")
            save_lyrics_as_lrc(merged_lyrics, lrc_path)
            print(f"\33[32m✓ \33[0m歌词已保存到 {lrc_path}\x1b[K")
        
        if (output_option == 'metadata' or output_option == 'both') and audio_file_path:
            lrc_content = '\n'.join([format_lrc_line(time, text) for time, text in merged_lyrics])
            
            return True, lrc_content
        
        return True, None
        
    except Exception as e:
        print(f"\33[33m! 处理歌词时出错: {e}\33[0m\x1b[K")
        write_to_failed_list(track_id, track_name, artist_name, f"处理歌词失败: {e}", download_path)
        return False, None

def add_metadata_to_audio(file_path, track_info, lyrics_content=None):
    if not MUTAGEN_INSTALLED:
        print("\33[33m! 未安装mutagen库，跳过添加元数据\33[0m\x1b[K")
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

        print(f"\33[32m✓ \33[0m已为 {os.path.basename(file_path)} 添加元数据\x1b[K")
    except Exception as e:
        print(f"\33[33m! 添加元数据时出错: {e}\33[0m\x1b[K")

def normalize_path(path):
    if path:
        # 除开头和结尾的空格
        path = path.strip()
        # 除引号
        if (path.startswith("'") and path.endswith("'")) or (path.startswith('"') and path.endswith('"')):
            path = path[1:-1]
        # 除尾部空格
        path = path.rstrip()
    
    expanded_path = os.path.expanduser(path)
    normalized_path = os.path.normpath(expanded_path)
    if not os.path.exists(normalized_path):
        try:
            os.makedirs(normalized_path)
            print(f"\33[32m✓ \33[0m创建目录: {normalized_path}")
        except Exception as e:
            print(f"\33[31m× 创建目录失败: {e}\33[0m")
            default_path = os.path.join(os.getcwd(), "downloads")
            os.makedirs(default_path, exist_ok=True)
            print(f"\33[33m! 将使用默认下载路径: {default_path}\33[0m")
            return default_path
    return normalized_path

def get_playlist_tracks_and_save_info(playlist_id, level, download_path):
    try:
        # 使用带超时的函数获取播放列表
        tracks, error = get_playlist_all_tracks(playlist_id)
        if error:
            print(f"\33[31m× 获取歌单列表时出错: {error}\33[0m\x1b[K")
            return
            
        if not tracks or 'songs' not in tracks:
            print("\33[31m× 获取歌单列表返回无效数据\33[0m\x1b[K")
            return
            
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        playlist_info_filename = os.path.join(download_path, f'!#_playlist_{playlist_id}_info.txt')
        with open(playlist_info_filename, 'w', encoding='utf-8') as f:
            for track_info in tracks['songs']:
                track_id = track_info['id']
                track_name = track_info['name']
                artist_name = ', '.join(artist['name'] for artist in track_info['ar'])
                f.write(f"{track_id} - {track_name} - {artist_name}\n")
        print(f"\33[32m✓ \33[0m歌单信息已保存到 {playlist_info_filename}")
        total_tracks = len(tracks['songs'])
        for index, track_info in enumerate(tracks['songs'], start=1):
            track_id = track_info['id']
            track_name = track_info['name']
            artist_name = ', '.join(artist['name'] for artist in track_info['ar'])
            download_and_save_track(track_id, track_name, artist_name, level, download_path, track_info, index, total_tracks)
        print("="*terminal_width+"\x1b[K")
        print(f"\33[32m✓ 操作已完成，歌曲已下载并保存到 \33[36m{download_path}\33[32m 文件夹中。\33[0m\x1b[K")
    except Exception as e:
        print(f"\33[31m× 获取歌单列表或下载歌曲时出错: {e}\33[0m\x1b[K")

def get_track_info(track_id, level, download_path):
    try:
        # 使用带超时的函数获取曲目详情
        track_info_rsp, error = get_track_detail([track_id])
        if error:
            print(f"\33[31m× 获取歌曲信息时出错: {error}\33[0m\x1b[K")
            return
            
        if not track_info_rsp or 'songs' not in track_info_rsp or not track_info_rsp['songs']:
            print(f"\33[31m× 获取歌曲信息返回无效数据\33[0m\x1b[K")
            return
            
        track_info = track_info_rsp['songs'][0]
        track_id = track_info['id']
        track_name = track_info['name']
        artist_name = ', '.join(artist['name'] for artist in track_info.get('ar', []))
        download_and_save_track(track_id, track_name, artist_name, level, download_path, track_info, 1, 1)
        print(f"\33[32m✓ \33[0m歌曲 {track_name} 已保存到 {download_path} 文件夹中。\x1b[K")
    except Exception as e:
        print(f"\33[31m! 获取歌曲信息时出错: {e}\33[0m\x1b[K")

def download_and_save_track(track_id, track_name, artist_name, level, download_path, track_info=None, index=None, total=None):
    def make_safe_filename(filename):
        return re.sub(r'[\\/*?:"<>|]', "-", filename)

    try:
        # 使用带超时的API调用获取音频URL
        url_info, error = get_track_audio([track_id], level, "flac")
        if error:
            write_to_failed_list(track_id, track_name, artist_name, f"获取下载链接失败: {error}", download_path)
            print(f"\33[31m! 获取曲目 {track_name} 的下载链接时出错: {error}\33[0m\x1b[K")
            return
            
        if not url_info or 'data' not in url_info or not url_info['data']:
            write_to_failed_list(track_id, track_name, artist_name, "获取下载链接返回无效数据", download_path)
            print(f"\33[31m! 获取曲目 {track_name} 的下载链接返回无效数据\33[0m\x1b[K")
            return
            
        url = url_info['data'][0].get('url')
        if url:
            max_retries = 2
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    # 使用带超时的请求初始化下载
                    response = requests.get(url, stream=True, timeout=30)
                    if response.status_code != 200:
                        print(f"\33[31m× 获取 URL 时出错: {response.status_code} - {response.text}\33[0m\x1b[K")
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
                    
                    if terminal_width >= 88:
                        print("="*terminal_width+"\x1b[K" + f"\n\33[94m{progress_status}正在下载: {safe_filename}\33[0m\x1b[K")
                    else:
                        print(f"正在下载: {safe_filename}\33[0m\x1b[K")
                        pass
                    
                    downloaded = 0
                    progress_bar_length = 35 if terminal_width >= 88 else min(20, terminal_width - 40)
                    speed = 0  
                    show_progress_bar = terminal_width >= 88
                    last_downloaded = 0
                    last_update_time = time.time()
                    download_stalled = False
                    no_progress_timer = None
                    
                    def check_download_progress():
                        nonlocal download_stalled, last_downloaded
                        if downloaded == last_downloaded:
                            download_stalled = True
                        
                    with open(safe_filepath, 'wb') as f:
                        start_time = time.time()
                        for chunk in response.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # 检查是否有下载进度
                                current_time = time.time()
                                if current_time - last_update_time >= 10:  # 每10秒检查一次进度
                                    if downloaded == last_downloaded:
                                        # 无进展，中断并重试
                                        print(f"\33[33m! 下载 {safe_filename} 停滞，正在重试...\33[0m\x1b[K")
                                        break
                                    last_downloaded = downloaded
                                    last_update_time = current_time
                                
                                if file_size > 0 and show_progress_bar:
                                    percent = downloaded / file_size
                                    bar_filled = int(progress_bar_length * percent)
                                    bar = '\33[32m█' * bar_filled + '\33[0m_' * (progress_bar_length - bar_filled)
                                    
                                    elapsed_time = time.time() - start_time
                                    if elapsed_time > 0:
                                        speed = downloaded / elapsed_time / 1024  # KB/s
                                    
                                    sys.stdout.write(f"\r|{bar}| {percent*100:.1f}% {downloaded/1024/1024:.2f}MB/{file_size/1024/1024:.2f}MB {speed:.1f}KB/s\x1b[K")
                                    sys.stdout.flush()
                    
                    # 检查下载是否完成
                    if downloaded < file_size and file_size > 0:
                        retry_count += 1
                        if retry_count <= max_retries:
                            print(f"\33[33m! 下载不完整，正在重试 ({retry_count}/{max_retries})...\33[0m\x1b[K")
                            continue
                        else:
                            write_to_failed_list(track_id, track_name, artist_name, "下载不完整", download_path)
                            print(f"\33[31m× 多次尝试下载失败: {safe_filename}\33[0m\x1b[K")
                            return
                    
                    # 下载成功，跳出重试循环
                    break
                
                except (Timeout, ConnectionError, RequestException) as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        print(f"\33[33m! 下载超时，正在重试 ({retry_count}/{max_retries})...\33[0m\x1b[K")
                    else:
                        write_to_failed_list(track_id, track_name, artist_name, f"下载失败: {e}", download_path)
                        print(f"\33[31m× 多次尝试下载失败: {e}\33[0m\x1b[K")
                        return
            
            if show_progress_bar:
                sys.stdout.write("\r\33[2A\33[K")  
                print(f"\33[32m✓ 已下载: \33[0m{safe_filename}\x1b[K")
            else:
                print(f"\33[32m✓ 已下载{progress_status}\33[0m{safe_filename}\x1b[K")
            
            # 检查音频长度，短于35秒警告
            try:
                audio = MutagenFile(safe_filepath)
                if audio is not None and hasattr(audio, 'info') and hasattr(audio.info, 'length'):
                    duration = audio.info.length
                    if duration < 35:
                        print(f"\33[33m! 警告: {safe_filename} 音频长度仅为 {duration:.1f} 秒，可能为试听片段。\33[0m\x1b[K")
                        print("\33[33m  出现这种问题可能是您没有VIP权限或网易云变更接口所致。\33[0m\x1b[K")
                        write_to_failed_list(track_id, track_name, artist_name, f"音频长度过短({duration:.1f}s)，可能为试听片段", download_path)
            except Exception as e:
                print(f"\33[33m! 检查音频长度时出错: {e}\33[0m\x1b[K")
            
            if not track_info and url_info['data'][0].get('id'):
                try:
                    track_detail, error = get_track_detail([url_info['data'][0]['id']])
                    if not error and track_detail and 'songs' in track_detail and track_detail['songs']:
                        track_info = track_detail['songs'][0]
                    elif error:
                        print(f"\33[33m! 获取曲目详情失败: {error}\33[0m\x1b[K")
                except Exception as e:
                    print(f"\33[33m! 获取曲目详情失败: {e}\33[0m\x1b[K")
            
            # 处理歌词
            lyrics_success, lyrics_content = process_lyrics(
                track_id, track_name, artist_name, 
                lyrics_option, download_path, safe_filepath
            )
            
            # 添加元数据
            if track_info:
                add_metadata_to_audio(safe_filepath, track_info, lyrics_content if lyrics_success else None)
            else:
                write_to_failed_list(track_id, track_name, artist_name, "无法添加元数据: 缺少曲目信息", download_path)
                print("\33[33m! 无法添加元数据: 缺少曲目信息\33[0m\x1b[K")
                
        else:
            if terminal_width >= 88:
                sys.stdout.write("\r\33[1A\33[K")  
            write_to_failed_list(track_id, track_name, artist_name, "无可用下载链接（可能歌曲已下架）", download_path)
            print(f"\33[31m! 无法下载 {track_name} - {artist_name}, 详情请查看 !#_FAILED_LIST.txt\33[0m\x1b[K")
    except (KeyError, IndexError) as e:
        if terminal_width >= 88:
            sys.stdout.write("\r\33[1A\33[K")  
        write_to_failed_list(track_id, track_name, artist_name, f"URL信息错误: {e}", download_path)
        print(f"\33[31m! 访问曲目 {track_name} - {artist_name} 的URL信息时出错: {e}\33[0m\x1b[K")
    except Exception as e:
        if terminal_width >= 88:
            sys.stdout.write("\r\33[1A\33[K")  
        write_to_failed_list(track_id, track_name, artist_name, f"未知下载错误: {e}", download_path)
        print(f"\33[31m! 下载歌曲时出错: {e}\33[0m\x1b[K")

def write_to_failed_list(track_id, track_name, artist_name, reason, download_path):
    failed_list_path = os.path.join(download_path, "!#_FAILED_LIST.txt")
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
        print("\33[32m✓ \33[0m会话已从文件加载。")
        if DEBUG:
            print("当前 Cookie 信息：")
            for cookie in session.cookies:
                print(f"  {cookie.name}: {cookie.value} (Domain: {cookie.domain})")
            print(session)
            input("按回车键继续...")
        return session
    else:
        return None

def get_current_nickname(default_name: str = '未登录用户') -> str:
    """获取当前登录用户昵称，失败则返回默认值。"""
    try:
        status = login.GetCurrentLoginStatus()
        if DEBUG:
            print("当前登录状态：", status)
            input("按回车键继续...")
        if isinstance(status, dict):
            prof = status.get('profile') or {}
            name = prof.get('nickname') or prof.get('nickName')
            if name:
                return str(name)
        return default_name
    except Exception:
        return default_name

def _parse_user_info_from_status(status: dict) -> dict:
    """从 login.GetCurrentLoginStatus() 的返回结构中提取昵称、用户ID和VIP信息，尽可能兼容多种字段名。"""
    nickname = None
    user_id = None
    vip = None
    if not isinstance(status, dict):
        return {'nickname': nickname, 'user_id': user_id, 'vip': vip}

    prof = status.get('profile') or {}
    nickname = prof.get('nickname') or prof.get('nickName') or status.get('nickname')
    user_id = prof.get('userId') or status.get('userId') or status.get('account', {}).get('id') if isinstance(status.get('account'), dict) else status.get('userId')

    # VIP 信息可能在多处：profile.vipType, status.vipType, profile.get('vip', {}).get('type')
    vip = prof.get('vipType') or status.get('vipType')
    if vip is None:
        vip_block = prof.get('vip') if isinstance(prof.get('vip'), dict) else None
        if isinstance(vip_block, dict):
            vip = vip_block.get('type') or vip_block.get('vipType')

    return {'nickname': nickname, 'user_id': user_id, 'vip': vip}

def display_user_info(session=None,silent=False):
    """打印当前会话的用户名与 VIP 状态（尽量容错）。

    如果传入 session，会先将其设为当前 pyncm 会话以便 login.GetCurrentLoginStatus() 使用。
    """
    try:
        if session is not None:
            try:
                pyncm.SetCurrentSession(session)
            except Exception:
                pass
        if USER_INFO_CACHE['user_id'] is not None:
            if DEBUG:
                print("skipped")
            # 如果已经有用户信息，直接返回
            nick = USER_INFO_CACHE.get('nickname') or '未知用户'
            uid = USER_INFO_CACHE.get('user_id') or '-'
            vip_val = USER_INFO_CACHE.get('vip')
            vip_str = '未知'
            
            if not silent:
                print(f"\33[32m✓ 登录用户: \33[36m{nick}\33[0m (ID: {uid}) VIP: \33[33m{vip_str}\33[0m")
            return USER_INFO_CACHE
        
        # 获取当前登录状态
        status = login.GetCurrentLoginStatus()
        info = _parse_user_info_from_status(status if isinstance(status, dict) else {})
        nick = info.get('nickname') or '未知用户'
        uid = info.get('user_id') or '-'
        vip_val = info.get('vip')
        vip_str = '未知'
        try:
            if vip_val is None:
                vip_str = '非VIP'
            else:
                # 有些接口使用 int 类型或字符串
                vip_int = int(vip_val)
                vip_str = 'VIP' if vip_int > 0 else '非VIP'
        except Exception:
            vip_str = str(vip_val)

        
        if not silent:
            print(f"\33[32m✓ 已登录: \33[36m{nick}\33[0m (ID: {uid}) 状态: \33[33m{vip_str}\33[0m")
        # 更新全局 USER_INFO_CACHE 字典而不是在函数内重新绑定，避免 UnboundLocalError
        USER_INFO_CACHE.update(info)
        return info
    except Exception as e:
        try:
            print(f"\33[33m! 无法获取用户信息: {e}\33[0m")
        except Exception:
            pass
        return {'nickname': None, 'user_id': None, 'vip': None}

if __name__ == "__main__":
    try:
        # 获取终端宽度
        terminal_width, _ = get_terminal_size()
        
        # 根据终端宽度决定是否显示ASCII艺术
        if terminal_width >= 88:
            print(""" __. __. ____. . . . . . . .  ____. . ___. . \33[0m.\33[0m\33[0m \33[0m\33[0m.\33[0m\33[0m \33[0m\33[0m.\33[0m . . . . .  ___. . . . . . .  __. . . 
/\\ \\/\\ \\/\\. _`\\.  /'\\_/`\\. . /\\. _`\\ /\\_ \\.\33[0m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[0m \33[0m. . . .  /\\_ \\.  __. . . . /\\ \\__.  
\\ \\ `\\\\ \\ \\ \\/\\_\\/\\. . . \\.  \\ \\ \\L\33[0m\\\33[0m\33[0m \33[0m\33[31m\\\33[0m\33[31m/\33[0m\33[31m/\33[0m\33[31m\\\33[0m \33[0m\\\33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[0m.\33[0m\33[0m \33[0m\33[31m_\33[0m\33[31m_\33[0m\33[31m.\33[0m . __. __\\//\\ \\ /\\_\\. . ___\\ \\ ,_\\. 
 \\ \\ , ` \\ \\ \\/_/\\ \\ \\__\\ \\.  \\ \\\33[0m \33[0m\33[31m,\33[0m\33[31m_\33[0m\33[31m_\33[0m\33[31m/\33[0m\33[31m \33[0m\33[31m\\\33[0m\33[0m \33[0m\\ \33[31m\\\33[0m\33[31m.\33[0m\33[31m \33[0m\33[0m \33[0m/'__`\\ /\\ \\/\\ \\ \\ \\ \\\\/\\ \\. /',__\\ \\ \\/. 
. \\ \\ \\`\\ \\ \\ \\L\\ \\ \\ \\_/\\ \\.  \\\33[0m \33[0m\33[31m\\\33[0m\33[31m \33[0m\33[31m\\\33[0m\33[31m/\33[0m\33[0m.\33[0m  \\\33[0m_\33[0m\33[0m\\\33[0m\33[31m \33[0m\33[31m\\\33[0m\33[31m_\33[0m\33[31m/\33[0m\33[31m\\\33[0m\33[31m \33[0m\33[0m\\\33[0m\33[0mL\33[0m\\.\\\\ \\ \\_\\ \\ \\_\\ \\\\ \\ \\/\\__, `\\ \\ \\_ 
.  \\ \\_\\ \\_\\ \\____/\\ \\_\\\\ \\_\\. \33[31m \33[0m\33[31m\\\33[0m\33[31m \33[0m\33[31m\\\33[0m\33[0m_\33[0m\\. \33[0m \33[0m\33[31m/\33[0m\33[31m\\\33[0m\33[31m_\33[0m\33[31m_\33[0m\33[31m_\33[0m\33[31m_\33[0m\33[31m\\\33[0m\33[31m \33[0m\33[31m\\\33[0m\33[31m_\33[0m\33[31m_\33[0m\33[31m/\33[0m\33[0m.\33[0m\\_\\/`____ \\/\\____\\ \\_\\/\\____/\\ \\__\\
. . \\/_/\\/_/\\/___/. \\/_/ \\/_/.\33[0m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m\\\33[0m/_/.\33[31m \33[0m\33[31m \33[0m\33[31m\\\33[0m\33[31m/\33[0m\33[31m_\33[0m\33[0m_\33[0m\33[31m_\33[0m\33[31m_\33[0m\33[31m/\33[0m\33[31m\\\33[0m\33[0m/\33[0m\33[0m_\33[0m\33[31m_\33[0m\33[31m/\33[0m\33[31m\\\33[0m\33[31m/\33[0m\33[0m_\33[0m/`/___/> \\/____/\\/_/\\/___/. \\/__/
. . . . . . . . . . . . . . . \33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[0m \33[0m. .\33[0m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[0m \33[0m. \33[0m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[0m.\33[0m .\33[0m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[0m \33[0m.  /\\___/. . . . . . . . . . .  
. . . . . . . . . . . . . . .\33[0m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[0m \33[0m. .\33[0m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[0m \33[0m. .\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m . \33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m.  \\/__/. . . . . . . . . . . . 
 ____. . . . . . . . . . . . .\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[0m.\33[0m ___\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[0m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[0m.\33[0m . \33[0m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m. .  __. . . . . . . . . . . .  
/\\. _`\\. . . . . . . . . . . .\33[0m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m \33[0m\33[0m/\33[0m\\_ \\\33[0m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[0m.\33[0m . .\33[31m \33[0m\33[31m.\33[0m\33[31m \33[0m\33[31m.\33[0m .  /\\ \\. . . . . . . . . . . . 
\\ \\ \\/\\ \\.  ___.  __. __. __.  \33[31m_\33[0m\33[31m_\33[0m\33[31m_\33[0m\33[31m\\\33[0m\33[0m/\33[0m/\\ \\.\33[0m \33[0m\33[0m.\33[0m\33[0m \33[0m\33[0m \33[0m___. .\33[35m \33[0m\33[31m \33[0m\33[31m_\33[0m\33[31m_\33[0m\33[0m.\33[0m .  \\_\\ \\. .  __. _ __. . . . . 
 \\ \\ \\ \\ \\ / __`\\/\\ \\/\\ \\/\\ \\/' \33[0m_\33[0m\33[31m \33[0m\33[31m`\33[0m\33[31m\\\33[0m\33[31m\\\33[0m\33[0m \33[0m\\ \\.  / __\33[0m`\33[0m\33[0m\\\33[0m\33[31m \33[0m\33[31m/\33[0m\33[31m'\33[0m\33[31m_\33[0m\33[0m_\33[0m`\\.  /'_` \\. /'__`/\\`'__\\. . . . 
. \\ \\ \\_\\ /\\ \\L\\ \\ \\ \\_/ \\_/ /\\ \\\33[0m/\33[0m\33[31m\\\33[0m\33[31m \33[0m\33[31m\\\33[0m\33[31m\\\33[0m\33[31m_\33[0m\33[31m\\\33[0m\33[31m \33[0m\33[0m\\\33[0m\33[0m_\33[0m\33[0m/\33[0m\33[0m\\\33[0m\33[0m \33[0m\33[31m\\\33[0m\33[31mL\33[0m\33[31m\\\33[0m\33[31m \33[0m\33[31m/\33[0m\33[31m\\\33[0m\33[0m \33[0m\\L\\.\\_/\\ \\L\\ \\/\\. __\\ \\ \\/. . . .  
.  \\ \\____\\ \\____/\\ \\___x___/\\ \\_\\ \\\33[0m_\33[0m\33[31m/\33[0m\33[31m\\\33[0m\33[31m_\33[0m\33[31m_\33[0m\33[31m_\33[0m\33[31m_\33[0m\33[31m\\\33[0m\33[31m \33[0m\33[31m\\\33[0m\33[31m_\33[0m\33[31m_\33[0m\33[31m_\33[0m\33[0m_\33[0m\33[0m\\\33[0m \\__/.\\_\\ \\___,_\\ \\____\\ \\_\\. . . .  
. . \\/___/ \\/___/. \\/__//__/. \\/_/\\/_\\/_\33[0m_\33[0m\33[0m_\33[0m\33[0m_\33[0m\33[0m/\33[0m\33[0m\\\33[0m\33[0m/\33[0m\33[0m_\33[0m__/ \\/__/\\/_/\\/__,_ /\\/____/\\/_/. . . .  


                                                  Netease Cloud Music Playlist Downloader""")
        else:
            print("\n\nNetease Cloud Music Playlist Downloader")
            print("\33[33m! 您的终端窗口宽度小于88个字符，部分特性已被停用。\33[0m")
            print("\33[44;37m若要完整展示程序特性和下载进度，请调整窗口宽度或字体大小到可以完整显示这行后重新执行脚本\33[0m\n\n")
            # print("="*88)
            '''
    ========================================================================================================
            '''
            
        if DEBUG:
            print("\33[33m! 调试模式已启用。\33[0m")
            print("\33[33m  调试模式可能会输出大量冗余或敏感信息。\33[0m")
            print("\33[33m  如果不需要调试信息，请删除或注释掉 DEBUG = True。\33[0m")
        session = load_session_from_file()
        if session:
            print("  使用保存的会话登录。")
            print("\33[33m  如需更换账号，请删除 session.json 文件后重新运行脚本。\33[0m")
            try:
                display_user_info(session)
            except Exception:
                pass
            time.sleep(2)
        else:
            try:
                session = get_qrcode()
                if session:
                    save_session_to_file(session)
                time.sleep(3)
            except Exception as e:
                print(e)
                input("  按回车退出程序...")
                sys.exit(1)

        # ============ 新的菜单式配置与启动流程 ============
        default_path = os.path.join(os.getcwd(), "downloads")
        config = {
            'download_path': default_path,
            'mode': 'playlist',   # 'playlist' | 'track'
            'playlist_id': None,
            'track_id': None,
            'level': 'exhigh',
            'lyrics_option': 'both',
        }

        preview_cache = {
            'playlist': {'id': None, 'name': None, 'count': None, 'error': None},
            'track': {'id': None, 'name': None, 'artist': None, 'error': None}
        }

        def color_text(text, color_code):
            return f"\33[{color_code}m{text}\33[0m"

        def set_download_path():
            print("\n\33[2m===========================================\33[0m")
            print("> 下载路径编辑")
            print("\n  输入下载路径（可拖拽文件夹至此），按回车确认。")
            ipt = input("\33[36m  > \33[0m\33[4m")
            print("\33[0m", end="")
            if not ipt.strip():
                config['download_path'] = default_path
            else:
                config['download_path'] = normalize_path(ipt)

        def toggle_mode():
            config['mode'] = 'track' if config['mode'] == 'playlist' else 'playlist'

        def input_id_for_mode():
            print("\n\33[2m===========================================\33[0m")
            print("> 配置 ID")
            print("\33[94mi 有关于歌单 ID 和单曲 ID 的说明，请参阅 https://github.com/padoru233/NCM-Playlist-Downloader/blob/main/README.md#使用方法\33[0m")
            if config['mode'] == 'playlist':
                ipt = input("  请输入歌单 ID\33[36m > \33[0m")
                config['playlist_id'] = ipt.strip() or None
            else:
                ipt = input("  请输入单曲 ID\33[36m > \33[0m")
                config['track_id'] = ipt.strip() or None
            refresh_preview()

        def choose_level():
            print("\n\33[2m===========================================\33[0m")
            print("> 音质 选项")
            print("\33[94mi 有关于音质选项的详细说明，请参阅 https://github.com/padoru233/NCM-Playlist-Downloader/blob/main/README.md#音质说明\33[0m")
            print("可使用的音质选项：")
            opts = [
                ("standard", "标准 MP3 128kbps"),
                ("exhigh", "极高 MP3 320kbps"),
                ("lossless", "无损 FLAC 48kHz/16bit"),
                ("hires", "高解析度无损 FLAC 192kHz/16bit"),
                ("jymaster", "高清臻音 FLAC 96kHz/24bit"),
            ]
            for i, (val, zh) in enumerate(opts, 1):
                flag = "\33[44m" if config['level'] == val else ""
                print(f"\33[36m[{i}]\33[0m {flag}{zh} ({val})\33[0m ")
            print("\n\33[36m[0]\33[0m 取消")
            sel = input("\33[36m> \33[0m").strip()
            mapping = {str(i): v for i, (v, _) in enumerate(opts, 1)}
            if sel in mapping:
                config['level'] = mapping[sel]

        def choose_lyrics():
            print("\33[2m\n===========================================\33[0m")
            print("> 歌词 选项")
            print("保存歌词的方式：")
            print("\33[36m[1]\33[0m 写入标签和文件")
            print("\33[36m[2]\33[0m 只写入标签")
            print("\33[36m[3]\33[0m 只写入lrc文件")
            print("\33[36m[4]\33[0m 不处理歌词")
            print("\n\33[36m[0]\33[0m 取消")
            sel = input("\33[36m> \33[0m").strip()
            if sel == '1':
                config['lyrics_option'] = 'both'
            elif sel == '2':
                config['lyrics_option'] = 'metadata'
            elif sel == '3':
                config['lyrics_option'] = 'lrc'
            elif sel == '4':
                config['lyrics_option'] = 'none'

        def refresh_preview():
            try:
                if config['mode'] == 'track' and config['track_id']:
                    if preview_cache['track']['id'] == config['track_id']:
                        return
                    info, err = get_track_detail([config['track_id']])
                    if err or not info or not info.get('songs'):
                        preview_cache['track'] = {'id': config['track_id'], 'name': None, 'artist': None, 'error': str(err) if err else '无结果'}
                    else:
                        song = info['songs'][0]
                        name = song.get('name', '')
                        artist = ', '.join(a.get('name', '') for a in song.get('ar', []))
                        preview_cache['track'] = {'id': config['track_id'], 'name': name, 'artist': artist, 'error': None}
                elif config['mode'] == 'playlist' and config['playlist_id']:
                    if preview_cache['playlist']['id'] == config['playlist_id']:
                        return
                    lst, err = get_playlist_all_tracks(config['playlist_id'])
                    if DEBUG:
                        print(f"调试信息：\33[90m{lst}\33[0m")
                        input("按回车键继续...")
                    if err or not lst or 'songs' not in lst:
                        preview_cache['playlist'] = {'id': config['playlist_id'], 'name': None, 'count': None, 'error': str(err) if err else '无结果'}
                    else:
                        songs = lst.get('songs', []) or []
                        count = len(songs)
                        first_song_name = songs[0].get('name') if songs else None
                        # 由于歌单名称可能无法获取，这里保存第一首歌的歌名用于展示
                        preview_cache['playlist'] = {
                            'id': config['playlist_id'],
                            'name': first_song_name,
                            'count': count,
                            'error': None
                        }
            except Exception as e:
                if config['mode'] == 'track':
                    preview_cache['track'] = {'id': config.get('track_id'), 'name': None, 'artist': None, 'error': str(e)}
                else:
                    preview_cache['playlist'] = {'id': config.get('playlist_id'), 'name': None, 'count': None, 'error': str(e)}

        def render_menu(display_only=False):
            
            print("\33[1J\33[H\33[0&J",end="")  # 清屏
            # if os.name == 'nt': # Windows 系统
            #     os.system('cls')
            # else: # Linux 或 macOS 系统
            #     os.system('clear')
            if DEBUG:
                print(display_user_info(silent=True))
                #{'nickname': None, 'user_id': 13199197479, 'vip': None}
            display_user_info(silent=True)
            user_info = display_user_info(silent=True)
            nickname = user_info.get('nickname') or '匿名用户'
            vip_status = '\33[33m黑胶VIP\33[32m' if user_info.get('vip') else '\33[0m\33[2m普通用户，下载可能受限\33[32m'
            print(f"\n\33[32m欢迎，\33[33m{nickname}\33[32m！{vip_status}\33[0m" if not display_only else f"\n\33[32m用户名：\33[33m{nickname}\33[32m，{vip_status}\33[0m")
            
            print("\33[31m获取用户信息时实际失败！您可能无法使用任何功能！\33[0m" if user_info.get('user_id') is None else "")
            terminal_width, _ = get_terminal_size()
            print("\33[2m"+"="*terminal_width+"\33[0m")

            dp = config['download_path']
            path_str = f"\33[36m默认（{dp}）\33[0m" if dp == default_path else f"\33[32m{dp}\33[0m"
            print(f"\33[36m[0]\33[0m下载位置：{path_str}")
            print("\33[2m"+"="*terminal_width+"\33[0m")

            selected_color = '33'  # 黄
            unselected_color = '2;9' # 灰
            p_lbl = color_text('歌单', selected_color if config['mode'] == 'playlist' else unselected_color)
            t_lbl = color_text('单曲', selected_color if config['mode'] == 'track' else unselected_color)
            id_val = config['playlist_id'] if config['mode'] == 'playlist' else config['track_id']
            id_title = '歌单ID' if config['mode'] == 'playlist' else '单曲ID'
            id_show = id_val if id_val else color_text('\33[5m[未指定]\33[0m', '31')
            print(f"\33[36m[1]\33[0m尝试下载 {p_lbl}{t_lbl}  \33[2m|\33[0m \33[36m[2]\33[0m{id_title}:\33[33m{id_show}\33[0m")
            print("\33[2m"+"-"*terminal_width+"\33[0m")

            if config['mode'] == 'track':
                print("单曲详细信息: " if config['track_id'] else "详细信息:")
                if config['track_id'] and preview_cache['track']['id'] == config['track_id'] and not preview_cache['track']['error']:
                    print(f"歌名：\33[36m{preview_cache['track'].get('name') or ''}\33[0m")
                    print(f"歌手：\33[36m{preview_cache['track'].get('artist') or ''}\33[0m")
                    ready_to_go = True
                elif config['track_id'] and preview_cache['track']['error']:
                    print(color_text(f"获取单曲信息失败：{preview_cache['track']['error']}，无法下载！", '31;5'))
                    print("\n")
                    ready_to_go = False
                else:
                    print(color_text(f"请先按[2]，指定要下载的曲目ID！", '31;5'))
                    print("\n")
                    ready_to_go = False
            else:
                print("歌单详细信息: " if config['playlist_id'] else "详细信息: ")
                if config['playlist_id'] and preview_cache['playlist']['id'] == config['playlist_id'] and not preview_cache['playlist']['error']:
                    if DEBUG:
                        print(f"调试信息：\33[90m{preview_cache['playlist']}\33[0m")
                    name = preview_cache['playlist'].get('name') or ''
                    count = preview_cache['playlist'].get('count')
                    print(f"曲目数：\33[36m{count if count is not None else ''}\33[0m")
                    print(f"第一首：\33[36m{name}\33[0m")
                    ready_to_go = True
                elif config['playlist_id'] and preview_cache['playlist']['error']:
                    print(color_text(f"获取歌单信息失败：{preview_cache['playlist']['error']}，无法下载！", '31;5'))
                    print("\n")
                    ready_to_go = False
                else:
                    print(color_text(f"请先按[2]，指定要下载的歌单ID！", '31;5'))
                    print("\n")
                    ready_to_go = False
            print("\n" if display_only else "\33[32m准备就绪，可以下载。\n\33[0m" if ready_to_go else "\n",end="")
            print("\33[2m"+"="*terminal_width+"\33[0m")
            print("下载选项\n" if not display_only else "",end="")
            print("\33[2m"+"-"*terminal_width+"\33[0m\n" if not display_only else "",end="")
            level_zh = {
                'standard': '标准', 'exhigh': '极高', 'lossless': '无损', 'hires': '高解析度无损', 'jymaster': '高清臻音'
            }.get(config['level'], config['level'])
            print(f"\33[36m[3]\33[0m音质: \33[33m{level_zh}\33[0m")
            lyrics_zh = {
                'both': '写入标签和文件',
                'metadata': '只写入标签',
                'lrc': '只写入lrc文件',
                'none': '不处理歌词'
            }.get(config['lyrics_option'], config['lyrics_option'])
            print(f"\33[36m[4]\33[0m歌词: \33[33m{lyrics_zh}\33[0m")
            print("\33[2m"+"-"*terminal_width+"\33[0m")
            if not display_only:
                print("\33[42;97;1;5m[9] ▶ 开始任务\33[0m\t[Ctrl + C] 退出程序" if ready_to_go else "\33[9m[9] ▶ 开始任务\33[0m\t[Ctrl + C] 退出程序")
                print("\n\n键入执行操作的序号，按回车确认\33[36m > \33[0m", end="")
            return ready_to_go

        
        while True:
            ready_to_go = render_menu()
            choice = input().strip()
            if choice == '0':
                set_download_path()
            elif choice == '1':
                toggle_mode()
            elif choice == '2':
                input_id_for_mode()
            elif choice == '3':
                choose_level()
            elif choice == '4':
                choose_lyrics()
            elif choice == '9':
                selected_id = config['playlist_id'] if config['mode'] == 'playlist' else config['track_id']
                if not selected_id:
                    print(color_text("× 未指定ID，请先通过[2]设置。", '31'))
                    time.sleep(2)
                    continue
                if not ready_to_go:
                    print(color_text("× 当前配置无法下载，请检查错误信息，或报告给开发者。", '31'))
                    time.sleep(2)
                    continue
                render_menu(display_only=True)
                print(f"\33[0m\n"+"="*terminal_width+"\n\33[94m  开始下载...\n\33[32m✓ 正在使用听歌API，不消耗VIP下载额度\33[0m\33[?25l")
                # 让全局下载流程拿到歌词选项
                globals()['lyrics_option'] = config['lyrics_option']
                if config['mode'] == 'playlist':
                    get_playlist_tracks_and_save_info(selected_id, config['level'], config['download_path'])
                else:
                    get_track_info(selected_id, config['level'], config['download_path'])
                print("\33[?25h",end="")
                break
            else:
                pass
    except KeyboardInterrupt:
        print("\33[?25h",end="")
        print("\n\n\33[33m× 操作已被用户取消（按下了Ctrl + C组合键）。\33[0m")
    except Exception as e: 
        print(f"\33[31m× 出现全局错误: {e}\33[0m")
        print("  请报告给开发者以便修复。")
    finally:
        print("\33[?25h",end="")
        input("\33[33m  按回车键退出...\33[0m")

