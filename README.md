# 网易云歌单下载  
  
## 介绍  
  
此脚本为获取网易云歌单并批量下载极高/无损/高清音质 

自动下载到当前目录下downloads文件夹，并生成歌单列表文件  

不消耗网易云音乐的下载次数，支持无损音质下载

可同步下载歌词（包括翻译）和元数据

使用简单，只需扫码登录，输入歌单id即可下载

## 使用方法

确保你已经安装了`git` `python-3.6`以上版本，然后运行以下命令
```
git clone https://github.com/padoru233/NCM-Playlist-Downloader.git
cd NCM-Playlist-Downloader
pip install -r requirements.txt
python script.py
```

### Windows 

```
git clone https://github.com/padoru233/NCM-Playlist-Downloader.git
cd NCM-Playlist-Downloader
.\run.bat
```

### Linux / Android Termux

```bash
git clone https://github.com/padoru233/NCM-Playlist-Downloader.git
cd NCM-Playlist-Downloader
chmod +x run.sh
./run.sh
```

---

1. 扫码登录 信息完全通过和保存在本地  
2. 获取歌单id，在歌单界面选择分享，得到网址：`https://music.163.com/m/playlist?id=12345678&creatorId=666666`
其中`playlist?id=`后面的数字为歌单id  
或者回车，输入歌曲id  
3. 选择音质：极高`exhigh` 无损`lossless` 高清`hires` 超清`jymaster` 默认无损  

## 说明

### 音质说明

- 标准`standard`
    - mp3格式 普通音质 ~128kbps
    - 声道: 立体声 stereo
    - 采样率: 44100 Hz
    - 位每采样: 32
    - 编解码器: MPEG Audio layer 1/2 (mpga)
    ```
    Stream #0:0: Audio: mp3 (mp3float), 44100 Hz, stereo, fltp, 128 kb/s
      Metadata:
        encoder         : Lavc58.13
    ```
    - 通常一首歌大小3-5MB左右

- **极高`exhigh` (HQ)**
    - mp3格式 近CD品质 最高320kbps
    - 声道: 立体声 stereo
    - 采样率: 44100 Hz
    - 位每采样: 32
    - 编解码器: MPEG Audio layer 1/2 (mpga)
    ```
    Stream #0:0: Audio: mp3 (mp3float), 44100 Hz, stereo, fltp, 320 kb/s
      Metadata:
        encoder         : Lavc58.13
    ```
    - 通常一首歌大小8-10MB左右

- 无损`lossless` (SQ VIP)
    - flac格式 高保真无损音质 最高48KHz/16bit
    - 声道: 立体声 stereo
    - 采样率: 44100 Hz
    - 位每采样: 32
    - 编解码器: FLAC (Free Lossless Audio Codec) (flac)
    ```
      Stream #0:0: Audio: flac, 44100 Hz, stereo, s16
    ```
    - 通常一首歌大小25-30MB左右
    - 需要 VIP 账号

- 高解析度无损`hires` (Spatial Audio VIP)
    - flac格式 更饱满清晰的高解析度音质 最高192kHz/24bit
    - 声道: 立体声 stereo
    - 采样率: 44100 Hz
    - 位每采样: 32
    - 编解码器: FLAC (Free Lossless Audio Codec) (flac)
    ```  
    Stream #0:0: Audio: flac, 44100 Hz, stereo, s16
    ```
    - 通常一首歌大小50MB左右
    - 需要 VIP 账号

- 高清臻音`jymaster` (Master VIP)
    - flac格式 声音听感增强 96kHz/24bit
    - 声道: 立体声 stereo
    - 采样率: 96000 Hz
    - 位每采样: 32
    - 编解码器: FLAC (Free Lossless Audio Codec) (flac)
    ```
      Stream #0:0: Audio: flac, 96000 Hz, stereo, s32 (24 bit)
    ```
    - 通常一首歌大小150MB左右
    - 需要 VIP 账号

### 音频标签（元数据）

本程序会自动为下载的音频文件添加完整的元数据标签（受限于可用的API）：
- 歌曲标题`TITLE`
- 艺术家信息`ARTIST`
- 专辑名称`ALBUM`
- 曲目轨道编号`track`
- 发行年份`DATE`
- 专辑封面图片
- 歌词（如果选择嵌入）`LYRICS`

支持MP3(ID3标签)和FLAC格式的元数据嵌入，使音乐文件在各类播放器中显示完整信息。

### 歌词

程序提供多种歌词处理方式，在下载时可选择：
- `lrc`：保存为独立LRC文件（与音频文件同名），UTF-8编码
- `metadata`：将歌词嵌入到音频文件元数据中
- `both`：同时保存独立文件和嵌入元数据
- `none`：不下载歌词

默认设置为保存独立LRC文件。

#### 歌词翻译处理

当歌词有翻译版本时，程序会处理翻译内容：
1. 解析原文和翻译歌词的时间轴
2. 将翻译行插入到对应原文行之后
3. 优化翻译行时间戳，使播放时原文与翻译依次显示
4. 导出为标准LRC格式，兼容大多数音乐播放器

示例：
```lyric
[01:01.57]I’m covering my ears like a kid
[01:04.81]我像孩子一样堵住耳朵
[01:04.82]When your words mean nothing, I go la la la
[01:09.17]当你的话语毫无意义时 我就高唱 啦啦啦
[01:09.18]I’m turning off the volume when you speak
...
```
显示效果：

---
I’m covering my ears like a kid <br>
我像孩子一样堵住耳朵<br>
**When your words mean nothing, I go la la la**<br>
当你的话语毫无意义时 我就高唱 啦啦啦 *（译文不会被播放器聚焦）*<br> 
I’m turning off the volume when you speak<br>

---
这种处理方式使得歌词在播放时，高亮原文，翻译位于原文下方，提供更好的阅读体验。

### 文件说明

- `session.json`：
  保存登录会话信息的文件，使您下次使用时无需重新登录。
  包含加密的用户凭证，仅保存在本地。

- `ncm.png`：
  登录时生成的二维码图片文件，用于网易云音乐APP扫码登录。
  登录完成后可以删除。

- `downloads/`：
  默认的下载目录，所有音乐和歌词文件将保存在此。
  可在运行程序时自定义下载路径。

- `!#_playlist_{playlist_id}_info.txt`：
  保存歌单信息的文本文件，包含歌单中所有歌曲的ID、名称和艺术家。
  便于查找特定歌曲和记录歌单内容。

- `!#_FAILED_LIST.txt`：
  记录下载失败的歌曲列表，包含歌曲ID、名称、艺术家和失败原因。
  常见失败原因包括：歌曲已下架、地区限制、单曲付费、VIP权限不足等。

## 鸣谢
- [pyncm](https://github.com/mos9527/pyncm)




