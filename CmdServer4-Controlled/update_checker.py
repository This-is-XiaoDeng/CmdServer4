import logging

logging.basicConfig(
    format="[%(asctime)s][%(name)s / %(levelname)s]: %(message)s",
    datefmt="%Y-%m-%D %H:%M:%S",
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)


def check_update(client_version):
    # TODO 自动检查更新
    pass
