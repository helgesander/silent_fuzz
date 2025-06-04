# silent_fuzz

Чтобы работал tor proxy:

1. Добавить в `torrc`:  `ControlPort 9051`
2. Запустить tor (`SOCKSPort` должен быть 9050 (дефолтный))

## Help

```sh
usage: silent_fuzz.py [-h] -u URL -w WORDLIST [-l LEGITIMATE] -o OUTPUT [-p PROXY_LIST] [--tor-proxy] [--delay DELAY]

options:
  -h, --help            show this help message and exit
  -u, --url URL         Url for fuzzing directories
  -w, --wordlist WORDLIST
                        Wordlist for fuzzing directories
  -l, --legitimate LEGITIMATE
                        Legitimate directories for fuzzing
  -o, --output OUTPUT   Output file with results
  -p, --proxy-list PROXY_LIST
                        List with proxies
  --tor-proxy           Use local tor socks server
  --delay DELAY         Range of delays between requests (min,max), default 1,5
```
