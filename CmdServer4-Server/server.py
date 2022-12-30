import threading
import getpass
import socket
import json
import logging
import random
import subprocess

logging.basicConfig(
    format="[%(asctime)s][%(name)s / %(levelname)s]: %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG
)


class cmdServer:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logger = logging.getLogger(__name__)
    tasks = dict()
    clients = {"control": dict(), "controlled": dict()}

    def __init__(self, config):
        self.config = config
        self.logger.debug(self.config)
        # 初始化服务器
        self.logger.info("Starting CmdServer Server ...")
        self.sock.bind(("", self.config["port"]))
        self.sock.listen(self.config["listen"])
        self.logger.info(f"Listening 0.0.0.0:{self.config['port']}")
        # 循环接收请求
        while True:
            sock, addr = self.sock.accept()
            self.logger.info(f"{addr[0]} connected to this server.")
            # 客户端登录
            clientLogin = json.loads(sock.recv(1024))
            if clientLogin["type"] == "ControlledLogin":
                cid = self.get_cid("controlled")
                self.clients["controlled"][cid] = {
                    "cid": cid,
                    "addr": addr,
                    "sock": sock,
                    "data": clientLogin,
                    "thread": threading.Thread(
                        target=lambda: self.controlledReceiveThread(
                            cid,
                            sock))}
                sock.send(json.dumps({"cid": cid}).encode())
                self.clients["controlled"][cid]["thread"].start()
            elif clientLogin["type"] == "ControlLogin":
                cid = self.get_cid("control")
                # 绑定被控端
                try:
                    self.logger.debug(clientLogin)
                    self.logger.debug(self.clients)
                    controlled = self.clients["controlled"][clientLogin["data"]
                                                            ["contronlled_id"]]
                except KeyError as e:
                    self.logger.debug(e)
                    sock.send(json.dumps(
                        {"cid": cid, "code": 404, "msg": "Client Not Found!"}).encode())
                    sock.close()
                else:
                    self.clients["control"][cid] = {
                        "addr": addr,
                        "sock": sock,
                        "data": clientLogin,
                        "controlled": controlled,
                        "thread": threading.Thread(
                            target=lambda: self.controlReceiveThread(
                                cid,
                                sock))}
                    sock.send(json.dumps({"cid": cid, "code": 200}).encode())
                    self.clients["control"][cid]["thread"].start()

    def controlReceiveThread(self, cid, sock):
        logger = logging.getLogger(f"controlled-{cid}")
        while True:
            recv_data = json.loads(sock.recv(2048))
            logger.debug(recv_data)
            # 解析数据
            if recv_data["type"] == "createTask":
                tid = self.get_tid()
                self.tasks[tid] = {"cid": cid}
                recv_data["data"]["tid"] = tid
                recv_data["data"]["cid"] = cid
            # 转发数据
            controlled_id = self.clients["control"][cid]["controlled"]["cid"]
            self.sendMessageTo(
                self.clients["controlled"][controlled_id]["sock"],
                recv_data["type"],
                recv_data
            )

    def sendMessageTo(self, sock, msg_type, message):
        msg = {"type": msg_type}
        msg.update(message)
        if "data" in msg.keys():
            msg.update(msg.pop("data"))
        self.logger.debug(message)
        # 发送
        sock.send(json.dumps(msg).encode())

    def controlledReceiveThread(self, cid, sock):
        logger = logging.getLogger(f"controlled-{cid}")
        while True:
            recv = sock.recv(2048)
            logger.debug(recv)
            recv_data = json.loads(recv)
            logger.debug(recv_data)
            # 转发数据
            self.sendMessageTo(
                self.clients["control"][self.tasks[recv_data["data"]["tid"]]["cid"]]["sock"],
                recv_data["type"],
                recv_data
            )
            # 分析数据
            if recv_data["type"] == "taskFinished":
                self.tasks.pop(recv_data["data"]["tid"])
                self.logger.info(f"Task {recv_data['data']['tid']} finished!")
            # elif recv_data["type"] == "commandOutput":
            #    sock.send(b"done")

    def get_cid(self, client_type):
        cid = ""
        for i in range(5):
            cid += random.choice("1234567890qwertyuiopasdfghjklzxcvbnm")
        # 查重
        if cid in self.clients[client_type].keys():
            return get_cid(client_type)
        else:
            return cid

    def get_tid(self):
        tid = ""
        for i in range(10):
            tid += random.choice("1234567890qwertyuiopasdfghjklzxcvbnm")
        # 查重
        if tid in self.tasks.keys():
            return get_tid()
        else:
            return tid
