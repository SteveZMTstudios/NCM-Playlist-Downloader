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
git clone https://github.com/SteveZMTstudios/NCM-Playlist-Downloader.git
cd NCM-Playlist-Downloader
pip install -r requirements.txt
python script.py
```

### Windows 

```
git clone https://github.com/SteveZMTstudios/NCM-Playlist-Downloader.git
cd NCM-Playlist-Downloader
.\run.bat
```

### Linux / Android Termux

```bash
git clone https://github.com/SteveZMTstudios/NCM-Playlist-Downloader.git
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
- 极高`exhigh` (HQ)
    mp3格式 CD音质 立体声 32位采样 ~192kbps 最高320kbps MPEG Audio layer 1/2 (mpga)
    通常一首歌大小8MB左右

- 无损`lossless` (SQ VIP)
    flac格式 高保真无损音质，最高48KHz/16bit
    通常一首歌大小25MB左右
    需要 VIP 账号

- 高清`hires` (Spatial Audio VIP)
    flac格式 声音听感增强，最高96kHz/24bit
    通常一首歌大小50MB左右
    需要 VIP 账号

- 超清`jymaster` (Master SVIP)
    flac格式 音乐制作大师级音质，最高192kHz/24bit
    通常一首歌大小150MB左右
    需要 SVIP 账号
    可能耗费下载用量

### 音频标签（元数据）

本程序会自动为下载的音频文件添加完整的元数据标签：
- 歌曲标题
- 艺术家信息
- 专辑名称
- 曲目编号
- 发行年份
- 专辑封面图片
- 歌词（如选择嵌入）

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
- [NCM Playlist Downloader (base)](https://github.com/padoru233/NCM-Playlist-Downloader)
- [pyncm](https://github.com/mos9527/pyncm)

## 许可

### 法律声明

本软件（NCM-Playlist-Downloader）基于原项目 [NCM Playlist Downloader (base)](https://github.com/padoru233/NCM-Playlist-Downloader) 补充开发，并遵循 GNU 通用公共许可证 v3.0（GPL-3.0）的条款。

### 授权许可

根据 GPL-3.0 协议，您拥有以下权利：

- **自由使用：** 您可以出于任何目的自由使用本软件。
- **自由复制：** 您可以复制本软件，并将其分发给他人。
- **自由修改：** 您可以修改本软件的源代码，以满足您的需求。
- **自由分发修改版：** 您可以分发修改后的本软件，但必须遵守 GPL-3.0 协议的条款。

### 限制条款

您在使用本软件时必须遵守以下限制：

- **商业用途限制：** 未经明确授权，禁止将本软件用于任何商业用途，包括但不限于提供付费下载服务、代下载服务或其他任何形式的收费服务。
- **遵守法律法规：** 禁止使用本软件进行任何可能违反网易云音乐用户协议或相关法律法规的行为，包括但不限于大规模批量下载、破解版权保护机制等。
- **保留版权声明：** 必须保留本软件及其衍生作品中的所有版权声明和许可信息，不得删除或修改。
- **GPL-3.0 兼容性：** 如果您分发修改后的本软件，必须确保您的修改版也遵循 GPL-3.0 协议，并向用户提供源代码。
- **不得附加限制：** 您不得对本软件的使用、复制、修改或分发施加任何超出 GPL-3.0 协议范围的限制。

### 免责声明

本软件按“现状”提供，不提供任何明示或暗示的保证，包括但不限于对适销性、特定用途适用性和非侵权性的保证。在任何情况下，软件作者或版权持有人均不对因使用本软件或与本软件相关的任何索赔、损害或其他责任承担责任，无论该责任是因合同、侵权或其他原因引起的。

### 知识产权

本软件可能包含受版权、专利或其他知识产权法律保护的材料。您同意尊重所有适用的知识产权法律，并仅在获得授权的情况下使用这些材料。

### 联系方式

若您认为本项目侵犯了您的权力，或有任何其他疑问，请通过 [admin#stevezmt.top](mailto:admin@stevezmt.top) 联系我删除。

### 完整协议

有关完整的使用条款和条件，请参阅 [GPL-3.0 协议全文](https://www.gnu.org/licenses/gpl-3.0.html)。


