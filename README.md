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


## 鸣谢
- [NCM Playlist Downloader (basic)](https://github.com/padoru233/NCM-Playlist-Downloader)
- [pyncm](https://github.com/mos9527/pyncm)
