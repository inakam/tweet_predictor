import re
import json
import MeCab
from requests_oauthlib import OAuth1Session
import time
import os

CK = "AAA"
CS = "BBB"
AT = "CCC"
AS = "DDD"

API_URL = "https://api.twitter.com/1.1/statuses/user_timeline.json"

def crawl_2000tweets(screen_name, CLASS_LABEL):
    max_id = -1
    for i in range(10):
        prev_max_id = max_id
        tweets, max_id = get_tweet_by_screen_name(screen_name, max_id)
        if (max_id > -1):
            # 正常に取得できた
            process_tweets(tweets, CLASS_LABEL)
            max_id -= 1
            time.sleep(1) # 仕様上1回/1秒が望ましい(900回/15分なので)
        elif (max_id == -2):
            #鍵垢
            print ("鍵垢のようなので取得できません")
            break
        elif (max_id == -3):
            #404エラー
            print ("404エラーのため飛ばします")
            break
        elif (max_id == -4):
            # ツイート数が2000に達していないもしくはブロック中で何もツイートが返ってこない
            print ("ツイート数2000未満もしくはブロック中です")
            break
        else:
            # エラーが返っている
            print ("1分待機します")
            time.sleep(60)
            print ("1分待機が終わりました")
            # エラーした分は巻き戻す
            i -= 1
            max_id = prev_max_id
    time.sleep(1) #1ユーザーが終わったら少し待つ

def process_tweets(tweets, CLASS_LABEL):
    surfaces = get_surfaces(tweets)     #ツイートを分かち書き
    write_txt(surfaces, CLASS_LABEL)                 #ツイートを書き込み

def get_tweet_by_screen_name(screen_name, max_id=-1):
    params = {
            'screen_name' : screen_name,
            'count' : 200,
            'include_rts' : 'false'
            }
    if (max_id != -1):
        params['max_id'] = max_id
    twitter = OAuth1Session(CK, CS, AT, AS)
    req = twitter.get(API_URL, params = params)
    results = []
    print ("screen_name: {} ".format(screen_name))
    if req.status_code == 200:
        # JSONをパース
        tweets = json.loads(req.text)
        if (not tweets):
            # ブロック中かこれ以上のツイートが存在しない
            return [], -4
        for tweet in tweets:
            results.append(tweet['text'])
            max_id = tweet['id']
        return results, max_id
    if req.status_code == 401:
        # 鍵垢
        print ("Error: {}({})".format(req.status_code, req.reason))
        return [], -2
    if req.status_code == 404:
        print ("Error: {}({})".format(req.status_code, req.reason))
        return [], -3
    else:
        # エラー
        print ("Error: {}({})".format(req.status_code, req.reason))
        return [], -1

def get_surfaces(contents):
    """
    文書を分かち書きし単語単位に分割
    """
    results = []
    for row in contents:
        content = format_text(row)
        tagger = MeCab.Tagger(' -d /usr/local/lib/mecab/dic/mecab-ipadic-neologd')
        tagger.parse('')
        surf = []
        node = tagger.parseToNode(content)
        while node:
            surf.append(node.surface)
            node = node.next
        results.append(surf)
    return results

def write_txt(contents, CLASS_LABEL="1"):
    """
    評価モデル用のテキストファイルを作成する
    """
    try:
        if(len(contents) > 0):
            fileNema = "tweet_data/tweet_data.txt"
            labelText = "__label__" + str(CLASS_LABEL) + ", "

            f = open(fileNema, 'a')
            for row in contents:
                # 空行区切りの文字列に変換
                spaceTokens = " ".join(row)
                result = labelText + spaceTokens + "\n"
                # 書き込み
                f.write(result)
            f.close()

        print(str(len(contents))+"行を書き込み")

    except Exception as e:
        print("テキストへの書き込みに失敗")
        print(e)

def format_text(text):
    '''
    ツイートから不要な情報を削除
    '''
    text=re.sub(r'https?://[\w/:%#\$&\?\(\)~\.=\+\-…]+', "", text)
    text=re.sub(r'@[\w/:%#\$&\?\(\)~\.=\+\-…]+', "", text)
    text=re.sub(r'&[\w/:%#\$&\?\(\)~\.=\+\-…]+', "", text)
    text=re.sub(';', "", text)
    text=re.sub('RT', "", text)
    text=re.sub('\n', " ", text)
    return text

def get_screen_name_list(file_name):
    screen_name_list=[]
    with open(file_name, "r") as f:
        line = f.readline().strip()
        while line:
            if (line.startswith('#')):
                # コメントは読み飛ばす
                line = f.readline().strip()
                continue
            screen_name_list.append(line)
            line = f.readline().strip()
    return screen_name_list
    

if __name__ == '__main__':
    class_num = 2
    class_name = ["Alpha", "Beta"]
    for i in range(1,class_num+1):
        if (not os.path.isfile("screen_name_list/screen_name_list_{}.txt".format(i))):
            continue
        screen_name_list = get_screen_name_list("screen_name_list/screen_name_list_{}.txt".format(i))
        for screen_name in screen_name_list:
            crawl_2000tweets(screen_name, class_name[i])