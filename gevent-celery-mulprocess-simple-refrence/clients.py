from celery_app import task1
from celery_app import task2
from celery_app.utils import TelnetServerM, RedisManage
import json
from datetime import datetime
from multiprocessing import Pool, Manager
import gevent
from gevent import monkey


def test_celery():
    """
    测试 task1

    :return:
    """
    for i in range(10):
        task1.num_add.apply_async(args=[i, i + 1])


def test_client_execute_cmd():
    """
     task2测试

    :return:
    """
    test_data = {'server_name': '锋芒', 'process_info': {'game_proc_id': '4952', 'game_proc_name': 'GS1',
                                                       'current_group_id_game_proc_name': '373_GS1',
                                                       'process_is_enable': True, 'game_proc_listen_ip': '172.19.1.86',
                                                       'process_telnet_port': 9920, 'process_connect_user': 'root',
                                                       'process_connect_password': 'root'}}

    task2.execute_cmd.apply_async(args=[test_data, execute_cmd])

    # def delete_all_key(self):
    #     for key in self.r.keys():
    #         self.r.remove(key)


def client_execute_cmd(datas):
    """
    task2真正运行，使用异步任务celery运行

    :param datas: dict
    :return:
    """
    for i in datas:
        task2.execute_cmd.apply_async(args=[i, execute_cmd])
    return True


def my_fuc(process_info, cmd, queue=None):
    """
    一个基础的twt类用法

    :param process_info:dict
    :param cmd:
    :param queue: pool queue
    :return:
    """
    ip = process_info["process_info"]["game_proc_listen_ip"]
    port = process_info["process_info"]["process_telnet_port"]
    t = TelnetServerM(ip, port, "root", "root")
    cmd_result = t.execute_cmd(cmd)
    process_info.update({"cmd": cmd, "cmd_result": cmd_result})
    if queue is not None:
        queue.put(process_info)
    return process_info


def normoal_execute(datas):
    """
    顺序执行

    :param datas:
    :return:
    """

    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S"')
    for i in datas:
        print(i)
        my_fuc(i, execute_cmd)

    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S"')
    return {"start_time": start_time, "end_time": end_time}


def mul_func(datas):
    """
    多进程版本

    :param datas:
    :return:
    """
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S"')
    pool = Pool(4)
    mul_queue = Manager().Queue()
    length = 0
    for i in datas:
        length = length + 1
        pool.apply_async(my_fuc, args=(i, execute_cmd, mul_queue))
    tmp_num = 0
    while tmp_num < length:
        # print(mul_queue.get())
        mul_queue.get()
        tmp_num += 1
        rate = tmp_num / length
        rate = "进度:%.2f%%\n" % (rate * 100)
        print(rate, end="\t")
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S"')
    return {"start_time": start_time, "end_time": end_time}


def gevent_execute(datas):
    """
    gevent版本

    :param datas:
    :return:
    """
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S"')
    jobs = []

    for i, item in enumerate(datas):
        print(i)
        jobs.append(gevent.spawn(my_fuc, item, execute_cmd, None))

    gevent.joinall(jobs, timeout=3, count=4, raise_error=False)
    for job in jobs:
        print(job.get())
    end_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S"')
    return {"start_time": start_time, "end_time": end_time}


def settle_data(datas):
    """
    数据整理

    :param datas:
    :return:
    """
    server_gs = []
    for i in datas:
        # print(i["server_name"])
        if i["server_name"] in test_server:
            for j in i["processes"]:
                # print(j)
                # continue
                if "GS" in j["game_proc_name"]:
                    server_gs.append({"server_name": i["server_name"], "process_info": j})
    return server_gs


if __name__ == "__main__":
    execute_cmd = "cmd.ls()"
    test_server = ["锋芒", "宏图", "如意"]
    with open("20180926", "r") as f:
        text_content = f.read()
    data = json.loads(text_content)
    data = settle_data(data)

    normal_time = normoal_execute(data)

    mul_process_time = mul_func(data)
    # {'normal_time': {'start_time': '2018-09-26 19:42:07"', 'end_time': '2018-09-26 19:42:56"'},
    #  'mul_process_time': {'start_time': '2018-09-26 19:42:56"', 'end_time': '2018-09-26 19:43:08"'}}
    # 'celery_time': {'start_time': '2018-09-26 19:43:08', 'end_time': '2018-09-26 19:43:21'}}
    print({"normal_time": normal_time,
           "mul_process_time": mul_process_time,
           })

    client_execute_cmd(data)
    rm = RedisManage()
    # 从redis里面获取数据并且判断异步是否执行完成
    celery_time = rm.count_time(len(data))
    # rm.delete_all_key()

    print({"normal_time": normal_time,
           "celery_time": celery_time
           })
    monkey.patch_all()  # 对程序中的IO操作进行标记
    gevent_time = gevent_execute(data)
    print({"normal_time": normal_time,
           "gevent_time": gevent_time
           })

    """
    {'normal_time': {'start_time': '2018-09-26 21:33:05"', 'end_time': '2018-09-26 21:33:53"'},
    'mul_process_time': {'start_time': '2018-09-26 21:33:53"', 'end_time': '2018-09-26 21:34:05"'}}
     'celery_time': {'start_time': '2018-09-26 21:34:05', 'end_time': '2018-09-26 21:34:18'}}
   'gevent_time': {'start_time': '2018-09-26 21:34:18"', 'end_time': '2018-09-26 21:34:21"'}}
    """
