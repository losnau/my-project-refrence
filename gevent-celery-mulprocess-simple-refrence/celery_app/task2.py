from celery_app import app
from celery_app.utils import TelnetServerM


@app.task
def execute_cmd(process_info, cmd):
    ip = process_info["process_info"]["game_proc_listen_ip"]
    port = process_info["process_info"]["process_telnet_port"]

    t = TelnetServerM(ip, port, "root", "root")
    cmd_result = t.execute_cmd(cmd)
    process_info.update({"cmd": cmd, "cmd_result": cmd_result})
    return process_info
