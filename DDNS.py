#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import re
import os
import sys
import json
import urllib.request
import socket
import time

# ---------- 配置 ----------
CACHE_FILE = "ipv6_cache.txt"     # 存放上次获取到的 IPv6 地址
OUTPUT_FILE = "ipv6.txt"          # 最终写入最新 IPv6 地址的文件（供 Pages 读取）
# 如果希望脚本自动执行 git 提交，取消下面注释并填写你的仓库路径
# GIT_REPO_PATH = r"C:\your\repo\path"   # Windows 示例
# GIT_REPO_PATH = "/home/user/repo"      # Linux 示例
# --------------------------

def get_ipv6_by_web(url):
    """通过访问外部 API 获取公网 IPv6 地址"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            ip = resp.read().decode('utf-8').strip()
            # 简单校验 IPv6 格式
            if ':' in ip and not ip.startswith('fe80'):
                return ip
    except Exception:
        pass
    return None

def get_ipv6_by_local_command():
    """
    通过系统命令获取 IPv6 临时地址（优先返回临时公网地址）
    支持 Windows (ipconfig) 和 Linux (ip -6 addr)
    """
    if sys.platform.startswith('win'):
        try:
            output = subprocess.check_output("ipconfig", encoding="gbk", timeout=3)
            # 查找 "临时 IPv6 地址" 段，提取后面的 IPv6
            lines = output.splitlines()
            for i, line in enumerate(lines):
                if "临时 IPv6 地址" in line or "Temporary IPv6 Address" in line:
                    # 提取冒号分隔的 IPv6（去除前缀说明）
                    match = re.search(r'([0-9a-fA-F:]+)', line)
                    if match:
                        ip = match.group(1)
                        if ':' in ip and not ip.startswith('fe80'):
                            return ip
        except Exception:
            pass
    else:  # Linux / macOS
        try:
            output = subprocess.check_output("ip -6 addr show scope global", shell=True, encoding='utf-8', timeout=3)
            # 查找包含 temporary 的 inet6 行
            lines = output.splitlines()
            for line in lines:
                if "temporary" in line and "inet6" in line:
                    match = re.search(r'inet6\s+([0-9a-fA-F:]+)', line)
                    if match:
                        ip = match.group(1).split('/')[0]  # 去掉前缀长度
                        if ':' in ip and not ip.startswith('fe80'):
                            return ip
        except Exception:
            # 尝试 ifconfig（备用）
            try:
                output = subprocess.check_output("ifconfig", encoding='utf-8', timeout=3)
                # 查找 inet6 且带有 temporary 或 flags 的行（不同发行版输出不同）
                lines = output.splitlines()
                for i, line in enumerate(lines):
                    if "inet6" in line and "temporary" in line:
                        match = re.search(r'inet6\s+([0-9a-fA-F:]+)', line)
                        if match:
                            ip = match.group(1).split('/')[0]
                            if ':' in ip and not ip.startswith('fe80'):
                                return ip
            except Exception:
                pass
    return None

def get_current_ipv6():
    """
    综合多种方式获取当前公网 IPv6 临时地址
    优先使用 Web API（稳定），失败则回退到本地命令
    """
    # 定义多个可靠 IPv6 检测网址
    web_urls = [
        "https://v6.ident.me",
        "http://getip6.china-ipv6.cn:5010/",
        "https://6.ipw.cn",
        "https://ipv6.icanhazip.com",
        "https://api6.ipify.org",
    ]
    
    # 依次尝试 Web API
    for url in web_urls:
        ip = get_ipv6_by_web(url)
        if ip:
            return ip
    
    # 若所有 Web 失败，尝试本地命令
    ip = get_ipv6_by_local_command()
    if ip:
        return ip
    
    # 都失败则返回 None
    return None

def main():
    current_ip = get_current_ipv6()
    if not current_ip:
        print("❌ 未能获取到有效的公网 IPv6 地址")
        sys.exit(1)
    
    # 读取上次保存的地址
    old_ip = ""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            old_ip = f.read().strip()
    
    # 如果地址发生变化，更新文件
    if current_ip != old_ip:
        print(f"🔄 IPv6 地址变化: {old_ip} -> {current_ip}")
        # 写入缓存文件（记录当前地址）
        with open(CACHE_FILE, "w") as f:
            f.write(current_ip)
        # 写入输出文件（供 Pages 读取）
        with open(OUTPUT_FILE, "w") as f:
            f.write(current_ip)
        
        # ---------- 可选：自动 git 提交 ----------
        # 如果你希望脚本自动 push，取消下面代码的注释，并配置好 GIT_REPO_PATH
        # import subprocess
        # repo_path = GIT_REPO_PATH
        # try:
        #     subprocess.check_call(["git", "-C", repo_path, "add", CACHE_FILE, OUTPUT_FILE])
        #     subprocess.check_call(["git", "-C", repo_path, "commit", "-m", f"Update IPv6: {current_ip}"])
        #     subprocess.check_call(["git", "-C", repo_path, "push"])
        #     print("✅ Git push 完成")
        # except Exception as e:
        #     print(f"⚠️ Git 操作失败: {e}")
        # -----------------------------------------
        
        print(f"✅ 已更新 IPv6 地址文件: {OUTPUT_FILE}")
    else:
        print(f"ℹ️  IPv6 地址未变化，仍为 {current_ip}")

if __name__ == "__main__":
    main()