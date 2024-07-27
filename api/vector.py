import os
import requests
import json
import base64
import datetime
import subprocess

from requests.auth import HTTPBasicAuth

from main import app
import func.apibase as ab
from func.config import cfg

app_name = os.path.splitext(os.path.basename(__file__))[0]
cfga = cfg[app_name]

@app.post("/" + app_name)
async def api_vector(args: dict) -> ab.ApiResponse:
    # 更新したいファイルを一度消す
    url = f"http://{cfga['vector_server']}/delete"
    res = requests.post(url, json=args)

    # 最新のファイルをinputにコピー
    subprocess.run('wsl -e bash /mnt/c/CurrenTTC/user/write.sh', shell=True)

    # vectorデータを更新
    url = f"http://{cfga['vector_server']}/embedding"
    res = requests.post(url, json={})

    return ab.res(0, 'ok')
