import requests
import csv
import time
import random
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

def make_request(url):
    user_agent = UserAgent()
    headers = {'User-Agent': user_agent.random}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  
        return response
    except requests.RequestException:
        return None


def parse_news_content(response):
    soup = BeautifulSoup(response.text, 'lxml')
    selectors = {
        'title': 'body > div.cm-blackbar > div.cm-blackbar__body > div.wrap > div:nth-child(3) > div.p-out-left > div.p-article.p-article__ui > div.pt-bar.pt-bar__ui > div.pt-bar-title.pt-bar-title__ui > h1',
        'time': 'body > div.cm-blackbar > div.cm-blackbar__body > div.wrap > div:nth-child(3) > div.p-out-left > div.p-article.p-article__ui > div.pt-bar.pt-bar__ui > div.pt__meta.pt__meta__ui > ul > li.pt__li.pt__li--publish',
        'author': 'body > div.cm-blackbar > div.cm-blackbar__body > div.wrap > div:nth-child(3) > div.p-out-left > div.p-article.p-article__ui > div.rec-content.articleBody__font > div.status-msg-wrap > div > div > a > h1 > span',
        'content': 'body > div.cm-blackbar > div.cm-blackbar__body > div.wrap > div:nth-child(3) > div.p-out-left > div.p-article.p-article__ui > div.rec-content.articleBody__font > p',
        'tags': 'body > div.cm-blackbar > div.cm-blackbar__body > div.wrap > div:nth-child(3) > div.p-out-left > div.p-article.p-article__ui > div.rec-content.articleBody__font li > a'
    }

    data = {}
    for key, selector in selectors.items():
        if key != 'content' and key != 'tags':
            element = soup.select_one(selector)
            if element:
                data[key] = element.text.strip()
            else:
                return None  # 如果关键信息缺失，返回 None

    # 特别处理内容和标签
    content_elements = soup.select(selectors['content'])
    if content_elements:
        data['content'] = ' '.join([p.text.strip() for p in content_elements[:-1]])  # 去除最后一个 <p> 标签
    else:
        return None

    tag_elements = soup.select(selectors['tags'])
    data['tags'] = ', '.join([tag['title'] for tag in tag_elements if 'title' in tag.attrs])  # 获取所有 <a> 标签的 title 属性

    return [data['title'], data['time'], data['author'], data['content'], data['tags']]


def fetch_news(url):
    response = make_request(url)
    if response:
        return parse_news_content(response)
    return None


def read_last_id(log_file):
    try:
        with open(log_file, 'r') as file:
            last_id = file.read().strip()
            return int(last_id) if last_id else 1
    except FileNotFoundError:
        return 1


def write_last_id(log_file, last_id):
    with open(log_file, 'w') as file:
        file.write(str(last_id))


def update_progress_and_estimate_time(start_id, current_id, end_id, total_elapsed_time, total_count):
    average_time_per_article = total_elapsed_time / total_count
    remaining_articles = end_id - current_id
    estimated_time = remaining_articles * average_time_per_article
    estimated_hours, estimated_remainder = divmod(estimated_time, 3600)
    estimated_minutes, estimated_seconds = divmod(estimated_remainder, 60)

    print(f"進度: {current_id} / {end_id}")
    print(f"預計剩餘時間: {int(estimated_hours)}小時 {int(estimated_minutes)}分鐘 {int(estimated_seconds)}秒")


def append_to_csv(news_data_list, csv_file):
    with open(csv_file, mode='a', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(news_data_list)

def main():
    base_url = 'https://www.cmoney.tw/notes/note-detail.aspx?nid='
    log_file = 'cmoney_ids.txt'
    csv_file = 'cmoney_news.csv'
    start_id = read_last_id(log_file)
    end_id = 758990

    news_data_list = []
    total_elapsed_time = 0
    total_count = 0

    start_time = time.time()

    for news_id in range(start_id, end_id + 1):
        url = f'{base_url}{news_id}'
        news_data = fetch_news(url)

        total_count += 1
        if news_data:
            news_data_list.append(news_data)

        if total_count % 5 == 0:
            elapsed_time = time.time() - start_time
            total_elapsed_time += elapsed_time
            write_last_id(log_file, news_id)
            update_progress_and_estimate_time(start_id, news_id, end_id, total_elapsed_time, total_count)
            start_time = time.time()

        if news_data_list and len(news_data_list) >= 5:
            append_to_csv(news_data_list, csv_file)
            news_data_list = []

        time.sleep(random.uniform(0.2, 0.25 ))  # 增加等待時間範圍，減少被封鎖的機會

    if news_data_list:
        append_to_csv(news_data_list, csv_file)

if __name__ == "__main__":
    main()