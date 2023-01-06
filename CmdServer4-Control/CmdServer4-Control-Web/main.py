import logging
import socket
import json
import hashlib
import threading
import flask
import argparse

logging.basicConfig(
    format="[%(asctime)s][%(name)s / %(levelname)s]: %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)
parser = argparse.ArgumentParser(description="A server of commands.")
parser.version = "4.0.1"
parser.add_argument("-v", "--version", action="version")
parser.add_argument("-p", "--password", help="Controlled Password")
parser.add_argument("cid", help="csr controlled client id")
args = parser.parse_args()
config = json.load(open("./config.json"))


class CMDServerClient:

    def __init__(self):
        # 初始化变量
        self.logger = logging.getLogger("core")
        self.recv_data = []
        self.app = flask.Flask(__name__)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # TODO web主页
        self.app.add_url_rule(
            "/send",
            "sendCommand",
            self.sendCommand,
            methods=[
                "GET",
                "POST"])
        if self.connect(args.password):
            threading.Thread(target=self.getReceive).start()
            self.app.run(host="0.0.0.0", port=config["local_server_port"])

    def connect(self, password = None):
        self.logger.info(
            f"Connecting to {config['server']['ip']}:{config['server']['port']} ...")
        self.sock.connect((config['server']['ip'], config['server']['port']))
        self.logger.info("Server connected!")
        # 登录
        if password is not None:
            encodedPassword = hashlib.sha1(password.encode("utf-8")).hexdigest()
        else:
            encodedPassword = None
        self.send(
            "ControlLogin",
            {
                "controlled_id": args.cid,
                "password": encodedPassword
            }
        )
        recv_data = json.loads(self.sock.recv(1024))
        if recv_data["code"] == 200:
            return True
        elif recv_data["code"] == 403:
            self.logger.warning("Wrong Password")
            self.sock.close()
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connect(input("Password: "))
        else:
            self.logger.error(f"Falied to login: {recv_data['msg']}")
            self.logger.debug(recv_data)
        return False

    def send(self, msg_type, message):
        self.sock.send(
            json.dumps(
                {
                    "type": msg_type,
                    "data": message
                }
            ).encode()
        )

    def getReceive(self):
        while True:
            self.recv_data += [json.loads(self.sock.recv(2048))]

    def getOutput(self):
        output = ""
        tid = None
        while True:
            length = 0
            for recv in self.recv_data:
                self.logger.debug(recv)
                if recv["type"] == "createdTask" and tid is None:
                    tid = recv["tid"]
                    self.recv_data.pop(length)
                elif recv["type"] == "commandOutput" and recv["tid"] == tid:
                    output += recv["text"]
                    self.recv_data.pop(length)
                elif recv["type"] == "taskFinished" and recv["tid"] == tid:
                    self.recv_data.pop(length)
                    return output

    def sendCommand(self):
        """if flask.requests.method == "POST":
            command = flask.request.from("command")
            cwd = flask.request.from("cwd")
        else:"""
        command = flask.request.args.get("command")
        cwd = flask.request.args.get("cwd")
        self.send("createTask", {"command": command, "cwd": cwd})
        self.logger.debug(command)
        output = self.getOutput()
        return output


if __name__ == "__main__":
    logger.info(f"CmdServer [Version {parser.version}] Control Web")
    CMDServerClient()
