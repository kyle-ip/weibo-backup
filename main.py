# coding: utf8

import requests
import re
import os
import json
import time

from fastapi import FastAPI
from PIL import Image
from lxml import etree

BASE_PATH = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)
    )
    , "img"
)

TEXT_TEMPLATE = """
作者：{0}
发布时间：{1}
内容：{2}
"""

WRITE_TEXT_API_URL = "http://www.gaituba.com/plus/txt2jpg.php"

TEXT_IMG_URL_PREFIX = "http://www.gaituba.com/static/box/"

TAG_PATTERN = re.compile(r'<.*?>')

app = FastAPI()


class WeiBoParser(object):

    def __init__(self, title: str = "", url: str = ""):
        self.url = url
        self.title = title
        self.img_list = []
        self.img_path_list = []
        self.content = ""
        self.author = ""
        self.create_time = ""
        self.today = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        path = os.path.join(BASE_PATH, self.today)
        if not os.path.exists(path):
            os.makedirs(path)

    def download_images(self) -> bool:
        """
        下载图片
        :return:
        """

        for i, img_url in enumerate(self.img_list):
            file_name = os.path.join(
                BASE_PATH, self.today, "{0}-{1}.jpg".format(self.title, i)
            )
            self.img_path_list.append(file_name)
            with open(file_name, 'wb') as f:
                res = requests.get(img_url, timeout=10)
                if res.status_code != 200:
                    return False
                f.write(res.content)
        return True

    def write_text(self) -> bool:
        """
        把正文内容写入图片
        :return:
        """
        text = TEXT_TEMPLATE.format(
            self.author, self.create_time, self.content.replace("<br />", "\n")
        )
        params = {
            "content": text,
            "f_size": 12,
            "userStyle": "000000|FFFFFF",
            "fontStyle": "simhei.ttf"
        }
        res = requests.post(WRITE_TEXT_API_URL, params, timeout=10)
        if res.status_code != 200:
            return False
        response = json.loads(res.text)
        if not response.get("state"):
            return False

        img_url = TEXT_IMG_URL_PREFIX + response.get("imgurl").split("/")[-1]
        file_name = os.path.join(
            BASE_PATH, self.today, "{0}-text.jpg".format(self.title)
        )
        with open(file_name, 'wb') as f:
            res = requests.get(img_url)
            if res.status_code != 200:
                return False
            f.write(res.content)
            self.img_path_list.append(file_name)
        img = Image.open(file_name)
        img = img.crop((0, 0, img.width, img.height - 40))
        img.save(file_name)
        return True

    def joint_images(self):
        """
        拼接图片
        :return:
        """
        img_file_list = [Image.open(fn) for fn in self.img_path_list]
        width = max([img_file.width for img_file in img_file_list])
        ims_size = [list(im.size) for im in img_file_list]

        # 计算相对长图目标宽度尺寸
        for i in range(len(ims_size)):
            rate = width / ims_size[i][0]
            ims_size[i][0] = width
            ims_size[i][1] = int(rate * ims_size[i][1])

        sum_height = sum([im[1] for im in ims_size])

        # 创建空白长图
        try:
            result = Image.new(img_file_list[0].mode, (width, sum_height))

            # 拼接
            top = 0
            for i, im in enumerate(img_file_list):
                # 等比缩放
                mew_im = im.resize(ims_size[i], Image.ANTIALIAS)
                result.paste(mew_im, box=(0, top))
                top += ims_size[i][1]

            # 保存
            file_name = os.path.join(
                BASE_PATH, self.today, "{0}-res.jpg".format(self.title)
            )
            result.save(file_name)
        except Exception as e:
            print(e)
            return False
        return True

    def parse_data(self) -> bool:
        """
        解析数据
        :return:
        """

        res = requests.get(self.url, timeout=10)
        if res.status_code != 200:
            return False
        html = etree.HTML(res.text)
        scripts = html.cssselect("script")
        if not scripts:
            return False

        # 取出填充数据的 js
        script = []
        for s in scripts:
            lines = str(s.text).split("\n")
            if len(lines) > 1:
                script = [line.strip() for line in lines]
                break

        for line in script:

            if "created_at" in line:
                self.create_time = self.author = line \
                    .replace('"created_at": "', '') \
                    .replace('",', '')
                continue

            if "\"screen_name\"" in line:
                self.author = line \
                    .replace('"screen_name": "', '') \
                    .replace('",', '')
                continue

            # content
            if "\"text\"" in line:
                html = line \
                    .replace('"text": "', '') \
                    .replace('",', '') \
                    .replace("<br />", "\n")
                self.content = TAG_PATTERN.sub('', html)
                continue

            # image
            if "sinaimg.cn/large/" in line and "original_pic" not in line:
                self.img_list.append(
                    line.replace('"url": "', '').replace('",', '')
                )
        return True

    def run(self) -> str:
        if self.parse_data() \
                and self.write_text() \
                and self.download_images() \
                and self.joint_images():
            return os.path.join(
                BASE_PATH, self.today, "{0}-res.jpg".format(self.title)
            )


@app.get("/get_image")
def get_image(title: str, url: str):
    obj = WeiBoParser(title, url)
    return {
        "msg": "OK!",
        "data": obj.run(),
        "code": 0
    }


if __name__ == "__main__":
    obj = WeiBoParser("test", "https://m.weibo.cn/6010658056/4466393782880237")
    obj.run()
