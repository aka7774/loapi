import os
import requests
import json
import base64
import datetime
import io
from PIL import Image

from requests.auth import HTTPBasicAuth

from main import app
import func.apibase as ab
from func.config import cfg

app_name = os.path.splitext(os.path.basename(__file__))[0]
cfga = cfg[app_name]

@app.post("/" + app_name)
async def api_animagine(args: dict) -> ab.ApiResponse:
    words = []
    path = cfga['dic_path']
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            for word in line.split(','):
                word = word.strip()
                if not word in words:
                    words.append(word)

    s = args['prompt']
    for word in words:
        s = s.replace(word, '')

    return ab.res(0, s)
