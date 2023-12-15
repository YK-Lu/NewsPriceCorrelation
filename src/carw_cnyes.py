import requests
import csv
import time
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
        'title': '#content > div > div > div._2hZZ.theme-app.theme-newsdetail > main > div._uo1n._2l9x > h1',
        'time': '#content > div > div > div._2hZZ.theme-app.theme-newsdetail > main > div._uo1n._2l9x > div._1R6L > time',
        'author': '#content > div > div > div._2hZZ.theme-app.theme-newsdetail > main > div._uo1n._2l9x > div._1R6L > span > span',
        'content': '#content > div > div > div._2hZZ.theme-app.theme-newsdetail > main > div._1S0A > article > section._82F6 > div._1UuP > div:nth-child(1)',
        'tags': '#content > div > div > div._2hZZ.theme-app.theme-newsdetail > main > div._1S0A > article > section._82F6 > nav > a'
    }

    data = {}
    for key, selector in selectors.items():
        element = soup.select_one(selector)
        if element:
            data[key] = element.text.strip()
        elif key != 'tags':  # 对于非标签元素，若不存在则返回 None
            return None

    # 即使没有标签，也处理并返回数据
    if 'tags' in data:
        data['tags'] = ', '.join([tag.text.strip() for tag in soup.select(selectors['tags'])])
    else:
        data['tags'] = 'None'

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
    base_url = 'https://news.cnyes.com/news/id/'
    log_file = 'crawled_ids.txt'
    csv_file = 'cnyes_news.csv'
    start_id = read_last_id(log_file)
    end_id = 2000000

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

        if total_count % 50 == 0:
            elapsed_time = time.time() - start_time
            total_elapsed_time += elapsed_time
            write_last_id(log_file, news_id)
            update_progress_and_estimate_time(start_id, news_id, end_id, total_elapsed_time, total_count)
            start_time = time.time()

        if news_data_list and len(news_data_list) >= 50:
            append_to_csv(news_data_list, csv_file)
            news_data_list = []

        #time.sleep(random.uniform(0.5, 2))  # 增加等待時間範圍，減少被封鎖的機會

    if news_data_list:
        append_to_csv(news_data_list, csv_file)

if __name__ == "__main__":
    main()