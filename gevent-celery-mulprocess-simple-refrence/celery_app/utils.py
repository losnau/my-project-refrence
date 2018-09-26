import telnetlib
from datetime import datetime
from socket import timeout
import logging
from logging import handlers
import os
import redis
import time


def make_logger(app_log_name=None, log_path=None, is_log_file=False):
    # 创建一个日志器logger并设置其日志级别为info
    # os.path.splitext(os.path.basename(__file__))[0]获取绝对路径的文件名
    if not app_log_name:
        app_log_name = "default"
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(process)d - %(name)s - %(lineno)d - %(module)s- %(levelname)s  - %(message)s",
        datefmt="%Y:%m:%d %H:%M:%S %p")
    my_app_logger = logging.getLogger(app_log_name)
    my_app_logger.setLevel(logging.WARNING)
    # file log config
    if is_log_file:
        if not log_path:
            log_path = "./log"
        try:
            os.mkdir(log_path)
        except OSError:
            pass
        log_file_name = os.path.join(log_path, app_log_name, ".log")
        file_size_header = handlers.RotatingFileHandler(log_file_name, maxBytes=104857600, backupCount=5)
        file_size_header.setLevel(logging.INFO)
        file_size_header.setFormatter(formatter)
        my_app_logger.addHandler(file_size_header)
    # 创建一个流处理器handler并设置其日志级别为INFO
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    # 创建一个格式器formatter并将其添加到处理器handler
    handler.setFormatter(formatter)
    # 为日志器logger添加上面创建的处理器handler
    my_app_logger.addHandler(handler)

    return my_app_logger


utils_log = make_logger(app_log_name="utils")


class RedisManage(object):
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 6379
        self.db = 1
        self.pool = None
        self.r = None
        self.pipe = None
        self.init()

    def init(self):
        self.pool = redis.ConnectionPool(host=self.host, port=self.port, db=self.db)
        self.r = redis.StrictRedis(connection_pool=self.pool)
        self.pipe = self.r.pipeline()

    def from_redis_get_key_value(self):
        keys = self.r.keys()
        for key in keys:
            self.pipe.get(key)
            print(self.pipe.execute()[0].decode())

    def count_time(self, count):
        start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        while True:
            time.sleep(0.5)
            keys = self.r.keys()
            if len(keys) == int(count):
                break
        end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return {"start_time": start_time, "end_time": end_time}


class TelnetServerM:
    def __init__(self, ip, port, username, password):
        """
        :param ip: str,server IP
        :param port: int,server Port
        :param username: str,Connect Server Username
        :param password: str,User of Password
        """
        self.ip = ip
        self.port = port
        self.password = password
        self.username = username
        self.tn = None
        self.timeout = 3
        self.telnet_server_login()

    def telnet_server_login(self):
        try:
            tn = telnetlib.Telnet(host=self.ip, port=self.port, timeout=self.timeout)
        except timeout:
            utils_log.error("---------timeout end------login IP:{}\tport:{}".format(self.ip, self.port))
            return False
        except ConnectionRefusedError:
            utils_log.error("------ConnectionRefusedError------login IP:{}\tport:{}".format(self.ip, self.port))
            return False
        except TimeoutError:
            utils_log.error("------TimeoutError-----login IP:{}\tport:{}".format(self.ip, self.port))
            return False
        utils_log.info("telnet login first input username :{}".format(datetime.now()))
        tn.read_until(b"Login:", timeout=self.timeout)
        utils_log.info('First input username:{}\tFirst input password:{}'.format(self.username, self.password))
        tn.write(self.username.encode('gbk') + b"\r\n")
        utils_log.info("telnet login first input password :{}".format(datetime.now()))
        tn.read_until(b"Password:", timeout=self.timeout)
        tn.write(self.password.encode('gbk') + b"\r\n")
        utils_log.info("telnet login second input username :{}".format(datetime.now()))
        tn.read_until(b"Login:", timeout=self.timeout)
        tn.write(self.username.encode('gbk') + b"\r\n")
        utils_log.info("telnet login second input password :{}".format(datetime.now()))
        tn.read_until(b"Password:", timeout=self.timeout)
        tn.write(self.password.encode('gbk') + b"\r\n")
        utils_log.info("telnet login second input password OK last:{}".format(datetime.now()))
        tn.expect(['GS>'.encode('gbk')], 1)
        utils_log.info("telnet login success :{}".format(datetime.now()))
        self.tn = tn
        return True

    def execute_cmd(self, cmd):
        utils_log.debug("真正执行命令：{}".format(cmd))
        if self.tn:
            # self.tn.write(cmd.encode('ascii') + b'\r\n')
            self.tn.write(cmd.encode('gbk') + b'\r\n')
            messages2 = self.tn.expect(['MTS>'.encode('gbk')], 1)
            try:
                # utils_log.info("\n\n真正执行命令：{}\n--------命令捕捉的结果如下--------\n{}".format(cmd, messages2[2].decode(
                #     "gbk")))
                return messages2[2].decode("gbk")
            except KeyError:
                # utils_log.warning("KeyError:{}".format(messages2))
                return messages2
            except UnicodeDecodeError:
                # utils_log.warning("UnicodeDecodeError:{}".format(messages2[2]))
                return messages2[2].decode("gbk", 'replace')
            finally:
                pass
        else:
            # utils_log.info("ip:{},port:{}username:{},telnet is not login".format(self.ip, self.port, self.username))
            return "ip:{},port:{}username:{},telnet is not login".format(self.ip, self.port, self.username)
