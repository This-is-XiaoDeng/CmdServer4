import logging
import server
import json
import update_checker
import argparse

logging.basicConfig(
    format="[%(asctime)s][%(name)s / %(levelname)s]: %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO
)
logger = logging.getLogger(__name__)
parser = argparse.ArgumentParser(description="A server of commands.")
parser.version = "4.0.1"
parser.add_argument("-v", "--version", action="version")
parser.add_argument("-p", "--password", help="Control connect password")
args = parser.parse_args()
config = json.load(open("./config.json"))


def main():
    logger.info(f"CmdServer 4 [Version {parser.version}] Controlled")
    if config["check_update"]:
        update_checker.check_update(parser.version)
    # 启动服务
    logger.info("Starting CmdServer Controlled Client")
    server.CMDServerControlled(config)


if __name__ == "__main__":
    if args.password:
        config["password"] = args.password
    main()
