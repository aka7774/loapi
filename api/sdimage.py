import os
import requests
import json
import base64
import datetime
import io
import math
from PIL import Image

from requests.auth import HTTPBasicAuth

from main import app
import func.apibase as ab
from func.config import cfg

app_name = os.path.splitext(os.path.basename(__file__))[0]
cfga = cfg[app_name]

@app.post("/" + app_name)
async def api_sdimage(args: dict) -> ab.ApiResponse:
    dt = datetime.datetime.now()

    # 強制モザイクモード
    # force_mosaic = False
    # if 'force_mosaic' in args:
        # force_mosaic = True
        # del args['force_mosaic']

    # if 'server' in args:
        # cfga['sdimage_server'] = args['server']
        # del args['server']

    # # sdforge
    # url = f"{cfga['sdimage_server']}/sdapi/v1/txt2img"
    # res = requests.post(url, json=args)
    # r = res.json()
    # image = base64.b64decode(r['images'][0])
    image = base64.b64decode(args['image_b64'])
    files = {'file': image}

    ts = dt.strftime(cfga['logfile_format'])

    # 背景透過前の画像を保存
    # path = f"{cfga['output_dir']}/{ts}_m.webp"
    # with open(path, 'wb') as f:
        # f.write(image)

    # safetychecker
    url = f"http://{cfga['safetychecker_server']}/check"
    res = requests.post(url, files=files)
    r = res.json()

    # katanuki
    # url = f"http://{cfga['katanuki_server']}/katanuki"
    # res = requests.post(url, files=files)
    # if res.content:
        # image = res.content

    # log
    h = ""
    if r["has_nsfw"]:
        h = "_h"
    if args['force_mosaic']:
        h = "_c"
    path = f"{cfga['output_dir']}/{ts}{h}.webp"
    with open(path, 'wb') as f:
        f.write(image)

    # jsでmosaicできないので妥協
    if r['has_nsfw'] or args['force_mosaic']:
        res = {
            'image_b64': base64.b64encode(mosaic(image)).decode('ascii'),
            'has_nsfw': r['has_nsfw'],
        }
        return ab.res(2, 'nsfw', res)

    print(datetime.datetime.now() - dt)

    res = {
        'image_b64': base64.b64encode(image).decode('ascii'),
        'has_nsfw': r['has_nsfw'],
    }
    return ab.res(0, 'ok', res)

def mosaic(image_bin):
    image = Image.open(io.BytesIO(image_bin))

    if image.width < image.height:
        image_min = image.width
    else:
        image_min = image.height
    intensity = math.ceil(image_min / 100)

    # 画像サイズをintensity分の1に縮小
    small = image.resize(
        (round(image.width / intensity), round(image.height / intensity))
    )

    # 元画像のサイズに拡大してモザイク処理
    result = small.resize(
        (image.width, image.height),
        resample=Image.NEAREST # 最近傍補間
    )

    output = io.BytesIO()
    result.save(output, format='webp')
    result_bin = output.getvalue()

    return result_bin
