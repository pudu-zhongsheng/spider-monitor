import requests
import json
import time
import random
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from urllib.parse import urlparse

try:
    from proxy_fetcher import get_one_working_proxy
except Exception:
    get_one_working_proxy = None  # type: ignore

api_url = "https://alpha123.uk/api/data?fresh=1"

def is_github_actions():
    return os.getenv('GITHUB_ACTIONS') == 'true'

print("定期监控空投数据变化...")
print(f"API地址: {api_url}")

if is_github_actions():
    print("🤖 检测到GitHub Actions环境")
else:
    print("💻 检测到本地环境")

# User-Agent列表
user_agents = [
    "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:30.0) Gecko/20100101 Firefox/30.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/537.75.14",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Win64; x64; Trident/6.0)",
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
    'Opera/9.25 (Windows NT 5.1; U; en)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
    'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
    "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

CHECK_INTERVAL = random.randint(25,45)
DATA_FILE = "latest_airdrop_data.json"
def get_public_ip(proxies: Optional[dict] = None) -> Optional[str]:
    """获取当前出口公网IP（支持代理）。"""
    try:
        resp = requests.get("https://httpbin.org/ip", timeout=8, proxies=proxies)
        if resp.status_code == 200:
            data = resp.json()
            origin = data.get("origin")
            if isinstance(origin, str):
                return origin.split(",")[0].strip()
        return None
    except Exception:
        return None


def format_proxy_host_port(proxy_url: str) -> str:
    try:
        parsed = urlparse(proxy_url)
        host = parsed.hostname or ""
        port = str(parsed.port) if parsed.port else ""
        if host and port:
            return f"{host}:{port}"
        return host or proxy_url
    except Exception:
        return proxy_url

EMAIL_CONFIG = {
    'smtp_server': os.getenv('SMTP_SERVER', 'smtp.163.com'),
    'smtp_port': int(os.getenv('SMTP_PORT', '25')),
    'sender_email': os.getenv('SENDER_EMAIL'),
    'sender_password': os.getenv('SENDER_PASSWORD'),
    'recipient_emails': os.getenv('RECIPIENT_EMAILS', '').split(',')
}

CHAIN_ID_MAPPING = {
    "1": "Ethereum Mainnet",
    "5": "Goerli Testnet",
    "11155111": "Sepolia Testnet",
    "56": "BNB Smart Chain",
    "8453": "Base Mainnet",
    "137": "Polygon",
    "42161": "Arbitrum One",
    "10": "Optimism",
    "43114": "Avalanche C-Chain",
    "250": "Fantom Opera",
    "100": "Gnosis Chain",
    "1284": "Moonbeam",
    "592": "Astar Network",
    "122": "Fuse Network",
    "1285": "Moonriver",
    "97": "BSC Testnet",
    "80001": "Mumbai Testnet",
    "43113": "Avalanche Fuji Testnet"
}

def get_airdrop_data(max_retries=3):
    for attempt in range(max_retries):
        try:
            selected_ua = random.choice(user_agents)
            
            headers = {
                'User-Agent': selected_ua,
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://alpha123.uk/zh/',
                'Cache-Control': 'no-cache'
            }
            
            time.sleep(random.uniform(1, 3))
            
            print(f"🔄 尝试获取数据 (第 {attempt + 1} 次)...")
            
            proxies = None
            proxy_used: Optional[str] = None

            if is_github_actions():
                proxy_url = os.getenv('PROXY_URL')
                if proxy_url:
                    proxies = {'http': proxy_url, 'https': proxy_url}
                    proxy_used = proxy_url
                else:
                    use_pool = os.getenv('USE_PROXY_POOL') == '1'
                    if use_pool and get_one_working_proxy:
                        try:
                            proxy_used = get_one_working_proxy(max_fetch=40)
                        except Exception:
                            proxy_used = None
                        if proxy_used:
                            proxies = {'http': proxy_used, 'https': proxy_used}
                if not proxies:
                    print("🚫 GitHub Actions环境下未找到可用代理，等待重试...")
                    time.sleep(random.uniform(5, 10))
                    continue
            else:
                proxy_url = os.getenv('PROXY_URL')
                if proxy_url:
                    proxies = {'http': proxy_url, 'https': proxy_url}
                    proxy_used = proxy_url
                else:
                    use_pool = os.getenv('USE_PROXY_POOL') == '1'
                    if use_pool and get_one_working_proxy:
                        try:
                            proxy_used = get_one_working_proxy(max_fetch=30)
                        except Exception:
                            proxy_used = None
                        if proxy_used:
                            proxies = {'http': proxy_used, 'https': proxy_used}

            if proxy_used:
                print(f"🌐 使用代理: {format_proxy_host_port(proxy_used)}")

            try:
                current_ip = get_public_ip(proxies)
                if current_ip:
                    if proxy_used:
                        print(f"🌍 当前出口IP(经代理): {current_ip}")
                    else:
                        print(f"🌍 当前出口IP(直连): {current_ip}")
                else:
                    print("🌍 无法获取当前出口IP")
            except Exception:
                print("🌍 获取当前出口IP时发生异常")
            
            response = requests.get(api_url, headers=headers, timeout=30, proxies=proxies)
            
            if response.status_code == 200:
                if not response.text.strip():
                    print(f"⚠️ 响应内容为空 (第 {attempt + 1} 次)")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(2, 5))
                        continue
                    return None
                
                try:
                    data = json.loads(response.text)
                    print(f"✅ 数据获取成功 (第 {attempt + 1} 次)")
                    return data
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON解析失败: {e} (第 {attempt + 1} 次)")
                    print(f"响应内容: {response.text[:200]}...")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(2, 5))
                        continue
                    return None
            else:
                print(f"⚠️ API请求失败，状态码: {response.status_code} (第 {attempt + 1} 次)")
                
                if response.status_code == 403:
                    print("🚫 检测到403错误，可能是IP被封禁，尝试更换代理...")
                    if is_github_actions():
                        if get_one_working_proxy:
                            try:
                                new_proxy = get_one_working_proxy(max_fetch=30)
                                if new_proxy:
                                    print(f"🔄 获取到新代理: {format_proxy_host_port(new_proxy)}")
                                    continue
                                else:
                                    print("❌ 无法获取新代理，等待后重试...")
                                    time.sleep(random.uniform(10, 20))
                                    continue
                            except Exception as e:
                                print(f"❌ 获取新代理失败: {e}")
                                time.sleep(random.uniform(10, 20))
                                continue
                        else:
                            print("❌ 代理模块不可用，等待后重试...")
                            time.sleep(random.uniform(10, 20))
                            continue
                    else:
                        if get_one_working_proxy:
                            try:
                                new_proxy = get_one_working_proxy(max_fetch=40)
                                if new_proxy:
                                    print(f"🔄 获取到新代理: {format_proxy_host_port(new_proxy)}")
                                    continue
                                else:
                                    print("❌ 无法获取新代理，等待后重试...")
                                    time.sleep(random.uniform(5, 10))
                                    continue
                            except Exception as e:
                                print(f"❌ 获取新代理失败: {e}")
                                time.sleep(random.uniform(5, 10))
                                continue
                        else:
                            print("❌ 代理模块不可用，等待后重试...")
                            time.sleep(random.uniform(5, 10))
                            continue
                else:
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(2, 5))
                        continue
                    return None
                
        except requests.exceptions.Timeout:
            print(f"⚠️ 请求超时 (第 {attempt + 1} 次)")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 5))
                continue
            return None
            
        except requests.exceptions.ConnectionError:
            print(f"⚠️ 连接错误 (第 {attempt + 1} 次)")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 5))
                continue
            return None
            
        except Exception as e:
            print(f"⚠️ 获取数据失败: {e} (第 {attempt + 1} 次)")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 5))
                continue
            return None
    
    print(f"❌ 所有重试都失败了，共尝试 {max_retries} 次")
    return None

def format_phase(phase):
    if phase is None:
        return "未知"
    return f"阶段{phase}"

def format_type(type_value):
    if type_value == "grab":
        return "先到先得"
    elif type_value is None or type_value == "":
        return "未知"
    else:
        return str(type_value)

def format_chain_id(chain_id):
    if chain_id is None or chain_id == "":
        return "未知网络"
    
    chain_id_str = str(chain_id)
    
    network_name = CHAIN_ID_MAPPING.get(chain_id_str)
    
    if network_name:
        return f"{network_name} (ID: {chain_id})"
    else:
        return f"未知网络 (ID: {chain_id})"

def format_field_name(field):
    field_mapping = {
        'status': '状态',
        'points': '积分',
        'amount': '数量',
        'date': '日期',
        'time': '时间',
        'type': '类型'
    }
    return field_mapping.get(field, field)

def format_airdrop_info(airdrop):
    name = airdrop.get('name', '未知')
    token = airdrop.get('token', 'N/A')
    points = airdrop.get('points', 'N/A')
    amount = airdrop.get('amount', 'N/A')
    date = airdrop.get('date', 'N/A')
    time = airdrop.get('time', 'N/A')
    phase = format_phase(airdrop.get('phase'))
    type_value = format_type(airdrop.get('type'))
    chain_id = format_chain_id(airdrop.get('chain_id'))
    
    return {
        'name_token': f"{token} ({name})",
        'points': points,
        'amount': amount,
        'date_time': f"{date} {time}",
        'phase': phase,
        'type': type_value,
        'chain_id': chain_id,
        'status': airdrop.get('status', 'unknown'),
        'completed': airdrop.get('completed', False)
    }

def load_latest_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载历史数据失败: {e}")
            return None
    return None

def save_latest_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存数据失败: {e}")
        return False

def send_email_notification(changes, processed_data):
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        subject = f"🚀 空投通知 - {current_time}"
        
        body = f"""
检测到空投更新！

当前状态:
- 空投数量: {processed_data['upcoming']} 个

数据变化:
"""
        if isinstance(changes, list) and changes:
            for idx, change in enumerate(changes, start=1):
                body += f"- {change}\n"
        elif isinstance(changes, str) and changes:
            body += f"- {changes}\n"
        else:
            body += "- 无具体变化明细\n"

        body += "\n详细项目信息:\n"
        
        airdrops = processed_data['data']
        active_count = 0
        for airdrop in airdrops:
            if not airdrop.get('completed', False):
                active_count += 1
                info = format_airdrop_info(airdrop)
                body += f"""
项目 {active_count}: {info['name_token']}
  积分: {info['points']}
  数量: {info['amount']}
  时间: {info['date_time']}
  阶段: {info['phase']}
  类型: {info['type']}
  区块链网络: {info['chain_id']}
"""
        
        body += """
---
此邮件由空投监控系统自动发送
"""
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = ', '.join(EMAIL_CONFIG['recipient_emails'])
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        
        text = msg.as_string()
        server.sendmail(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['recipient_emails'], text)
        server.quit()
        
        print("📧 邮件通知发送成功!")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

def compare_data(old_data, new_data):
    """对比新旧数据，检测变化（只关注未完成的空投）"""
    if not old_data or not new_data:
        return True, "首次检查或数据获取失败"
    
    old_airdrops = old_data.get('airdrops', [])
    new_airdrops = new_data.get('airdrops', [])
    
    old_active_airdrops = [item for item in old_airdrops if not item.get('completed', False)]
    new_active_airdrops = [item for item in new_airdrops if not item.get('completed', False)]
    
    changes = []
    
    if len(old_active_airdrops) != len(new_active_airdrops):
        changes.append(f"活跃项目数量变化: {len(old_active_airdrops)} -> {len(new_active_airdrops)}")
    
    old_map = {item.get('token'): item for item in old_active_airdrops}
    new_map = {item.get('token'): item for item in new_active_airdrops}
    
    for token, new_item in new_map.items():
        if token not in old_map:
            info = format_airdrop_info(new_item)
            changes.append(f"新增活跃项目: {info['name_token']} ({info['date_time']})")
    
    for token, old_item in old_map.items():
        if token not in new_map:
            new_item = next((item for item in new_airdrops if item.get('token') == token), None)
            if new_item and new_item.get('completed', False):
                info = format_airdrop_info(new_item)
                changes.append(f"项目已完成: {info['name_token']}")
            else:
                info = format_airdrop_info(old_item)
                changes.append(f"活跃项目移除: {info['name_token']}")
    
    for token, new_item in new_map.items():
        if token in old_map:
            old_item = old_map[token]
            
            old_completed = old_item.get('completed', False)
            new_completed = new_item.get('completed', False)
            if old_completed != new_completed and new_completed:
                info = format_airdrop_info(new_item)
                changes.append(f"项目已完成: {info['name_token']}")
            
            if not new_completed:
                important_fields = ['status', 'points', 'amount', 'date', 'time', 'type']
                for field in important_fields:
                    old_value = old_item.get(field)
                    new_value = new_item.get(field)
                    if field == 'amount':
                        item_type = str(new_item.get('type') or '').lower()
                        if item_type == 'tge':
                            continue
                    if old_value != new_value:
                        info = format_airdrop_info(new_item)
                        if field == 'type':
                            old_type_formatted = format_type(old_value)
                            new_type_formatted = format_type(new_value)
                            changes.append(f"项目类型变化: {info['name_token']} {format_field_name(field)}: {old_type_formatted} -> {new_type_formatted}")
                        else:
                            changes.append(f"项目信息变化: {info['name_token']} {format_field_name(field)}: {old_value} -> {new_value}")
    
    if changes:
        return True, changes
    else:
        return False, None

def process_airdrop_data(data):
    if not data or 'airdrops' not in data:
        print("❌ 没有找到空投数据")
        return None
    
    airdrops = data['airdrops']
    print(f"✅ 获取到 {len(airdrops)} 个空投项目")
    
    announced = []
    completed = []
    upcoming = []
    
    for airdrop in airdrops:
        if airdrop.get('status') == 'announced':
            if airdrop.get('completed'):
                completed.append(airdrop)
            else:
                upcoming.append(airdrop)
        else:
            announced.append(airdrop)
    
    print(f"📊 数据统计: 已完成 {len(completed)} 个, 即将开始 {len(upcoming)} 个, 其他 {len(announced)} 个")
    
    return {
        'total': len(airdrops),
        'completed': len(completed),
        'upcoming': len(upcoming),
        'announced': len(announced),
        'data': airdrops
    }

def check_changes_once():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"⏰ {current_time} 开始检查...")
    
    try:
        new_data = get_airdrop_data()
        if not new_data:
            print("❌ 获取数据失败，跳过本次检查")
            return False
        
        old_data = load_latest_data()
        
        has_changes, change_info = compare_data(old_data, new_data)
        
        if has_changes:
            print("🔔 检测到数据变化!")
            
            if isinstance(change_info, list):
                for change in change_info:
                    print(f"  📝 {change}")
            else:
                print(f"  📝 {change_info}")
            
            processed_data = process_airdrop_data(new_data)
            if processed_data:
                print(f"  📊 当前状态: 总计 {processed_data['total']} 个项目")
            
            print("  📧 正在发送邮件通知...")
            try:
                if send_email_notification(change_info, processed_data):
                    print("  ✅ 邮件通知发送成功")
                else:
                    print("  ❌ 邮件通知发送失败")
            except Exception as e:
                print(f"  ❌ 邮件发送异常: {e}")
            
            try:
                if save_latest_data(new_data):
                    print("  💾 新数据已保存")
                else:
                    print("  ⚠️ 数据保存失败")
            except Exception as e:
                print(f"  ❌ 数据保存异常: {e}")
            
            return True
            
        else:
            print("✅ 数据无变化")
            try:
                save_latest_data(new_data)
            except Exception as e:
                print(f"⚠️ 保存数据时出错: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 检查过程中发生严重错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_email():
    print("🧪 测试邮件发送功能")
    print("=" * 50)
    
    current_data = get_airdrop_data()
    if not current_data:
        print("❌ 获取数据失败")
        return
    
    processed_data = process_airdrop_data(current_data)
    if not processed_data:
        return
    
    test_changes = ["测试邮件: 系统运行正常", f"即将开始的空投: {processed_data['upcoming']}个"]
    
    print("📧 发送测试邮件...")
    if send_email_notification(test_changes, processed_data):
        print("✅ 测试邮件发送成功!")
        print("请您检查是否收到了来自zhongsheng24wx@163.com的邮件")
    else:
        print("❌ 测试邮件发送失败")

def health_check():
    print("🏥 执行健康检查...")
    
    print("🔍 检查API连接...")
    test_data = get_airdrop_data(max_retries=1)
    if test_data:
        print("✅ API连接正常")
        processed_data = process_airdrop_data(test_data)
        if processed_data:
            print(f"📊 当前数据: 总计 {processed_data['total']} 个项目")
    else:
        print("❌ API连接异常")
    
    print("🔍 检查数据文件...")
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 数据文件正常，包含 {len(data.get('airdrops', []))} 个项目")
        except Exception as e:
            print(f"❌ 数据文件异常: {e}")
    else:
        print("⚠️ 数据文件不存在")
    
    print("🔍 检查邮件配置...")
    try:
        print("✅ 邮件配置正常")
    except Exception as e:
        print(f"❌ 邮件配置异常: {e}")

def main():
    """主函数（GitHub Actions模式）"""
    print("🚀 空投数据变化监控系统 - GitHub Actions模式")
    print("=" * 50)
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            print("🧪 执行测试模式...")
            test_email()
            return
        elif sys.argv[1] == "init":
            print("📡 执行初始化模式...")
            initial_data = get_airdrop_data()
            if not initial_data:
                print("❌ 首次获取数据失败")
                return
            
            processed_data = process_airdrop_data(initial_data)
            if processed_data:
                save_latest_data(initial_data)
                print("💾 初始数据已保存")
            return
        elif sys.argv[1] == "health":
            print("🏥 执行健康检查模式...")
            health_check()
            return
    
    print("🔄 执行单次检查...")
    success = check_changes_once()
    
    if success:
        print("✅ 检查完成，发现变化并已发送通知")
    else:
        print("✅ 检查完成，无变化")

if __name__ == "__main__":
    main()
