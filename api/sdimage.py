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
async def api_sdimage(args: dict) -> ab.ApiResponse:
    dt = datetime.datetime.now()

    # sdforge
    url = f"http://{cfga['sdimage_server']}/sdapi/v1/txt2img"
    res = requests.post(url, json=args)
    r = res.json()
    image = base64.b64decode(r['images'][0])
    files = {'file': image}

    # safetychecker
    url = f"http://{cfga['safetychecker_server']}/check"
    res = requests.post(url, files=files)
    r = res.json()

    # katanuki
    url = f"http://{cfga['katanuki_server']}/katanuki"
    res = requests.post(url, files=files)
    if res.content:
        image = res.content

    # log
    ts = dt.strftime(cfga['logfile_format'])
    h = "_h" if r["has_nsfw"] else ""
    path = f"{cfga['output_dir']}/{ts}{h}.webp"
    with open(path, 'wb') as f:
        f.write(image)

    if r['has_nsfw']:
        return ab.res(2, 'nsfw')

    # overwrite. display for OBS
    with open(cfga['sd_image_path'], 'wb') as f:
        f.write(image)

    print(datetime.datetime.now() - dt)

    return ab.res(0, 'ok')
