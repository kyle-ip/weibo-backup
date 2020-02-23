# weibo-backup

[![Python](https://img.shields.io/badge/language-Python-red.svg)]()

> since 2020-02-23 22:00

## Introduction

A simple script to contert weibo (mobile)  to long image for backup.



## Usage

Module Installation: 

```shell
pip install -r requirements.txt
```

Run HTTP Sercvice: 

```shell
uvicorn main:app --reload
```

Request: 

```
http://localhost:8000/get_image?title=test_bakcup&url=https://m.weibo.cn/5249746181/4466577691376925
```

Response:

```json
{
    "msg": "OK!",
    "data": "https://github.com/psf/requests/test-res.jpg",
    "code": 0
}
```



Original weibo screenshot:

<center>

![image-20200222140049840](https://ywh-oss.oss-cn-shenzhen.aliyuncs.com/blog/weibo-backup-origin.jpg?x-oss-process=image/resize,p_50)

</center>

Backup Images:

<center>

![image-20200222140049840](https://ywh-oss.oss-cn-shenzhen.aliyuncs.com/blog/weibo-backup-bak.jpg?x-oss-process=image/resize,p_50)

</center>

## License

See LICENSE file.