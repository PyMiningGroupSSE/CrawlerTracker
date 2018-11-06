import json
import requests
import threading
import configobj
import tasklist
import logging
import time
import socket
from urllib.parse import urlparse
from msg_socket import MsgSocket
from nodelist import NodeInfo, NodeList
from flask import Flask, render_template, jsonify
from mongodb import MongoDb

# define request command strings
__CMD_CONNECT__ = "connect"
__CMD_TASK__ = "task"
__CMD_XPATH__ = "xpath"
__CMD_SUBMIT__ = "submit"
__CMD_EXIT__ = "exit"

# define connection status codes
__CODE_CONN_SUCCESS__ = 100
__CODE_CONN_FAILED__ = 101
__CODE_TASK_SUCCESS__ = 200
__CODE_TASK_FAILED__ = 201
__CODE_TASK_EMPTY__ = 210
__CODE_XPATH_SUCCESS__ = 300
__CODE_XPATH_FAILED__ = 301
__CODE_SUBMIT_SUCCESS__ = 400
__CODE_SUBMIT_FAILED__ = 401
__CODE_SUBMIT_EXIT__ = 410

# define connection macros
__BACKLOG__ = 20
__BUFF_SIZE__ = 4096

# define config file
__conf__ = configobj.ConfigObj("config.ini", encoding="UTF-8")

# TaskList
__tasklist__ = tasklist.TaskList(timeout=30)
__xpaths__ = json.load(open(__conf__["xpaths"]["path"], "r"))

__nodelist__ = NodeList()
__flask_app__ = Flask(__name__)

# MongoDB
host = __conf__["mongodb"]["host"]
port = __conf__["mongodb"]["port"]
user = pwd = None
if "user" in __conf__["mongodb"] and __conf__["mongodb"]["user"]:
    user = __conf__["mongodb"]["user"]
if "pass" in __conf__["mongodb"] and __conf__["mongodb"]["pass"]:
    pwd = __conf__["mongodb"]["pass"]
__mongo__ = MongoDb(host, port, user, pwd)


def main():
    threading.Thread(target=fetch_urls).start()
    msgsock = MsgSocket()
    msgsock.bind(__conf__["server"]["bind_addr"], __conf__["server"]["bind_port"])
    msgsock.listen(50)
    while True:
        try:
            conn, address = msgsock.accept()
            msg = json.loads(conn.recv_msg())
        except:
            continue
        if msg["cmd"] == __CMD_CONNECT__ and msg["id"] not in __nodelist__.get_ids():
            __nodelist__.append(NodeInfo(msg["id"], address[0]))
            print("client '{0}' connected".format(address[0]))
            threading.Thread(target=server, args=(conn, msg["id"])).start()
            res = dict(id=msg["id"], status=__CODE_CONN_SUCCESS__,
                       info="success", data="")
        else:
            res = dict(id=msg["id"], status=__CODE_CONN_FAILED__,
                       info="id already taken", data="")
        conn.send_msg(json.dumps(res))


def fetch_urls():
    entries = __conf__["entries"]
    page = int(__conf__["states"]["entry_page"])
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8"
    }
    while True:
        if __tasklist__.length() > 200:
            time.sleep(1)
            continue
        logging.info("fetching new tasks")
        for key in entries.keys():
            news_urls = list()
            data = requests.get(entries[key].format(50, page), headers=headers).json()
            for news_item in data["result"]["data"]:
                if urlparse(news_item["url"]).netloc not in __xpaths__.keys():
                    continue
                news_urls.append(key + "|" + news_item["url"])
            __tasklist__.add_tasks(news_urls)
            time.sleep(1)
        page += 1
        __conf__["states"]["entry_page"] = str(page)
        __conf__.write()


def server(cli_conn, cli_id):
    cli_conn.settimeout(300)
    while True:
        try:
            msg = cli_conn.recv_msg()
        except socket.timeout:
            msg = None
        if msg is None:
            break
        else:
            msg = json.loads(msg)
        if msg["cmd"] == __CMD_TASK__:
            tasks = __tasklist__.get_tasks(int(msg["data"]["count"]))
            logging.info("dispatch tasks '{}' to client '{}'".format(tasks, cli_id))
            if tasks is not None:
                res = dict(id=msg["id"], status=__CODE_TASK_SUCCESS__,
                           info="success", data={"urls": tasks})
            else:
                res = dict(id=msg["id"], status=__CODE_TASK_EMPTY__,
                           info="empty", data={"urls": []})
            cli_conn.send_msg(json.dumps(res))
        elif msg["cmd"] == __CMD_XPATH__:
            host = msg["data"]["host"]
            if host in __xpaths__.keys():
                res = dict(id=msg["id"], status=__CODE_XPATH_SUCCESS__,
                           info="success", data={host: __xpaths__[host]})
            else:
                res = dict(id=msg["id"], status=__CODE_XPATH_FAILED__,
                           info="failed", data="")
            cli_conn.send_msg(json.dumps(res))
        elif msg["cmd"] == __CMD_SUBMIT__:
            logging.info("preparing to receive data")
            artilist = msg["data"]["artilist"]
            if artilist is not None:
                res = dict(id=msg["id"], status=__CODE_SUBMIT_SUCCESS__,
                           info="success", data="")
                cli_conn.send_msg(json.dumps(res))
            else:
                res = dict(id=msg["id"], status=__CODE_SUBMIT_FAILED__,
                           info="failed", data="")
                cli_conn.send_msg(json.dumps(res))
                continue
            __nodelist__.get_node(cli_id).add_count(len(artilist))
            done_list = list()
            for item in artilist:
                done_list.append(item["type"] + "|" + item["url"])
                if item["title"] is not None:
                    __mongo__.put_news(item)
            __tasklist__.done_tasks(done_list)
    __nodelist__.remove(cli_id)
    logging.info("client '{}' disconnected".format(cli_id))


@__flask_app__.route("/")
def flask_home():
    return render_template("status.html", nodelist=__nodelist__.get_list(), total_cnt=__mongo__.get_news_count())


@__flask_app__.route("/api/v1/nodes", methods=["GET"])
def flask_api_nodes():
    return __generate_json__(True, data=__nodelist__.get_dict())


@__flask_app__.route("/api/v1/newscount", methods=["GET"])
def flask_api_tasks():
    return __generate_json__(True, data={"totalCount": __mongo__.get_news_count()})


def __generate_json__(status, info=None, token=None, data=None):
    ret_dict = dict(
        status="success" if status else "error",
        info=info,
        token=None if token is None else str(token, encoding="utf-8"),
        data=data
    )
    return jsonify(ret_dict)


if __name__ == '__main__':
    threading.Thread(target=main).start()
    logging.basicConfig(level=logging.WARNING)
    __flask_app__.debug = False
    __flask_app__.run(host="0.0.0.0", port=25316)
