import requests
from bs4 import BeautifulSoup
import pandas as pd

# スクレイピング対象のURL
url = 'https://frederic-official.com/'

# HTMLコンテンツを取得
response = requests.get(url)
if response.status_code == 200:
    html_content = response.text
else:
    print('Failed to retrieve the webpage.')
    exit()

# HTMLコンテンツをパース
soup = BeautifulSoup(html_content, 'html.parser')

# ニュースタイトルを取得
titles = soup.find_all('h2', class_='news-title')

# データを保存
data = {'Title': [title.text for title in titles]}
df = pd.DataFrame(data)
df.to_csv('news_titles.csv', index=False)

print('Data has been saved to news_titles.csv')
