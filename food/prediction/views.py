import requests
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import MeCab
from sentence_transformers import SentenceTransformer, util
import numpy as np

API_KEY = '45e8bb8ecab406a6'
API_ENDPOINT = 'https://webservice.recruit.co.jp/hotpepper/gourmet/v1/'

mecab = MeCab.Tagger("-Owakati")

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

def tokenize(text):
    return mecab.parse(text).strip()

def get_embedding(text):
    tokenized_text = tokenize(text)  
    embedding = model.encode(tokenized_text)
    return embedding

# メインページの処理
def index(request):
    prefectures = {
        '北海道':{
        '北海道': 'Z041',
    },
    '東北': {
        '青森': 'Z051',
        '岩手': 'Z052',
        '宮城': 'Z053',
        '秋田': 'Z054',
        '山形': 'Z055',
        '福島': 'Z056',
    },
    '関東': {
        '東京': 'Z011',
        '神奈川': 'Z012',
        '埼玉': 'Z013',
        '千葉': 'Z014',
        '茨城': 'Z015',
        '栃木': 'Z016',
        '群馬': 'Z017',
    },
    '中部': {
        '岐阜': 'Z031',
        '静岡': 'Z032',
        '愛知': 'Z033',
        '三重': 'Z034',
        '新潟': 'Z061',
        '富山': 'Z062',
        '石川': 'Z063',
        '福井': 'Z064',
        '山梨': 'Z065',
        '長野': 'Z066',
    },
    '関西': {
        '滋賀': 'Z021',
        '京都': 'Z022',
        '大阪': 'Z023',
        '兵庫': 'Z024',
        '奈良': 'Z025',
        '和歌山': 'Z026',
    },
    '中国': {
        '鳥取': 'Z071',
        '島根': 'Z072',
        '岡山': 'Z073',
        '広島': 'Z074',
        '山口': 'Z075',
    },
    '四国': {
        '徳島': 'Z081',
        '香川': 'Z082',
        '愛媛': 'Z083',
        '高知': 'Z084',
    },
    '九州': {
        '福岡': 'Z091',
        '佐賀': 'Z092',
        '長崎': 'Z093',
        '熊本': 'Z094',
        '大分': 'Z095',
        '宮崎': 'Z096',
        '鹿児島': 'Z097',
        '沖縄': 'Z098',
    },
}
    
    budget_mapping = {
            '指定なし':'budget',
            '1001~1500円': 'B011',
            '1501~2000円': 'B001',
            '2001~3000円': 'B002',
            '3001~4000円': 'B003',
            '4001~5000円': 'B008',
            '5001~7000円': 'B004',
            '7001~10000': 'B005',
            '10000円以上': 'B006,B012,B013,',
        }
    return render(request, 'index.html', {'prefectures': prefectures, 'budget_mapping': budget_mapping})


@csrf_exempt
def search(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword')
        large_area = request.POST.get('prefecture')
        budget = request.POST.get('budget')  

        params = {
            'key': API_KEY,
            'keyword': keyword,
            'large_area': large_area,
            'format': 'json',
            'count': 10
        }
        if budget != 'budget':  # 'budget' は「指定なし」のコード
            params['budget'] = budget

        try:
            response = requests.get(API_ENDPOINT, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            return HttpResponse(f"APIリクエスト中にエラーが発生しました: {e}", status=500)

        if 'results' in data and 'shop' in data['results']:
            shops = data['results']['shop']
            shop_embeddings = []

            
            for shop in shops:
                # descriptionをここで設定
                description = shop.get('name', '') + ' ' + shop.get('genre', {}).get('name', '') + ' ' + shop.get('genre', {}).get('catch', '') + ' ' + shop.get('catch', '')
                embedding = get_embedding(description)
                shop_embeddings.append((shop, embedding))

            # キーワードのベクトルを取得
            keyword_embedding = get_embedding(keyword)
            
            
            # コサイン類似度を計算して類似度でソート
            similarities = []
            for shop, embedding in shop_embeddings:
                similarity = util.cos_sim(keyword_embedding, embedding)[0][0].item()
                similarities.append((shop, similarity))

            similarities.sort(key=lambda x: x[1], reverse=True)
            top_shops = [shop for shop, _ in similarities[:50]]
        else:
            top_shops = []

        return render(request, 'results.html', {'shops': top_shops})
    else:
        return HttpResponse("Invalid request method", status=405)
