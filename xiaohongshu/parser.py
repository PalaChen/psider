import copy
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re


def end(expire: int):
    n = datetime.now().timestamp()
    e = copy.deepcopy(expire)
    if e - n < 0:
        print("试用期结束")
        raise Exception


def parser_question(content: str):
    soup = BeautifulSoup(content, 'lxml')
    div_ele = soup.find("div", {"class": "date-group"})
    question = None
    if div_ele:
        question = div_ele.text

    div_eles = soup.find_all("div", {"class": "report-item"})
    final_li = []
    for div_ele in div_eles:
        title_ele = div_ele.find("div", {"class": "title"})
        name_ele = div_ele.find("span", {"class": "name"})
        up_ele = div_ele.find("div", {"class": "thumb-up"})
        name = None
        goods = None
        url = None
        if title_ele:
            url = title_ele.parent.get("href")
        if name_ele:
            name = name_ele.text
        if up_ele.text:
            goods = up_ele.text

        # print(f"{name} url:{url} 点赞数：{goods}")
        temp_dict = {
            "name": name,
            "goods": goods,
            "url": url,
        }
        final_li.append(temp_dict)
    return question, final_li


def parser_discover_by_wap(content: str):
    soup = BeautifulSoup(content, "lxml")
    # script=soup.find("script",{"type":"application/ld+json"})
    # print(script)
    pattern = re.compile('<script\ type="application/ld\+json">([\w\W]*?)</script>')
    res = pattern.search(content)

    if not res:
        return
    res = res.group(1)

    # desc_ele=soup.find("div",{"class":"desc"})
    # print(desc_ele.text)
    div_eles = soup.select("div.reds-text.color-l")
    link_num = None
    collect_num = None
    commemt_num = None
    if len(div_eles) > 0:
        div_ele = div_eles[0]

        action_li = div_ele.select("div.y-middle")
        for i, action_ele in enumerate(action_li):
            if i > 1:
                break
            if i == 0:
                link_num = action_ele.text.rstrip("+")
            if i == 1:
                collect_num = action_ele.text.rstrip("+")

    div_eles = soup.select("div.reds-text.fs15.comment-count")
    if len(div_eles) > 0:
        div_ele = div_eles[0]
        commemt_num = div_ele.text.rstrip("条精选评论").rstrip("+")
    # print(f"点赞：{link_num} 收藏：{collect_num}")
    temp_dict = {
        "name": res['name'],
        "thumbnailUrl": res['thumbnailUrl'],
        "datePublished": res['datePublished'],
        "author": res['author']['name'],
        "link_num": link_num,
        "collect_num": collect_num

    }
    # print(temp_dict)


def parser_discover(content: str):
    pattern = re.compile('<script>window.__INITIAL_STATE__=([\w\W]*?)</script>')
    res = pattern.search(content)

    if not res:
        return
        # pattern = re.compile('<script>window.__INITIAL_STATE__=([\w\W]*?)</script>')
        # res = pattern.search(content)

    res = res.group(1)
    res = res.replace("undefined", "null")

    res = json.loads(res)

    note_dict = res['note']['note']
    if not note_dict:
        return None
    imageList = note_dict.get('imageList', [])
    li = []
    for t in imageList:
        li.append(t['url'].replace("\u002F", "/"))

    video = None
    stream = note_dict.get('video', {}).get("media", {}).get("stream", {})
    if isinstance(stream, dict):
        for k, v in stream.items():
            if len(v) == 0:
                continue
            video = v[0].get("masterUrl")
    final_dict = {
        "description": note_dict['desc'],
        "liked_count": note_dict['interactInfo']['likedCount'],
        "collected_count": note_dict['interactInfo']['collectedCount'],
        "comment_count": note_dict['interactInfo']['commentCount'],
        "note_id": note_dict['noteId'],  # 笔记id
        "title": note_dict['title'],
        "user_id": note_dict['user']['userId'],
        "nickname": note_dict['user']['nickname'],
        "images": li,
        "video": video
    }

    return final_dict


def t():
    with open("./html/1.html", 'r', encoding='utf-8') as f:
        data = f.read()
    print(parser_question(data))


def t2():
    with open("html/6401644f0000000013030751.html", 'r', encoding='utf-8') as f:
        data = f.read()
    res = parser_discover(data)
    print(res)


if __name__ == '__main__':
    # t()
    t2()
