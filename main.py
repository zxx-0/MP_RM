import json
import re
import requests
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def load_processed_tokens():
    """加载已处理的 token_name 列表"""
    return set(json.load(open('processed_tokens.json', 'r', encoding='utf-8')) 
               if os.path.exists('processed_tokens.json') else [])

def save_processed_tokens(processed_tokens):
    """保存已处理的 token_name 列表"""
    with open('processed_tokens.json', 'w', encoding='utf-8') as f:
        json.dump(list(processed_tokens), f, ensure_ascii=False, indent=4)

def send_telegram_message(token, chat_id, message):
    """发送 Telegram 消息"""
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        })
        response.raise_for_status()
        logging.info("Telegram 消息发送成功")
    except Exception as e:
        logging.error(f"Telegram 消息发送失败: {e}")

def format_project_message(project):
    """格式化项目信息消息"""
    return "\n".join([
        f"🚀 <b>MP新项目发现</b> 🚀",
        f"📛 项目名称: {project.get('token_name', 'N/A')}",
        f"🏷️ 代币符号: {project.get('token_symbol', 'N/A')}",
        f"📈 购买进度: {project.get('progress_buy', 0):.2f}%",
        f"💰 当前价格: {project.get('current_price_sui', 0):.8f} SUI",
        f"🌐 项目网站: {project.get('link_website', 'N/A')}",
        f"🔗 推特: {project.get('link_twitter', 'N/A')}",
        f"📣 电报: {project.get('link_telegram', 'N/A')}"
    ])

def fetch_ranking_data():
    """抓取排名数据"""
    url = "https://movepump.com/ranking"
    headers = {
        #"accept": "text/x-component",
        #"accept-encoding": "gzip, deflate, br, zstd",
        #"accept-language": "en,en-US;q=0.9,en-GB;q=0.8,zh-CN;q=0.7,zh;q=0.6",
        #"content-type": "application/json",
        #"cookie": "_ga=GA1.1.1741352674.1731594585; _ga_GNVVWBL3J9=GS1.1.1733238793.5.0.1733238903.0.0.0",
        #"dnt": "1",
        "next-action": "04ee47b34d62e8aeacb861b976bb67d69dd7ce34",
        #"next-router-state-tree": "%5B%22%22%2C%7B%22children%22%3A%5B%22ranking%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%5D%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D",
        #"origin": "https://movepump.com",
        #"referer": "https://movepump.com/ranking",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
    }
    payload = [{
        "page": 1, "pageSize": 15,
        "sort": "real_sui_reverse:desc",
        "search": "", "is_completed": False,
        "except_completed": True
    }]

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        match = re.search(r'1:(\{.*\})', response.text)
        return json.loads(match.group(1)) if match else None
    except Exception as e:
        logging.error(f"数据抓取错误: {e}")
        return None

def filter_new_projects(data, processed_tokens):
    """筛选新项目"""
    if not data or "data" not in data:
        logging.warning("无有效数据")
        return []

    return [
        project for project in data["data"]
        if project.get("progress_buy", 0) > 50 and 
           project.get("token_name") not in processed_tokens
    ]#购买进度（progress_buy）大于90，并且该项目尚未处理过（token_name 不在已处理列表中）

def main():
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    # 加载已处理的 token_name
    processed_tokens = load_processed_tokens()

    # 抓取数据
    ranking_data = fetch_ranking_data()
    if not ranking_data:
        return

    # 筛选新项目
    new_projects = filter_new_projects(ranking_data, processed_tokens)
    if not new_projects:
        logging.info("没有新的符合条件的项目")
        return

    logging.info(f"发现 {len(new_projects)} 个新项目")
    
    for project in new_projects:
        # 控制台输出项目详情
        logging.info(json.dumps(project, ensure_ascii=False, indent=2))
        
        # 发送 Telegram 消息
        message = format_project_message(project)
        send_telegram_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)

        # 记录已处理的项目
        processed_tokens.add(project['token_name'])

    # 保存已处理项目列表
    save_processed_tokens(processed_tokens)

if __name__ == "__main__":
    main()
