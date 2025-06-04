from concurrent.futures import ThreadPoolExecutor
import requests
from requests.exceptions import RequestException
import time

def test_proxy(proxy_address):
    try:
        proxy_dict = {
            'http': f'socks5://{proxy_address}',
            'https': f'socks5://{proxy_address}'
        }
        
        response = requests.get(
            'https://httpbin.org/ip',
            proxies=proxy_dict,
            timeout=10
        )
        return proxy_address, True, response.status_code
        
    except RequestException as e:
        return proxy_address, False, str(e)

def check_proxies_multithreaded(proxy_list, max_workers=10):
    working_proxies = []
    failed_proxies = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(test_proxy, proxy): proxy for proxy in proxy_list}
        
        for future in futures:
            proxy, is_working, status = future.result()
            if is_working:
                working_proxies.append(proxy)
            else:
                failed_proxies.append(proxy)
    
    return working_proxies, failed_proxies
