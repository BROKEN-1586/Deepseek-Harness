# -*- coding: utf-8 -*-
"""给 D 盘顶层文件夹写「悬停注释」（desktop.ini 的 InfoTip）。可逆：删掉 desktop.ini 即还原。"""
import os, ctypes, io

HIDDEN, SYSTEM, READONLY = 0x2, 0x4, 0x1
k32 = ctypes.windll.kernel32

def set_attr(path, attr):
    k32.SetFileAttributesW(str(path), attr)

NOTE = {
    "rag": "RAG 服务本体（rag_server.py + 9 个库的向量数据）。开机自启走 boot-rag.ps1；8001 端口。勿动。",
    "AutoPrep": "学习规划 / 周报脚本（study_planner.py、weekly_review.py）。定时任务已停用，手动跑。",
    "Clearn": "本项目工作区：DEEPCODE.md 规则、tools 脚本、recipes、问题汇总、_diag 产物。",
    "AgentData": "记忆库：memory（含 lessons-recent 备案热区、archive 归档）＋ keys.json 等配置。",
    "Goose-win32-x64": "goose 框架本体（便携版）。当前 Agent 运行环境。",
    "日程规划": "日程规划库（非 RAG）：01-日记 / 02-课程 / 03-周计划 / 04-汇总。Obsidian 镜像在 93-日程规划。",
    "_git": "Obsidian 自动快照仓库（obsidian.git ＋ auto_snapshot.ps1）。在用，勿删。",
    "backup": "所有自动备份的落点（cleanup / reorg / merge / syncflow / docker-move 等），名字带时间戳。",
    "01-下载与缓存": "临时下载落点（cxdownload）。文件在这里就是可删的。",
    "02-学习资料": "网课与素材：宋浩高数视频 7.1G、科三考场路线视频 1.4G、单词音频素材。",
    "03-工具软件": "绿色便携工具：Dism++、Everything、WizTree、卸载工具。不含安装型软件。",
    "04-EndNote": "EndNote 文献库（.enl ＋ .Data ＋ 压缩版 .enlx）。三个必须放在一起。",
    "英语温热练习": "四级手抄练习小库（Obsidian）：单词/ 写作/。用户手写，非标记源。",
    "Docker": "Docker 数据盘（DIFY 环境所在）。wsl\\disk\\docker_data.vhdx ≈17G，勿手删。",
    "models": "ComfyUI 等模型权重（8.2G）。",
    "VMs": "虚拟机镜像（16.6G）。",
    "WSL": "WSL 发行版数据（Ubuntu-2604）。",
    "Comfy-Desktop": "ComfyUI 桌面版（43.6G，含模型缓存）。",
    "Comfy UI": "ComfyUI 便携版程序目录。",
    "Program Files": "64 位程序安装目录（勿动）。",
    "ProgramData": "程序的公共数据目录（勿动）。",
    "Office 2021": "Office 2021 安装目录。",
    "IntelliJ IDEA 2026.2.3": "IntelliJ IDEA 安装目录（Toolbox 装的）。",
    "LegionZone": "联想 LegionZone 程序目录。",
    "EndNote2025 For Windows": "EndNote 2025 安装包/程序目录。",
    "LenovoSoftstore": "联想应用商店（含 Install 缓存）。",
    "LeStoreDownload": "联想商店下载的安装包（已清空，留作下载落点）。",
    "DownKyi": "B 站下载工具 DownKyi。",
    "BaiduNetdiskDownload": "百度网盘默认下载目录。",
    "KimiData": "Kimi 桌面端数据/缓存。",
    "乐云云盘": "乐云云盘客户端数据。",
    "SmartProxy-v2.1-Chrome-ManifestV3": "SmartProxy 浏览器扩展相关文件。",
    "PCL-2.14.0.0": "PCL 我的世界启动器。",
    "BiliGame": "B 站游戏客户端数据。",
    "WeGameApps": "WeGame 游戏目录。",
    "TapTap": "TapTap 客户端数据。",
    "SteamLibrary": "Steam 库目录。",
    "XboxGames": "Xbox 游戏安装目录（2G）。",
    "Documents": "应用数据（qwen-agent 等）。",
    "rail_user_data": "WeGame 运行数据。",
    "WindowsApps": "微软商店应用目录（系统，勿动）。",
    "WpSystem": "商店应用数据（系统，勿动）。",
    "CTF-OS": "空目录（CTF 环境占位，可删）。",
    "电脑管家迁移文件": "电脑管家搬家留下的文件：QQ/微信聊天记录（重要，别删）＋软件残留（可清）。",
    "System Volume Information": "系统还原点（系统目录，勿动）。",
    "$RECYCLE.BIN": "回收站。",
}

def write_infotip(path, text):
    ini = os.path.join(path, "desktop.ini")
    # desktop.ini 必须 UTF-16 LE（带 BOM）且带隐藏+系统属性，资源管理器才读
    with io.open(ini, "w", encoding="utf-16") as f:
        f.write("[.ShellClassInfo]\r\n")
        f.write("InfoTip=%s\r\n" % text.replace("\r", " ").replace("\n", " "))
    set_attr(ini, HIDDEN | SYSTEM)
    # 文件夹加「只读」属性，Explorer 才会去读 desktop.ini
    cur = k32.GetFileAttributesW(str(path))
    if cur != -1:
        set_attr(path, cur | READONLY)
    return ini

ok = fail = 0
for name, text in NOTE.items():
    p = os.path.join("D:\\", name)
    if not os.path.isdir(p):
        print("  跳过（不存在）:", name); continue
    try:
        write_infotip(p, "[%s] %s" % (name, text))
        ok += 1
    except Exception as e:
        fail += 1
        print("  !! %s: %s" % (name, e))
print("写入注释 %d 个目录，失败 %d" % (ok, fail))

# 抽查
for name in ["rag", "Docker", "电脑管家迁移文件", "02-学习资料"]:
    p = os.path.join("D:\\", name)
    ini = os.path.join(p, "desktop.ini")
    attr = k32.GetFileAttributesW(ini)
    txt = io.open(ini, encoding="utf-16").read().split("InfoTip=")[-1].strip() if os.path.exists(ini) else "缺失"
    print("  抽查 %-14s attr=0x%X  %s" % (name, attr, txt[:70]))
