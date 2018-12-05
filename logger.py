import logging


def get_logger(logger_name: str, log_level: int = logging.DEBUG) -> logging.Logger:
    """
    ロガーを生成
    :param logger_name:
    :param log_level:
    :return:
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level)
    handler_format = logging.Formatter('%(asctime)s [%(name)s] <%(levelname)s> %(message)s')
    stream_handler.setFormatter(handler_format)

    logger.addHandler(stream_handler)
    return logger
