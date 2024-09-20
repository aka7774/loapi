import os
import requests
import json
import csv
import base64
import re

from urllib.parse import quote
from requests.auth import HTTPBasicAuth

from main import app
import func.apibase as ab
from func.config import cfg

app_name = os.path.splitext(os.path.basename(__file__))[0]
cfga = cfg[app_name]

def fn_main(args: dict, tts_text):
    if 'style' not in args:
        args['style'] = 'Neutral'
    if 'length' not in args:
        args['length'] = 1

    if 'model' in args or 'speaker' in args:
        url = f"http://{cfga['server']}/models/info"
        res = requests.get(url, headers={'Content-Type': 'application/json'})
        info = json.loads(res.content)

        model_id = None
        for k, v in info.items():
            if v['id2spk']['0'] == args['speaker'] and f"/{args['model']}/" in v['config_path']:
                model_id = k
                break
        if model_id is None:
            raise ValueError('model not found')

        args['model_id'] = model_id

    url = f"http://{cfga['server']}/voice"
    params = {
        'text': tts_text,
        'model_name': args['model_name'],
        'style': args['style'],
        'length': args['length'],
    }
    body = cache_read(tts_text, args['style'], args['length'], args['model_name'])
    if not body:
        print(args)
        print(params)
        res = requests.get(url, params=params, headers={'Content-Type': 'application/json'})
        body = res.content

        cache_write(tts_text, args['style'], args['length'], args['model_name'], body)

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

        return ttsdic2(text)

def honorific(name):
    if not name:
        return ''
    elif name.endswith(('さん', 'ちゃん', 'たん', 'くん', '君', 'さま', '様')):
        return name
    else:
        return name + 'さん'

def cache_read(tts_text, style, length, model_name):
    path = f"{cfga['cache_dir']}/{model_name}_{style}_{length}_{tts_text}.ogg"
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as fp:
        body = fp.read()
    return body

def cache_write(tts_text, style, length, model_name, body):
    path = f"{cfga['cache_dir']}/{model_name}_{style}_{length}_{tts_text}.ogg"
    with open(path, 'wb') as fp:
        fp.write(body)




# TSVファイルから辞書を読み込む関数
def load_dictionary(file_path):
    typed_english_to_japanese = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            if len(row) == 2:
                typed_english_to_japanese[row[0].lower()] = row[1]
    return typed_english_to_japanese

# 辞書を読み込む
typed_english_to_japanese = load_dictionary(cfga['etoj_tsv_path'])

def convert_english_to_japanese_reading(text):
    sorted_keys = sorted(typed_english_to_japanese.keys(), key=len, reverse=True)

    for english_word in sorted_keys:
        japanese_reading = typed_english_to_japanese[english_word]
        regex = r'\b' + re.escape(english_word) + r'\b'
        text = re.sub(regex, japanese_reading, text, flags=re.IGNORECASE)

    return text

# 複合単語対応
def convert_sentence(sentence):
    # 英単語を検出する正規表現
    english_word_regex = r'[a-zA-Z &!]+'

    # 文章内の英単語を置換
    return re.sub(english_word_regex, lambda match: convert_to_katakana(match.group()), sentence)

def convert_to_katakana(word):
    result = ""
    remaining_word = word.lower()

    while remaining_word:
        longest_match = ""
        longest_match_katakana = ""

        for key in typed_english_to_japanese:
            if remaining_word.startswith(key) and len(key) > len(longest_match):
                longest_match = key
                longest_match_katakana = typed_english_to_japanese[key]

        if longest_match:
            result += longest_match_katakana
            remaining_word = remaining_word[len(longest_match):]
        else:
            # マッチが見つからない場合、元の単語を返す
            return word

    return result


tree = {
  'a': 'ア', 'i': 'イ', 'u': 'ウ', 'e': 'エ', 'o': 'オ',
  'k': {
    'a': 'カ', 'i': 'キ', 'u': 'ク', 'e': 'ケ', 'o': 'コ',
    'y': { 'a': 'キャ', 'i': 'キィ', 'u': 'キュ', 'e': 'キェ', 'o': 'キョ' },
  },
  's': {
    'a': 'サ', 'i': 'シ', 'u': 'ス', 'e': 'セ', 'o': 'ソ',
    'h': { 'a': 'シャ', 'i': 'シ', 'u': 'シュ', 'e': 'シェ', 'o': 'ショ' },
    'y': { 'a': 'シャ', 'i': 'シィ', 'u': 'シュ', 'e': 'シェ', 'o': 'ショ' },
  },
  't': {
    'a': 'タ', 'i': 'チ', 'u': 'ツ', 'e': 'テ', 'o': 'ト',
    'h': { 'a': 'テャ', 'i': 'ティ', 'u': 'テュ', 'e': 'テェ', 'o': 'テョ' },
    'y': { 'a': 'チャ', 'i': 'チィ', 'u': 'チュ', 'e': 'チェ', 'o': 'チョ' },
    's': { 'a': 'ツァ', 'i': 'ツィ', 'u': 'ツ', 'e': 'ツェ', 'o': 'ツォ' },
  },
  'c': {
    'a': 'カ', 'i': 'シ', 'u': 'ク', 'e': 'セ', 'o': 'コ',
    'h': { 'a': 'チャ', 'i': 'チ', 'u': 'チュ', 'e': 'チェ', 'o': 'チョ' },
    'y': { 'a': 'チャ', 'i': 'チィ', 'u': 'チュ', 'e': 'チェ', 'o': 'チョ' },
  },
  'q': {
    'a': 'クァ', 'i': 'クィ', 'u': 'ク', 'e': 'クェ', 'o': 'クォ',
  },
  'n': {
    'a': 'ナ', 'i': 'ニ', 'u': 'ヌ', 'e': 'ネ', 'o': 'ノ', 'n': 'ン',
    'y': { 'a': 'ニャ', 'i': 'ニィ', 'u': 'ニュ', 'e': 'ニェ', 'o': 'ニョ' },
  },
  'h': {
    'a': 'ハ', 'i': 'ヒ', 'u': 'フ', 'e': 'ヘ', 'o': 'ホ',
    'y': { 'a': 'ヒャ', 'i': 'ヒィ', 'u': 'ヒュ', 'e': 'ヒェ', 'o': 'ヒョ' },
  },
  'f': {
    'a': 'ファ', 'i': 'フィ', 'u': 'フ', 'e': 'フェ', 'o': 'フォ',
    'y': { 'a': 'フャ', 'u': 'フュ', 'o': 'フョ' },
  },
  'm': {
    'a': 'マ', 'i': 'ミ', 'u': 'ム', 'e': 'メ', 'o': 'モ',
    'y': { 'a': 'ミャ', 'i': 'ミィ', 'u': 'ミュ', 'e': 'ミェ', 'o': 'ミョ' },
  },
  'y': { 'a': 'ヤ', 'i': 'イ', 'u': 'ユ', 'e': 'イェ', 'o': 'ヨ' },
  'r': {
    'a': 'ラ', 'i': 'リ', 'u': 'ル', 'e': 'レ', 'o': 'ロ',
    'y': { 'a': 'リャ', 'i': 'リィ', 'u': 'リュ', 'e': 'リェ', 'o': 'リョ' },
  },
  'w': { 'a': 'ワ', 'i': 'ウィ', 'u': 'ウ', 'e': 'ウェ', 'o': 'ヲ' },
  'g': {
    'a': 'ガ', 'i': 'ギ', 'u': 'グ', 'e': 'ゲ', 'o': 'ゴ',
    'y': { 'a': 'ギャ', 'i': 'ギィ', 'u': 'ギュ', 'e': 'ギェ', 'o': 'ギョ' },
  },
  'z': {
    'a': 'ザ', 'i': 'ジ', 'u': 'ズ', 'e': 'ゼ', 'o': 'ゾ',
    'y': { 'a': 'ジャ', 'i': 'ジィ', 'u': 'ジュ', 'e': 'ジェ', 'o': 'ジョ' },
  },
  'j': {
    'a': 'ジャ', 'i': 'ジ', 'u': 'ジュ', 'e': 'ジェ', 'o': 'ジョ',
    'y': { 'a': 'ジャ', 'i': 'ジィ', 'u': 'ジュ', 'e': 'ジェ', 'o': 'ジョ' },
  },
  'd': {
    'a': 'ダ', 'i': 'ヂ', 'u': 'ヅ', 'e': 'デ', 'o': 'ド',
    'h': { 'a': 'デャ', 'i': 'ディ', 'u': 'デュ', 'e': 'デェ', 'o': 'デョ' },
    'y': { 'a': 'ヂャ', 'i': 'ヂィ', 'u': 'ヂュ', 'e': 'ヂェ', 'o': 'ヂョ' },
  },
  'b': {
    'a': 'バ', 'i': 'ビ', 'u': 'ブ', 'e': 'ベ', 'o': 'ボ',
    'y': { 'a': 'ビャ', 'i': 'ビィ', 'u': 'ビュ', 'e': 'ビェ', 'o': 'ビョ' },
  },
  'v': {
    'a': 'ヴァ', 'i': 'ヴィ', 'u': 'ヴ', 'e': 'ヴェ', 'o': 'ヴォ',
    'y': { 'a': 'ヴャ', 'i': 'ヴィ', 'u': 'ヴュ', 'e': 'ヴェ', 'o': 'ヴョ' },
  },
  'p': {
    'a': 'パ', 'i': 'ピ', 'u': 'プ', 'e': 'ペ', 'o': 'ポ',
    'y': { 'a': 'ピャ', 'i': 'ピィ', 'u': 'ピュ', 'e': 'ピェ', 'o': 'ピョ' },
  },
  'x': {
    'a': 'ァ', 'i': 'ィ', 'u': 'ゥ', 'e': 'ェ', 'o': 'ォ',
    'y': {
      'a': 'ャ', 'i': 'ィ', 'u': 'ュ', 'e': 'ェ', 'o': 'ョ',
    },
    't': {
      'u': 'ッ',
      's': {
        'u': 'ッ',
      },
    },
  },
  'l': {
    'a': 'ァ', 'i': 'ィ', 'u': 'ゥ', 'e': 'ェ', 'o': 'ォ',
    'y': {
      'a': 'ャ', 'i': 'ィ', 'u': 'ュ', 'e': 'ェ', 'o': 'ョ',
    },
    't': {
      'u': 'ッ',
      's': {
        'u': 'ッ',
      },
    },
  },
}

def convert_roman_to_kana(original):
    def to_half_width(s):
        return ''.join(chr(ord(c) - 65248) if 'Ａ' <= c <= 'ｚ' else c for c in s)
    
    str_input = to_half_width(original).lower()
    result = ''
    tmp = ''
    index = 0
    node = tree

    def push(char, to_root=True):
        nonlocal result, tmp, node
        result += char
        tmp = ''
        node = tree if to_root else node

    while index < len(str_input):
        char = str_input[index]
        if re.match(r'[a-z]', char):
            if char in node:
                next_node = node[char]
                if isinstance(next_node, str):
                    push(next_node)
                else:
                    tmp += original[index]
                    node = next_node
                index += 1
                continue
            prev = str_input[index - 1] if index > 0 else ''
            if prev and (prev == 'n' or prev == char):
                push('ン' if prev == 'n' else 'ッ', False)
            if node != tree and char in tree:
                push(tmp)
                continue
        push(tmp + char)
        index += 1

    tmp = re.sub(r'n$', 'ン', tmp)
    push(tmp)
    return result

ranges = [
    r'[\ud800-\ud8ff][\ud000-\udfff]',  # 基本的な絵文字除去
    r'[\ud000-\udfff]{2,}',  # サロゲートペアの二回以上の繰り返しがあった場合
    r'\ud7c9[\udc00-\udfff]',  # 特定のシリーズ除去
    r'[0-9|*|#][\uFE0E-\uFE0F]\u20E3',  # 数字系絵文字
    r'[0-9|*|#]\u20E3',  # 数字系絵文字
    r'[©|®|\u2010-\u3fff][\uFE0E-\uFE0F]',  # 環境依存文字や日本語との組み合わせによる絵文字
    r'[\u2010-\u2FFF]',  # 指や手、物など、単体で絵文字となるもの
    r'\uA4B3',  # 数学記号の環境依存文字の除去
]

surrogate_pair_code = [
    65038,
    65039,
    8205,
    11093,
    11035
]

def remove_emoji(in_value):
    reg = re.compile('|'.join(ranges), flags=re.UNICODE)
    ret_value = re.sub(reg, '', in_value)

    # パターンにマッチする限り、除去を繰り返す（一回の正規表現除去では除去しきないパターンがあるため）
    while reg.search(ret_value):
        ret_value = re.sub(reg, '', ret_value)

    # 二重で絵文字チェック（4バイト、サロゲートペアの残りカス除外）
    result = ''
    for c in ret_value:
        code = ord(c)
        if (len(re.sub(r'%..', 'x', quote(c))) < 4 and
            not any(code == code_num for code_num in surrogate_pair_code)):
            result += c

    return result

def ttsdic2(s):
    # コメント内のURL、タグを除去
    re_url = r'http(s)?://([\w\-]+\.)+[\w\-]+(/[\w\- ./?%&=~]*)?'
    s = re.sub(re_url, '', s)
    re_tag = r'<[^>]+>'
    s = re.sub(re_tag, '', s)

    # 絵文字を除去
    s = remove_emoji(s)
    
    # カッコの中は読まない
    s = re.sub(r'[(（].*?[)）]', '', s)

    tts_ignore = ['*', "'", '"', 'ω', ':']
    for n in tts_ignore:
        s = s.replace(n, '')

    # 辞書にある英語はカタカナ訛りで発音しようとする
    s = convert_english_to_japanese_reading(s)
    # 複合単語もできるだけ処理する
    s = convert_sentence(s)
    # それ以外のアルファベットはローマ字読みしようとする
    s = convert_roman_to_kana(s)

    return s
