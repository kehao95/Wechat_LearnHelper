__author__ = 'kehao'
import requests

url = "http://127.0.0.1:5000"


def get(data=None, url=url):
    r = requests.get(url)
    print(r.status_code)
    print(r.content)


def post(data=None, url=url):
    r = requests.post(url, data)
    print(r.status_code)
    print(r.content)


if __name__ == "__main__":
    # get(url="http://127.0.0.1:5000")
    # get(url="http://127.0.0.1:5000/123")
    # get(url="http://127.0.0.1:5000/token/123")
    # get(url="http://127.0.0.1:5000/?id=23")
    data = '<xml><ToUserName><![CDATA[gh_271b17ee3580]]></ToUserName>\n<FromUserName><![CDATA[okHWgw6aLgj_RptXWJyDs-Emmw4A]]></FromUserName>\n<CreateTime>1445250786</CreateTime>\n<MsgType><![CDATA[text]]></MsgType>\n<Content><![CDATA[\xe6\x96\x87\xe5\xad\x97]]></Content>\n<MsgId>6207304860788332824</MsgId>\n</xml>'
    post(data=data, url="http://127.0.0.1:5000")
    #get(url="http://127.0.0.1:5000?echostr=hello")
