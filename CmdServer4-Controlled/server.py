import threading
import getpass
import socket
import json
import logging
import subprocess
import time
import traceback

logging.basicConfig(
    format="[%(asctime)s][%(name)s / %(levelname)s]: %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG
)


class cmdServerControlled:
    logger = logging.getLogger(__name__)
    task = dict()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self, config):
        self.config = config
        # 连接中心服务器
        self.logger.debug(self.config)
        self.logger.info(
            f"Connecting to {self.config['server']['host']}:{self.config['server']['tcp_port']} ...")
        self.sock.connect(
            (self.config["server"]["host"],
             self.config["server"]["tcp_port"]))
        self.logger.info("Server connected.")
        # 获取信息
        self.send("ControlledLogin", {"user": getpass.getuser()})
        self.clientData = json.loads(self.sock.recv(1024))
        self.logger.debug(self.clientData)
        self.logger.info(
            f"CmdServer started, client id: {self.clientData['cid']}")
        # 启动循环
        self.execute()

    def createTask(self, cid, tid, command, cwd):
        logger = logging.getLogger(f"{cid}-{tid}")
        logger.info(f"{cid} created task {tid}: {command}")
        self.task[tid]["subprocess"] = subprocess.Popen(
            args=command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        while True:
            # try:
            buffer = self.task[tid]["subprocess"].stdout.readline()
            try:
                buffer = buffer.decode("utf-8")
            except BaseException:
                buffer = buffer.decode("gbk")

            if buffer == "" and self.task[tid]["subprocess"].poll(
            ) is not None:
                break
            logger.info(buffer)
            self.send("commandOutput", {"text": buffer, "tid": tid})
            # 延迟防卡死
            time.sleep(0.03)
        self.send("taskFinished", {"tid": tid})

    def execute(self):
        while True:
            data = json.loads(self.sock.recv(2048))
            self.logger.debug(data)
            # 解析数据
            if data["type"] == "createTask":
                self.task[data["tid"]] = {}
                self.task[data["tid"]]["thread"] = threading.Thread(
                    target=self.createTask,
                    args=(data["cid"], data["tid"], data["command"], data["cwd"])
                )
                self.task[data["tid"]]["thread"].start()
                self.send(
                    "createdTask", {
                        "tid": data["tid"], "cid": data["cid"]})
            elif data["type"] == "textInput":
                self.task[data["tid"]]["subprocess"].communicate(
                    self, data["text"], 0)
                self.send("inputedText", {"tid": data["tid"]})
            elif data["type"] == "killTask":
                self.task[data["tid"]]["subprocess"].kill()

    def send(self, msg_type, message=None):
        self.logger.debug(f"Sending [{msg_type}] {message} ...")
        self.sock.send(
            json.dumps(
                {"type": msg_type, "data": message}
            ).encode("utf-8")
        )
