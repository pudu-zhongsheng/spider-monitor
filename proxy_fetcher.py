import requests
import random
import time
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup


def fetch_free_proxies(max_count: int = 20, timeout: int = 12, retries: int = 2) -> List[str]:

    urls = [
        "https://free-proxy-list.net/zh-cn/",
        "https://free-proxy-list.net/",
    ]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://free-proxy-list.net/',
    }

    last_error: Optional[Exception] = None
    for attempt in range(retries + 1):
        for url in urls:
            try:
                resp = requests.get(url, headers=headers, timeout=timeout)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, 'html.parser')

                table = soup.find('table', id='proxylisttable')
                if table is None:
                    table = soup.find('table', class_='table')
                if table is None:
                    continue

                tbody = table.find('tbody')
                if tbody is None:
                    continue

                proxies: List[str] = []
                for tr in tbody.find_all('tr'):
                    tds = [td.get_text(strip=True) for td in tr.find_all('td')]
                    if len(tds) < 7:
                        continue
                    ip = tds[0]
                    port = tds[1]
                    anonymity = (tds[4] or '').lower()
                    https_flag = (tds[6] or '').lower()

                    if anonymity == 'elite proxy' and https_flag == 'yes':
                        proxies.append(f"http://{ip}:{port}")

                    if len(proxies) >= max_count:
                        break

                if not proxies:
                    fallback: List[str] = []
                    for tr in tbody.find_all('tr'):
                        tds = [td.get_text(strip=True) for td in tr.find_all('td')]
                        if len(tds) < 7:
                            continue
                        ip = tds[0]
                        port = tds[1]
                        anonymity = (tds[4] or '').lower()
                        https_flag = (tds[6] or '').lower()
                        if anonymity in ('anonymous', 'elite proxy') and https_flag == 'yes':
                            fallback.append(f"http://{ip}:{port}")
                        if len(fallback) >= max_count:
                            break
                    proxies = fallback

                if proxies:
                    return proxies
            except Exception as e:
                last_error = e
                time.sleep(random.uniform(0.5, 1.2))

    return []


def test_proxy(proxy_url: str, test_url: str = "https://httpbin.org/get", timeout: int = 8) -> bool:
    try:
        proxies = {'http': proxy_url, 'https': proxy_url}
        resp = requests.get(test_url, proxies=proxies, timeout=timeout)
        return resp.status_code == 200 and bool(resp.text.strip())
    except Exception:
        return False


def get_working_proxies(max_fetch: int = 20, max_validate: int = 8, relax_if_empty: bool = True, return_first: bool = True) -> List[str]:

    raw = fetch_free_proxies(max_count=max_fetch)
    if not raw and relax_if_empty:
        raw = fetch_free_proxies(max_count=max_fetch * 2)
    if not raw:
        return []

    working: List[str] = []
    random.shuffle(raw)

    for proxy in raw:
        if test_proxy(proxy):
            if return_first:
                return [proxy]
            working.append(proxy)
        if len(working) >= max_validate:
            break
        time.sleep(random.uniform(0.2, 0.6))

    if not working and relax_if_empty:
        return raw[:max_validate]

    return working


def get_one_working_proxy(max_fetch: int = 30, relax_if_empty: bool = True) -> Optional[str]:
    results = get_working_proxies(
        max_fetch=max_fetch,
        max_validate=1,
        relax_if_empty=relax_if_empty,
        return_first=True,
    )
    return results[0] if results else None


def pick_proxy_or_none(pool: List[str]) -> Optional[str]:
    if not pool:
        return None
    return random.choice(pool)