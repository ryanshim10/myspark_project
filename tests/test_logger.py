from app.services.logger import setup_logger
from loguru import logger


def test_logger(tmp_path):
    setup_logger(tmp_path)
    logger.info("hello")
    assert (tmp_path / "app.log").exists()
