import os
import requests
import json
import csv
import base64
import re

from requests.auth import HTTPBasicAuth

from main import app
import func.apibase as ab
from func.config import cfg

app_name = os.path.splitext(os.path.basename(__file__))[0]
cfga = cfg[app_name]

def fn_main(args: dict, tts_text):
    if 'model' not in args:
        return ''

    url = f"http://{cfga['server']}/models/info"
    res = requests.get(url, headers={'Content-Type': 'application/json'})
    info = json.loads(res.content)

    model_id = None
    for k, v in info.items():
        if v['id2spk']['0'] == args['model']:
            model_id = k
            break
    if model_id is None:
        raise ValueError('model not found')

    url = f"http://{cfga['server']}/voice"
    args['text'] = tts_text
    args['model_id'] = model_id
    args['model_id'] = model_id
    args['length'] = 1
    if 'style' not in args:
        args['style'] = 'Neutral'
    body = cache_read(args['text'], args['style'], args['model'])
    if not body:
        print(args)
        res = requests.get(url, params=args, headers={'Content-Type': 'application/json'})
        body = res.content

        cache_write(args['text'], args['style'], args['model'], body)

    return base64.b64encode(body)

@app.post("/" + app_name)
async def api_main(args: dict) -> ab.ApiResponse:
    try:
        if 'user_id' in args:
            tts_text = honorific(ttsdic(args['tts_text'], args['user_id'], True))
        else:
            tts_text = ttsdic(args['tts_text'])
        if not tts_text:
            return ab.res(0, '')
        body = fn_main(args, tts_text)
        return ab.res(0, body)
    except Exception as e:
        print(e)
        return ab.res(1, str(e))

def ttsdic(text, user_id = None, is_name = False):
    with open(cfga['ttsdic_tsv_path'], 'r', encoding='utf-8') as fp:
        tsv = csv.reader(fp, delimiter='\t')
        for row in tsv:
            if user_id and len(row) > 2 and row[2] == 'user_id' and row[0] == user_id:
                return honorific(row[1])
            elif len(row) > 2 and row[2] == 'resub':
                text = re.sub(row[0], '', text)
            elif is_name and len(row) > 2 and row[2] == 'name' and row[0] == text:
                text = honorific(row[1])
            elif row[0] in text:
                if len(row) == 1:
                    row[1] = ''
                text = text.replace(row[0], row[1])

        return text

def honorific(name):
    if not name:
        return ''
    elif name.endswith(('さん', 'ちゃん', 'たん', 'くん', '君', 'さま', '様')):
        return name
    else:
        return name + 'さん'

def cache_read(tts_text, style, model):
    path = f"{cfga['cache_dir']}/{model}_{style}_{tts_text}.ogg"
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as fp:
        body = fp.read()
    return body

def cache_write(tts_text, style, model, body):
    path = f"{cfga['cache_dir']}/{model}_{style}_{tts_text}.ogg"
    with open(path, 'wb') as fp:
        fp.write(body)