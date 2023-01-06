import threading
import getpass
import socket
import json
import logging
import subprocess
import time
import hashlib

logging.basicConfig(
    format="[%(asctime)s][%(name)s / %(levelname)s]: %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG
)


class CMDServerControlled:
    def __init__(self, config):
        # 初始化变量
        self.logger = logging.getLogger(__name__)
        self.task = dict()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.config = config
        # 连接服务器
        self.connect(self.config["cid"])
        # 启动循环
        self.execute()

    def connect(self, cid=None):
        # 连接中心服务器
        self.logger.debug(self.config)
        self.logger.info(
            f"Connecting to {self.config['server']['host']}:{self.config['server']['tcp_port']} ...")
        self.sock.connect(
            (self.config["server"]["host"],
             self.config["server"]["tcp_port"]))
        self.logger.info("Server connected.")
        # 登录服务器
        loginMessage = {"user": getpass.getuser(), "password": None, "cid": cid}
        if self.config["password"]:
            loginMessage["password"] = hashlib.sha1(self.config["password"].encode("utf-8")).hexdigest()
        self.send("ControlledLogin", loginMessage)
        self.clientData = json.loads(self.sock.recv(1024))
        self.logger.debug(self.clientData)
        self.logger.info(
            f"CmdServer started, client id: {self.clientData['cid']}")

    def createTask(self, cid, tid, command, cwd):
        # 创建任务
        logger = logging.getLogger(f"{cid}-{tid}")
        logger.info(f"{cid} created task {tid}: {command}")
        try:
            self.task[tid]["subprocess"] = subprocess.Popen(
                args=command,
                shell=True,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
        except Exception as e:
            self.send("taskCreateError", {"tid": tid, "msg": str(e)})
            self.send("taskFinished", {"tid": tid})
        
        # 获取输出
        while True:
            # 获取输出
            buffer = self.task[tid]["subprocess"].stdout.readline()
            try:
                buffer = buffer.decode("utf-8")
            except BaseException:
                buffer = buffer.decode("gbk")
            # 分析数据
            if buffer == "" and self.task[tid]["subprocess"].poll() is not None:
                break
            logger.info(buffer)
            self.send("commandOutput", {"text": buffer, "tid": tid})
            # 延迟防卡死
            time.sleep(0.03)
        self.send("taskFinished", {"tid": tid})

    def execute(self):
        while True:
            try:
                data = json.loads(self.sock.recv(2048))
                self.logger.debug(data)
                
                # 创建服务
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
                # 输入文本
                elif data["type"] == "textInput":
                    self.task[data["tid"]]["subprocess"].communicate(
                        self, data["text"], 0)
                    self.send("inputedText", {"tid": data["tid"]})
                # 杀死任务
                elif data["type"] == "killTask":
                    self.task[data["tid"]]["subprocess"].kill()

            except Exception as e:
                self.logger.error(e)
                try:
                    self.sock.close()
                except:
                    pass
                self.logger.error("Disconnected, reconnecting . . .")
                self.connect()


    def send(self, msg_type, message=None):
        self.logger.debug(f"Sending [{msg_type}] {message} ...")
        self.sock.send(
            json.dumps(
                {"type": msg_type, "data": message}
            ).encode("utf-8")
        )
