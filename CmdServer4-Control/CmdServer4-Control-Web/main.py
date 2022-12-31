import logging
import socket
import json
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
parser.version = "4.0.0"
parser.add_argument("-v", "--version", action="version")
parser.add_argument("cid", help="csr controlled client id")
args = parser.parse_args()
config = json.load(open("./config.json"))


class cmdServerClient:
    logger = logging.getLogger("core")
    recv_data = []
    app = flask.Flask(__name__)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __init__(self):
        # TODO web主页
        self.app.add_url_rule(
            "/send",
            "send_command",
            self.send_command,
            methods=[
                "GET",
                "POST"])
        self.logger.info(
            f"Connecting to {config['server']['ip']}:{config['server']['port']} ...")
        self.sock.connect((config['server']['ip'], config['server']['port']))
        self.logger.info("Server connected!")
        # 登录
        self.send("ControlLogin", {"contronlled_id": args.cid})
        recv_data = json.loads(self.sock.recv(1024))
        if recv_data["code"] == 200:
            threading.Thread(None, self.getReceive).start()
            self.app.run(host="127.0.0.1", port=config["local_server_port"])
        else:
            self.logger.error(f"Falied to login: {recv_data['msg']}")
            self.logger.debug(recv_data)

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

    def send_command(self):
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
    cmdServerClient()
