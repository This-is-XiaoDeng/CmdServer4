import logging
import server
import json
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
parser.add_argument("-p", "--port", type=int, help="csr server port")
parser.add_argument("-l", "--listen", type=int, help="csr server port")
args = parser.parse_args()
config = json.load(open("./config.json"))
config["port"] = args.port or config["port"]
config["listen"] = args.listen or config["listen"]


def main():
    logger.info(f"CmdServer 4 [Version {parser.version}] Server")
    server.cmdServer(config)
    logger.info("Exited.")


if __name__ == "__main__":
    main()
