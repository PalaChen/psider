import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

headers = {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
}


def parser(content: str) -> dict:
    soup = BeautifulSoup(content, 'lxml')
    title = soup.find('title').text
    div = soup.find("div", {"class": "lesson"})
    return {"title": title, "content": str(div)}


def spider(nid:int):
    url = urljoin("https://3yya.com/lesson/", str(nid))
    response = requests.get(url, headers=headers)
    status_code = response.status_code
    print(f"nid:{nid} status_code:{status_code}")
    if status_code == 404:
        return

    content = response.text
    print(parser(content))


def main():
    for i in range(1, 96):
        spider(i)


if __name__ == '__main__':
    # spider("https://3yya.com/lesson/91")
    main()
