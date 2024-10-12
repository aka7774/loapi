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
async def api_log(args: dict) -> ab.ApiResponse:
    dt = datetime.datetime.now()
    
    os.makedirs(cfga['log_dir'], exist_ok=True)
    log_path = f"{cfga['log_dir']}/{dt.strftime(cfga['logfile_format'])}.log"
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"[{dt.strftime('%H:%M:%S')}]\n")
        f.write(f"{args.get('timestamp')}\n")
        f.write(f"{args.get('userid')}\n")
        f.write(f"{args.get('name')}\n")
        f.write(f"{args.get('comment')}\n")
        f.write("--------\n")
        f.write(f"{args.get('prompt')}\n")
        f.write("--------\n")
        #response = '\n'.join(filter(lambda x: x.strip(), map(lambda x: x.strip(), args['response'].split('\n'))))
        f.write(f"{args.get('response')}\n")
    return ab.res(0, 'ok.')
