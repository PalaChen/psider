import json
import multiprocessing
import os
import re
import sys
import time
import hashlib
import configparser
import requests
from datetime import datetime
from threading import Thread
from multiprocessing import Pool
from typing import (
    Callable,
    Union,
    Optional,
    Any
)

IS_EXE = False

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    BASE_PATH = os.path.dirname(os.path.relpath(sys.argv[0]))
else:
    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(BASE_PATH)

from parser import parser_question, parser_discover
from latest_user_agents import get_random_user_agent
from cookie import get_cookie
from db import db, ArticleModel, QuestionModel
from log import get_log, INFO_LOG

logger = get_log(BASE_PATH, INFO_LOG)


class Config(dict):
    def __getattr__(self, key) -> Optional[Any]:
        value = self.get(key)
        if value is None:
            return
        if value.lower() in ['yes', 'true', 'on', ]:
            return True
        if value.lower() in ['no', 'false', 'off', ]:
            return False
        if value.isdigit():
            return int(value)
        return value

    def __setattr__(self, key, value) -> None:
        self[key] = value

    proxy_addr: Optional[str]
    auth_key: Optional[str]
    password: Optional[str]
    use_proxy: Optional[bool]
    start: Optional[int]
    end: Optional[int]
    process_num: Optional[int]
    save_image: Optional[bool]
    save_video: Optional[bool]
    interval_frequency: Optional[int]


config = configparser.ConfigParser()
config.read(os.path.join(BASE_PATH, "config.ini"), encoding='utf-8')

c = Config(dict(config['DEFAULT']))

SAVE_HTML = c.save_html

USE_PROXY = c.use_proxy

# 账密模式
proxyUrl = "http://%(user)s:%(password)s@%(server)s" % {
    "user": c.auth_key,
    "password": c.password,
    "server": c.proxy_addr,
}
proxies = {
    "http": proxyUrl,
    "https": proxyUrl,
}


def get_cookie_str(cookies: Union[dict, list]) -> str:
    cookie = ""
    if isinstance(cookies, dict):
        for k, v in cookies.items():
            cookie += f"{k}={v}; "
    elif isinstance(cookies, list):
        for t in cookies:
            cookie += f"{t['name']}={t['value']}; "

    # cookie={}
    # for t in cookies:
    #     cookie[t['name']]=t['value']

    return cookie


def get_session_id(url: str) -> str:
    pattern = re.compile("question/(.*)")
    res = pattern.search(url)
    if res:
        return res.group(1)


def save_file(url: str, content: str):
    file_name = None
    if "item" in url or "explore" in url:
        pattern = re.compile("(explore|item)/(.*)\?")
        res = pattern.search(url)
        if res: file_name = res.group(2)
    else:
        file_name = get_session_id(url)

    if file_name is None:
        return
    with open(f"./html/{file_name}.html", 'w', encoding='utf-8') as f:
        f.write(content)


def get_path(file_type: str, file_name: Union[str, None] = None) -> str:
    if file_name:
        return os.path.join(BASE_PATH, file_type, file_name)
    return os.path.join(BASE_PATH, file_type)


def check_dirname_exist():
    dirnames = ['image', 'video']
    for dir in dirnames:
        path = get_path(dir)
        if not os.path.exists(path):
            os.mkdir(path)


class Request():
    def __init__(self, save=False):
        self.save = save

    def __call__(self, func: Callable):
        def wrapper(obj, *args, **kwargs):
            payload = func(obj, *args, **kwargs)
            if USE_PROXY:
                payload['proxies'] = proxies
            url = payload.pop("url")
            headers = {}
            headers['Cookie'] = obj.cookie
            headers['User-Agent'] = obj.user_agent

            try:
                response = requests.request("GET", url, headers=headers, **payload)
            except Exception as e:
                logger.error(f"请求异常 url:{url}  错误如下:")
                logger.exception(e)
                return None

            status_code = response.status_code
            if status_code != 200:
                logger.info(f"请求失败 url:{url} 状态码：{status_code}")
                return None
            logger.info(f"请求成功 url:{url} 状态码：{status_code}")
            content = response.text
            if self.save:
                save_file(url, content)
            return content

        return wrapper


class Download():
    def __init__(self, file_type: str):
        self.file_type = file_type
        check_dirname_exist()

    def __call__(self, func: Callable):
        def wrapper(obj, *args, **kwargs):
            payload = func(obj, *args, **kwargs)

            if USE_PROXY:
                payload['proxies'] = proxies

            file_path = get_path(self.file_type, payload.pop('file_name'))
            headers = {}
            headers['cookie'] = obj.cookie
            headers['User-Agent'] = obj.user_agent
            try:
                with requests.get(stream=True, headers=headers, **payload) as r:
                    r.raise_for_status()
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
            except Exception as e:
                logger.error("下载出现异常 错误如下：")
                logger.exception(e)

            return None

        return wrapper


def get_userage_and_cookie():
    user_agent = get_random_user_agent()
    cookie_li = get_cookie(user_agent)
    cookie = get_cookie_str(cookie_li)
    return user_agent, cookie


class XiaoHongShuSpider(object):
    def __init__(self, interval_frequency: int = 5,
                 save_image: bool = False,
                 save_video: bool = False,
                 user_agent=None,
                 cookie=None):
        """

        :param save_image:是否下载图片
        :param save_video: 是否下载视频
        :param interval_frequency:睡眠时间
        """

        self.session = requests.Session()
        self.save_image = save_image
        self.save_video = save_video
        logger.info(f"interval_frequency:{interval_frequency}")

        if isinstance(interval_frequency, int):
            interval_frequency = interval_frequency

        self.interval_frequency = interval_frequency

        if user_agent and cookie:
            self.user_agent = user_agent
            self.cookie = cookie
        else:
            self.reflush()

    def reflush(self):
        self.user_agent, self.cookie = user_agent, cookie = get_userage_and_cookie()
        logger.info(f"user_agent:{user_agent}")
        logger.info(f"cookie:{cookie}")

    def get_question(self, url: str):
        content = self.get(url)
        if content is None:
            return
        question_id = get_session_id(url)
        question, items = parser_question(content)
        logger.info(f"items:{len(items)}")
        li = []

        num = 0
        for item in items:
            url = item['url'].replace("discovery/item", "explore")

            try:
                discovery_dict = self.get_explore(url)
            except Exception as e:
                logger.error(f"请求发生异常 url:{url}")
                logger.exception(e)
                continue

            if not isinstance(discovery_dict, dict):
                logger.info("请检查ip是否被屏蔽")
                num += 1
                continue
            images = discovery_dict['images']
            if self.save_image:
                self.mulitply_download_images(images)

            discovery_dict['images'] = json.dumps(images)

            if self.save_video:
                video_url = discovery_dict['video']
                if isinstance(video_url, str):
                    logger.info(f"开始下载视频 网址：{video_url}")
                    self.download_video(video_url)

            discovery_dict['question_id'] = question_id
            discovery_dict['question'] = question
            discovery_dict['url'] = url

            li.append(discovery_dict)

            time.sleep(self.interval_frequency)

        with db.atomic():
            ArticleModel.insert_many(li).execute()

        logger.info(f"数据保存成功:{len(li)}")
        if len(li) > 5:
            status = 1
        else:
            status = 0

        obj = QuestionModel(question_id=question_id,
                            num=len(li),
                            status=status
                            )
        obj.save()

    @Request(save=SAVE_HTML)
    def get(self, url: str) -> dict:
        return {"url": url}

    @Download("image")
    def download_image(self, url: str):
        file_name = f"{hashlib.md5(url.encode(encoding='utf-8')).hexdigest()}.jpg"

        return {"url": url,
                "file_name": file_name
                }

    @Download("video")
    def download_video(self, url: str):
        file_name = url.split('/')[-1]
        file_name = file_name.split('?')[0]
        if "mp4" not in file_name:
            file_name += ".mp4"

        return {"url": url,
                "file_name": file_name
                }

    def mulitply_download_images(self, images):
        if not isinstance(images, list):
            return
        logger.info(f"图片数量：{len(images)}")
        li = []
        for image_url in images:
            logger.info(f"开始下载图片 网址：{image_url}")
            t = Thread(target=self.download_image, args=(image_url,))
            li.append(t)

        for i in li:
            i.start()
            i.join()

    def get_explore(self, url: str) -> Union[dict, None]:
        content = self.get(url)
        if content is None:
            logger.info("请求失败 获取网页内容为空")
            return
        discovery_dict = parser_discover(content)
        return discovery_dict

    def check_question_status(self, question_id: int) -> bool:
        obj = QuestionModel.get_or_none(QuestionModel.question_id == question_id)
        if obj is None:
            return True
        if obj.status == 0:
            return True
        return False

    def run(self, start: int, end: int):
        logger.info(f"开始爬取 question起始:{start} 和结束：{end}")
        if start == end:
            end += 1

        for i in range(start, end):
            logger.info(f"开始爬取 question:{i}")
            url = f"https://www.xiaohongshu.com/mobile/question/{i}"
            if not self.check_question_status(i):
                logger.info(f"已爬取 question:{i} ")
                continue

            try:
                self.get_question(url)
            except Exception as e:
                logger.error(f"发生异常 question:{i}")
                logger.exception(e)
                continue

            time.sleep(self.interval_frequency)
            logger.info('-' * 100)


def split_list_n_list(origin_list, n):
    if len(origin_list) % n == 0:
        cnt = len(origin_list) // n
    else:
        cnt = len(origin_list) // n + 1

    if cnt >= 10:
        cnt = 10

    for i in range(0, int(len(origin_list) / cnt + 1)):
        yield origin_list[i * cnt:(i + 1) * cnt]


def run(start: int,
        end: int,
        interval_frequency: int = 1,
        save_image: bool = False,
        save_video: bool = False,
        user_agent=None,
        cookie=None):
    s = XiaoHongShuSpider(interval_frequency, save_image, save_video, user_agent, cookie)
    s.run(start, end)


def multiply_run(process_num: int,
                 start: int,
                 end: int,
                 interval_frequency: int = 1,
                 save_image: bool = False,
                 save_video: bool = False):
    print("多进程开始运行")

    li = split_list_n_list(list(range(start, end + 1)), process_num)
    print(F"问题分配完成 process_num:{process_num}")

    pool = Pool(processes=process_num)
    for i in li:

        if len(i) == 0:
            continue
        user_agent, cookie = get_userage_and_cookie()

        args = (i[0],
                i[-1],
                interval_frequency,
                save_image,
                save_video,
                user_agent,
                cookie)

        pool.apply_async(run, args=args)

    pool.close()
    pool.join()
    logger.info("爬取任务完成")


if __name__ == '__main__':

    multiprocessing.freeze_support()
    if c.process_num == 1:
        run(c.start,
            c.end,
            c.interval_frequency,
            c.save_image,
            c.save_video)
    else:
        multiply_run(c.process_num,
                     c.start,
                     c.end,
                     c.interval_frequency,
                     c.save_image,
                     c.save_video)
