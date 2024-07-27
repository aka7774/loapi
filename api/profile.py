import os
import requests
import json
import base64
import datetime

from requests.auth import HTTPBasicAuth

from main import app
import func.apibase as ab
from func.config import cfg

app_name = os.path.splitext(os.path.basename(__file__))[0]
cfga = cfg[app_name]

@app.post("/" + app_name)
async def api_profile(args: dict) -> ab.ApiResponse:
    dt = datetime.datetime.now()
    
    os.makedirs(cfga['profile_dir'], exist_ok=True)
    print(args['user_id'])
    log_path = f"{cfga['profile_dir']}/{args['user_id']}.log"
    if not os.path.exists(log_path):
        return ab.res(0, '')
    with open(log_path, 'r', encoding='utf-8') as f:
        profile = f.read()

    txt_path = f"{cfga['profile_dir']}/{args['user_id']}.txt"
    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            profile += f.read()

    print(profile)

    return ab.res(0, profile)
