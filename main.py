import time
import requests
import argparse
import random
import urllib3
from UserAgenter import UserAgent
from requests.exceptions import RequestException
from utils.proxy import check_proxies_multithreaded
from utils.tor import change_tor_ip, set_tor_proxy, launch_tor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_random_user_agent() -> str:
    ua = UserAgent()
    ua_random_functions = [
        ua.RandomEdgeAgent,
        ua.RandomSafariAgent,
        ua.RandomAndroidAgent,
        ua.RandomFirefoxAgent,
        ua.RandomOperaAgent,
    ]

    random_ua_func = random.choice(ua_random_functions)
    return random_ua_func()


def create_proxy_dict(proxy_address):
    proxy_url = f"socks5://{proxy_address}"
    
    return {
        'http': proxy_url,
        'https': proxy_url
    }   

def run_fuzz(url, wordlist, legitimate, proxy_list, delay_range, output, tor_proxy=False, change_interval=(5, 25)):
    directories = []
    legitimate_counter = 0
    output_file = open(output, 'w')
    
    if len(legitimate) > 0:
        for i in range(len(wordlist) // 4):
            directories.append(legitimate[legitimate_counter % len(legitimate)])
            directories.append(legitimate[(legitimate_counter + 1) % len(legitimate)])
            directories.append(legitimate[(legitimate_counter + 2) % len(legitimate)])
            directories.extend(random.sample(wordlist, 1))
            legitimate_counter += 3
    else:
        directories.extend(wordlist)
        directories.extend(random.sample(wordlist, len(wordlist) % 4))
    
    start_time = time.time()
    delay = None
    request_counter = 0
    change_threshold = random.randint(*change_interval)  
    
    if tor_proxy:
        set_tor_proxy()
        current_proxy = None
    else:
        current_proxy = random.choice(proxy_list) if proxy_list else None
    
    for dir in directories:
        full_url = f"{url}/{dir}"
        delay = random.choice(delay_range)
        
        if request_counter >= change_threshold:
            if tor_proxy:
                print("Set new IP via TOR!")
                change_tor_ip()
            elif proxy_list:
                current_proxy = random.choice(proxy_list)
            
            request_counter = 0
            change_threshold = random.randint(*change_interval)

        while True:
        
            proxy_dict = {}
            if not tor_proxy and current_proxy:
                proxy_dict = create_proxy_dict(current_proxy)
            
            response, proxy_is_failed = craft_request(full_url, delay, proxy_dict, get_random_user_agent())
            request_counter += 1
            
            if proxy_is_failed:
                if not tor_proxy and current_proxy in proxy_list:
                    proxy_list.remove(current_proxy)
                    if proxy_list:
                        current_proxy = random.choice(proxy_list)
                        request_counter = 0 
                    else:
                        print("No more proxies available!")
                        break
            else:
                break
            
            if dir not in legitimate and response.status_code != 404:
                print("need save...")
                output_file.write(f"URL: {full_url} | Status: {response.status_code} | Text:\n{response.text}")
                output_file.flush()
    
    output_file.close()


def craft_request(url, delay, proxy, user_agent):
    result_string = 'URL: {}'
    response = None
    proxy_failed = False
    
    try:
        if proxy:
            response = requests.get(
                url,
                headers={'User-Agent': user_agent},
                proxies=proxy,
                timeout=20 
            )
            print((result_string + ' | Status: {} | Proxy: {}').format(
                url, 
                response.status_code, 
                proxy['http'].split('socks5://')[1]
            ))
        else:
            response = requests.get(
                url,
                headers={'User-Agent': user_agent},
                timeout=20
            )
            print((result_string + ' | Status: {}').format(url, response.status_code))
        time.sleep(delay) 
            
    except (requests.exceptions.Timeout, 
            requests.exceptions.ConnectionError,
            requests.exceptions.ProxyError) as e:
        print(f"Error for {url} with proxy {proxy['http'].split('socks5://')[1]}, remove from list...")
        proxy_failed = True
        time.sleep(delay) 
        
    return response, proxy_failed

def init_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='silent_fuzz',
    )
    parser.add_argument('-u', '--url', help='Url for fuzzing directories', required=True)
    parser.add_argument('-w', '--wordlist', help='Wordlist for fuzzing directories', required=True)
    parser.add_argument('-l', '--legitimate', help='Legitimate directories for fuzzing')
    parser.add_argument('-o', '--output', help='Output file with results', required=True)
    parser.add_argument('-p', '--proxy-list', help='List with proxies')
    parser.add_argument('--tor-proxy', help='Use local tor socks server', action='store_true')
    parser.add_argument('--delay', help='Range of delays between requests (min,max)', type=str, default='1,5')

    return parser


def main():
    parser = init_cli()
    args = parser.parse_args()

    delay_min, delay_max = map(int, args.delay.split(','))
    delay_range = range(delay_min, delay_max + 1)

    with open(args.wordlist, 'r') as file:
        wordlist = [line.strip() for line in file.readlines()]

    if args.legitimate:
        with open(args.legitimate, 'r') as file:
            legitimate = [line.strip() for line in file.readlines()]
    else:
        legitimate = []

    if args.proxy_list:
        with open(args.proxy_list, 'r') as file:
            proxy_list = [line.strip() for line in file.readlines()]
    else:
        proxy_list = []

    if args.tor_proxy:
        set_tor_proxy()

    run_fuzz(args.url, wordlist, legitimate, proxy_list, delay_range, args.output, args.tor_proxy)


if __name__ == '__main__':
    main()
