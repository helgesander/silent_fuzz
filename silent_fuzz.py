import time
import requests
import argparse
import random
import urllib3
from UserAgenter import UserAgent
from requests_tor import RequestsTor

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

def write_to_file(data, output):
    with open(output, "w", encoding='utf-8') as f:
        for item in data:
            f.write(f'DIR: {item['dir']} | Status {item['status_code']} | Length: {item['content_length']}\n')


def run_fuzz(url, wordlist, legitimate, proxy_list, delay_range, output, tor_proxy=False, change_interval=(5, 25)):
    directories = []
    output_file = open(output, 'w')
    results = []
    sorted_results = []

    
    if len(legitimate) > 0:
        word_counter = 0
        dir_counter = 0
        while word_counter != len(wordlist):
            if dir_counter % 4 > 0:
                directories.append(random.choice(legitimate))
            else:
                directories.append(wordlist[word_counter])
                word_counter += 1
            dir_counter += 1
    else:
        directories.extend(wordlist)

    delay = None
    request_counter = 0
    change_threshold = random.randint(*change_interval)  

    rt = None

    if tor_proxy:
        rt = RequestsTor(tor_ports=(9050,), tor_cport=9051, password=None,
                     autochange_id=10, threads=1)
        current_proxy = None
    else:
        current_proxy = random.choice(proxy_list) if proxy_list else None
    
    for d in directories:
        full_url = f"{url}/{d}"
        delay = random.choice(delay_range)
        
        if request_counter >= change_threshold:
            if proxy_list:
                current_proxy = random.choice(proxy_list)
            
            request_counter = 0
            change_threshold = random.randint(*change_interval)

        while True:
            proxy_dict = {}
            if not tor_proxy and current_proxy:
                proxy_dict = create_proxy_dict(current_proxy)
            
            response, proxy_is_failed = craft_request(rt, full_url, delay, proxy_dict, get_random_user_agent())

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
                    rt.new_id()
            else:
                if d not in legitimate:
                    results.append({
                        'dir': d,
                        'status_code': response.status_code,
                        'content_length': len(response.text),
                    })
                break
            
    sorted_results = sorted(results, key=lambda x: (x['status_code'], x['content_length']))
    write_to_file(sorted_results, output)
    
    output_file.close()


def craft_request(rt, url, delay, proxy, user_agent):
    result_string = 'URL: {} | Status: {}'
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
            print((result_string + ' | Proxy: {}').format(
                url, 
                response.status_code, 
                proxy['http'].split('socks5://')[1]
            ))
        else:
            response = rt.get(
                url,
                headers={'User-Agent': user_agent},
                timeout=20
            )
            print((result_string).format(url, response.status_code))
        time.sleep(delay) 
            
    except (requests.exceptions.Timeout, 
            requests.exceptions.ConnectionError,
            requests.exceptions.ProxyError) as e:
        if proxy:
            print(f"Error for {url} with proxy {proxy['http'].split('socks5://')[1]}, remove from list...")
            proxy_failed = True
        else: 
            print(f'Error for {url} with tor {rt.check_ip()}')
            proxy_failed = True
            time.sleep(delay) 
        
    return response, proxy_failed

def init_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog='silent_fuzz.py',
    )
    parser.add_argument('-u', '--url', help='Url for fuzzing directories', required=True)
    parser.add_argument('-w', '--wordlist', help='Wordlist for fuzzing directories', required=True)
    parser.add_argument('-l', '--legitimate', help='Legitimate directories for fuzzing')
    parser.add_argument('-o', '--output', help='Output file with results', required=True)
    parser.add_argument('-p', '--proxy-list', help='List with proxies')
    parser.add_argument('--tor-proxy', help='Use local tor socks server', action='store_true')
    parser.add_argument('--delay', help='Range of delays between requests (min,max), default 1,5', type=str, default='1,5')

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

    run_fuzz(args.url, wordlist, legitimate, proxy_list, delay_range, args.output, args.tor_proxy)


if __name__ == '__main__':
    main()
