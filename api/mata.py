import os
import requests
import json
import base64
import datetime
import csv
import re

from main import app
import func.apibase as ab
from func.config import cfg
import api.sbv2 as lr

app_name = os.path.splitext(os.path.basename(__file__))[0]
cfga = cfg[app_name]

@app.post("/" + app_name)
async def api_main(args: dict) -> ab.ApiResponse:
    try:
        chunk = '00';
        if 'chunk' in args:
            chunk = args['chunk']

        chars = read_chars()

        mata = []
        mata_path = f"{cfga['chunk_tsv_dir']}/{chunk}.tsv"
        if not os.path.exists(mata_path):
            return ab.res(2, f"{mata_path} not found.")
        with open(mata_path, 'r', encoding='utf-8') as fp:
            tsv_reader = csv.reader(fp, delimiter='\t')
            for row in tsv_reader:
                while len(row) < 4:
                    row.append(None)
                if row[1] in chars:
                    row.extend(chars[row[1]])
                mata.append(row)

        return ab.res(0, '', {'mata': mata})
    except Exception as e:
        print(e)
        return ab.res(1, str(e))

@app.get("/" + app_name + "/scenario")
async def api_scenario() -> ab.ApiResponse:
    try:
        rei = re.compile(r'^(\d+) +(.*)$')
        rec = re.compile(r'^・')
        ret = re.compile(r'^(.*?)「(.*)$')
        chunk = '00'
        tsvs = []
        with open(cfga['scenario_txt_path'], 'r', encoding='utf-8') as fp:
            for line in fp:
                if not line:
                    continue

                r = re.findall(rei, line)
                if r:
                    if tsvs:
                        save_tsv(chunk, tsvs)
                        tsvs.clear()
                    (chunk, title) = r[0]
                    tsvs.append(['6', 'image', f'{chunk}.webp'])
                    tsvs.append(['6', 'title', f'{title}'])
                    continue

                r = re.findall(rec, line)
                if r:
                    continue

                r = re.findall(ret, line)
                if r:
                    (name, talk) = r[0]
                    tsvs.append(['6', name, talk])
                    cache_save(name, talk)
                    continue

            save_tsv(chunk, tsvs)

        return ab.res(0, '', {})
    except Exception as e:
        print(e)
        return ab.res(1, str(e))

def save_tsv(chunk, tsvs):
    mata_path = f"{cfga['chunk_tsv_dir']}/{chunk}.tsv"
    with open(mata_path, 'w', encoding='utf-8') as fp:
        for tsv in tsvs:
            fp.write("\t".join(tsv))
            fp.write("\n")

def cache_save(name, talk):
    chars = read_chars()
    if not name in chars:
        return False
    lr.fn_main({
        #'model_name': chars[name][0],
        'id': chars[name][0],
        # 'transpose': chars[name][3],
        # 'speed': chars[name][4],
    }, talk)

def read_chars():
    chars = {}
    with open(cfga['char_tsv_path'], 'r', encoding='utf-8') as fp:
        tsv_reader = csv.reader(fp, delimiter='\t')
        for row in tsv_reader:
            if not row:
                continue
            chars[row[0]] = row[1:]

    return chars
