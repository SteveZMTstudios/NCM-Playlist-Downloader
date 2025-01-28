# 网易云歌单下载  
  
## 介绍  
  
此脚本为获取网易云歌单并批量下载极高/无损/高清音质  
  
Windows需要安装python3+，确保pip和python添加到系统路径中，点击run.bat运行  
  
1、扫码登录 信息完全通过和保存在本地  
2、获取歌单id，在歌单界面选择分享，得到网址："https://music.163.com/m/playlist?id=12345678&creatorId=666666"  
其中"playlist?id="后面的数字为歌单id  
3、选择音质，极高exhigh 无损lossless 高清hires 超清jymaster 默认无损  
  
自动下载到当前目录下downloads文件夹，并生成歌单列表文件  
  
## 鸣谢
- [pyncm](https://github.com/mos9527/pyncm)
