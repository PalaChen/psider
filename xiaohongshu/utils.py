import re


def get_image_file_name(url: str) -> str:
    pattern = re.compile("(http|https://.*.com)/(.*)")
    res = pattern.search(url).group(2)
    return res


def t():
    urls = ["https://sns-img-qc.xhscdn.com/a68b2d75-86c0-0ce1-fd99-b67dbbab9ca3",
            "https://sns-img-hw.xhscdn.com/b3a1f34f-d071-9c6b-9047-f9744bdeaf3b",
            "https://sns-img-hw.xhscdn.com/0302b101kj2vzu1so7r070pdgy2d3260ax",
            ]
    for url in urls:
        print(get_image_file_name(url))


if __name__ == '__main__':
    # t()
    import hashlib
    url='https://sns-img-qc.xhscdn.com/a68b2d75-86c0-0ce1-fd99-b67dbbab9ca3'

