#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Like4Like Multi-Mode Bot (IG/Twitter/YouTube)
- Autosave cookies per platform into Penyimpanan/Cookies.json
- Menu includes:
  1) YouTube Like
  2) YouTube Subscribe
  3) Instagram Follow
  4) Twitter Follow
  5) Twitter Like
  6) Twitter Retweet
- Keeps original rich TUI vibe
- Uses request-based action: for all except Instagram Follow, we only open the target URL
  with the corresponding platform cookies (most L4L tasks validate via URL access).

Notes:
- No username/password login (avoids CAPTCHA). We stick to cookies.
- If a required platform cookie is missing, the bot will prompt once and autosave.
- Delay between tasks is configurable.
"""

import os, json, time, re, datetime
import requests
from typing import Optional, Dict, Any

try:
    from rich import print as rprint
    from rich.console import Console
    from rich.panel import Panel
    from rich.columns import Columns
except ModuleNotFoundError as e:
    exit(f"[Error] {str(e).capitalize()}! Install 'rich' -> pip install rich")

# --------------------------- CONSTANTS & MAPPINGS --------------------------- #
PENYIMPANAN_DIR = "Penyimpanan"
COOKIES_PATH = os.path.join(PENYIMPANAN_DIR, "Cookies.json")

# Like4Like "feature" keys and their earn pages + vrsta (type)
FEATURES: Dict[str, Dict[str, str]] = {
    # Menu label -> {feature, earn_page, vrsta}
    "yt_like":      {"feature": "youtube",    "earn": "/user/earn-youtube.php",             "vrsta": "like"},
    "yt_subscribe": {"feature": "youtubes",   "earn": "/user/earn-youtube-subscribe.php",  "vrsta": "subscribe"},
    "ig_follow":    {"feature": "instagramfol","earn": "/user/earn-instagram-follow.php",   "vrsta": "follow"},
    "tw_follow":    {"feature": "twitter",    "earn": "/user/earn-twitter.php",            "vrsta": "follow"},
    "tw_like":      {"feature": "twitterfav", "earn": "/user/earn-twitter-favorites.php",  "vrsta": "like"},
    "tw_retweet":   {"feature": "twitterret", "earn": "/user/earn-twitter-retweet.php",    "vrsta": "retweet"},
}

PLATFORM_COOKIE_KEYS = {
    "yt_like": "Cookies_Youtube",
    "yt_subscribe": "Cookies_Youtube",
    "ig_follow": "Cookies_Instagram",
    "tw_follow": "Cookies_Twitter",
    "tw_like": "Cookies_Twitter",
    "tw_retweet": "Cookies_Twitter",
}

# ------------------------------ UTILITIES ---------------------------------- #
class Store:
    @staticmethod
    def ensure_dir() -> None:
        if not os.path.isdir(PENYIMPANAN_DIR):
            os.makedirs(PENYIMPANAN_DIR, exist_ok=True)

    @staticmethod
    def load() -> Dict[str, Any]:
        Store.ensure_dir()
        if not os.path.exists(COOKIES_PATH):
            return {}
        try:
            with open(COOKIES_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def save(data: Dict[str, Any]) -> None:
        Store.ensure_dir()
        with open(COOKIES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

# ------------------------------ UI ----------------------------------------- #

def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    rprint(Panel(r"""[bold red]  _      _ _        _  _    _____                     
 | |    (_) |      | || |  / ____|                    
 | |     _| | _____| || |_| |  __ _ __ __ _ _ __ ___  
 | |    | | |/ / _ \__   _| | |_ | '__/ _` | '_ ` _ \ 
 | |____| |   <  __/  | | | |__| | | | (_| | | | | | |
[bold white] |______|_|_|\_\___|  |_|  \_____|_|  \__,_|_| |_| |_| 
        [underline green]Like4Like Multi - IG/Twitter/YouTube""", width=74, style="bold bright_black"))


def show_status(username: str, credits: int):
    rprint(Columns([
        Panel(f"[bold white]Like4Like :[bold green] {username}", width=36, style="bold bright_black"),
        Panel(f"[bold white]Koin :[bold red] {credits}", width=36, style="bold bright_black"),
    ]))


def menu() -> str:
    rprint(Panel("""
[bold white][[bold green]1[bold white]] YouTube Like
[bold white][[bold green]2[bold white]] YouTube Subscribe
[bold white][[bold green]3[bold white]] Instagram Follow
[bold white][[bold green]4[bold white]] Twitter Follow
[bold white][[bold green]5[bold white]] Twitter Like
[bold white][[bold green]6[bold white]] Twitter Retweet
[bold white][[bold green]7[bold white]] Keluar (Exit)
""", width=74, style="bold bright_black", subtitle="[bold bright_black]╭─────", subtitle_align="left"))
    choice = Console().input("[bold bright_black]   ╰─> ").strip()
    mapping = {
        "1": "yt_like",
        "2": "yt_subscribe",
        "3": "ig_follow",
        "4": "tw_follow",
        "5": "tw_like",
        "6": "tw_retweet",
        "7": "exit",
    }
    return mapping.get(choice, "")

# ------------------------------ L4L CLIENT --------------------------------- #

class L4L:
    BASE = "https://www.like4like.org"

    def __init__(self, cookies_l4l: str):
        self.cookies_l4l = cookies_l4l
        self.session = requests.Session()
        # set common headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Connection': 'keep-alive',
        })

    def _cookie_dict(self) -> Dict[str, str]:
        return { 'Cookie': self.cookies_l4l }

    def warmup(self, earn_path: str) -> None:
        # Visit the earn page to set proper referrers, etc.
        self.session.get(f"{self.BASE}{earn_path}", cookies=self._cookie_dict())

    def get_user_info(self) -> Optional[Dict[str, Any]]:
        # Same logic as original: api/get-user-info.php
        self.session.headers.update({
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': f'{self.BASE}/',
        })
        try:
            resp = self.session.get(f"{self.BASE}/api/get-user-info.php", cookies=self._cookie_dict(), timeout=30)
            if resp.ok and 'success' in resp.text:
                data = resp.json().get('data')
                return data
        except Exception:
            pass
        return None

    def get_tasks(self, feature: str) -> Optional[list]:
        # get-tasks
        self.session.headers.update({
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Referer': f'{self.BASE}/',
        })
        try:
            url = f"{self.BASE}/api/get-tasks.php?feature={feature}"
            resp = self.session.get(url, cookies=self._cookie_dict(), timeout=30)
            if resp.ok and 'success' in resp.text:
                j = resp.json()
                return j.get('data', {}).get('tasks', [])
        except Exception:
            pass
        return None

    def start_task(self, idlink: str, taskId: str, feature: str) -> bool:
        # start-task
        ts_ms = str(int(datetime.datetime.now().timestamp() * 1000))
        self.session.headers.update({'Content-Type': 'application/json; charset=utf-8'})
        url = f"{self.BASE}/api/start-task.php?idzad={idlink}&vrsta={feature}&idcod={taskId}&feature={feature}&_={ts_ms}"
        # Note: historical code used vrsta=follow, but L4L seems to accept feature duplication.
        # If start fails, we'll fallback by trying vrsta=follow for IG.
        try:
            resp = self.session.get(url, cookies=self._cookie_dict(), timeout=30)
            if '"success":true' in resp.text:
                return True
        except Exception:
            pass
        return False

    def check_url(self, target_url: str) -> bool:
        # checkurl.php expects form-urlencoded {url: target_url}
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Origin': self.BASE,
            'Referer': f'{self.BASE}/',
        })
        try:
            resp = self.session.post(f"{self.BASE}/checkurl.php", data={'url': target_url}, cookies=self._cookie_dict(), timeout=30)
            return resp.ok and ("http" in resp.text)
        except Exception:
            return False

    def validate(self, feature: str, vrsta: str, idlinka: str, idzad: str, idclana: str, target_url: str) -> Optional[str]:
        # validate-task.php -> returns credits string on success
        self.session.headers.update({
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Origin': self.BASE,
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'{self.BASE}{FEATURES_BY_FEATURE[feature]["earn"] if feature in FEATURES_BY_FEATURE else '/user/'}',
            'X-Requested-With': 'XMLHttpRequest',
        })
        data = {
            'url': target_url,
            'idlinka': idlinka,
            'idzad': idzad,
            'addon': False,
            'version': '',
            'idclana': idclana,
            'cnt': True,
            'vrsta': vrsta,
            'feature': feature,
        }
        try:
            resp = self.session.post(f"{self.BASE}/api/validate-task.php", data=data, cookies=self._cookie_dict(), timeout=30)
            if resp.ok and '"success":true' in resp.text and '"credits"' in resp.text:
                m = re.search(r'"credits":"(\d+)"', resp.text)
                if m:
                    return m.group(1)
        except Exception:
            pass
        return None

# Reverse index to fetch earn page inside validate headers
FEATURES_BY_FEATURE = {v['feature']: v for v in FEATURES.values()}

# ------------------------------ PLATFORM ACTIONS --------------------------- #

class Actions:
    @staticmethod
    def open_with_cookies(url: str, cookies: str) -> bool:
        try:
            with requests.Session() as s:
                s.headers.update({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                })
                r = s.get(url, cookies={'Cookie': cookies}, timeout=30, allow_redirects=True)
                return r.status_code == 200
        except Exception:
            return False

    @staticmethod
    def instagram_follow(username_or_url: str, cookies_instagram: str) -> bool:
        # Use the light approach similar to original: open profile, extract profilePage id, then POST follow.
        try:
            with requests.Session() as s:
                s.headers.update({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                })
                username = username_or_url.replace('https://www.instagram.com/', '').strip('/')
                r = s.get(f'https://www.instagram.com/{username}', cookies={'Cookie': cookies_instagram}, timeout=30)
                m = re.search(r'"profilePage_(\d+)"', r.text)
                if not m:
                    return False
                profile_id = m.group(1)
                # prepare follow
                csrftoken_match = re.search(r'csrftoken=([^;]+);', cookies_instagram)
                if not csrftoken_match:
                    return False
                csrftoken = csrftoken_match.group(1)
                s.headers.update({
                    'Referer': f'https://www.instagram.com/{username}',
                    'X-IG-App-ID': '936619743392459',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-Instagram-AJAX': '1012867433',
                    'X-IG-WWW-Claim': '0',
                    'X-CSRFToken': csrftoken,
                    'Accept': '*/*',
                    'X-ASBD-ID': '129477',
                    'Origin': 'https://www.instagram.com',
                    'Content-Type': 'application/x-www-form-urlencoded',
                })
                data = {
                    'container_module': 'profile',
                    'nav_chain': 'PolarisProfilePostsTabRoot:profilePage:1:via_cold_start',
                    'user_id': profile_id,
                }
                rf = s.post(f'https://www.instagram.com/api/v1/friendships/create/{profile_id}/', data=data, cookies={'Cookie': cookies_instagram}, timeout=30)
                return rf.ok
        except Exception:
            return False

# ------------------------------ BOT LOGIC ---------------------------------- #

class Bot:
    def __init__(self) -> None:
        Store.ensure_dir()
        self.db = Store.load()
        self.cookies_l4l = self.db.get('Cookies_Like4Like', '')

    def request_l4l_cookies(self) -> None:
        banner()
        rprint(Panel("[bold white]Masukkan cookies akun Like4Like kamu. Pastikan valid & login aktif!", width=74, style="bold bright_black", title="[bold bright_black]>> [Like4Like Cookies] <<", subtitle="[bold bright_black]╭─────", subtitle_align="left"))
        self.cookies_l4l = Console().input("[bold bright_black]   ╰─> ")
        self.db['Cookies_Like4Like'] = self.cookies_l4l
        Store.save(self.db)

    def ensure_platform_cookies(self, key: str, prompt_label: str) -> str:
        val = self.db.get(key, '')
        if val:
            return val
        rprint(Panel(f"[bold white]Masukkan cookies {prompt_label} (disarankan pakai akun fresh/fake).", width=74, style="bold bright_black", title=f"[bold bright_black]>> [{prompt_label} Cookies] <<", subtitle="[bold bright_black]╭─────", subtitle_align="left"))
        val = Console().input("[bold bright_black]   ╰─> ")
        self.db[key] = val
        Store.save(self.db)
        return val

    def run(self) -> None:
        # Ensure L4L cookies exist/valid
        if not self.cookies_l4l:
            self.request_l4l_cookies()
        client = L4L(self.cookies_l4l)
        info = client.get_user_info()
        if not info:
            rprint(Panel("[bold red]Cookies Like4Like invalid atau expired. Silakan input ulang.", width=74, style="bold bright_black", title="[bold bright_black]>> [Cookies Invalid] <<"))
            time.sleep(10)
            self.request_l4l_cookies()
            client = L4L(self.cookies_l4l)
            info = client.get_user_info()
            if not info:
                rprint(Panel("[bold red]Gagal memverifikasi Like4Like. Coba lagi nanti.", width=74, style="bold bright_black", title="[bold bright_black]>> [Error] <<"))
                return

        username = info.get('username', 'Unknown') if isinstance(info, dict) else 'Unknown'
        credits = int(info.get('credits', 0)) if isinstance(info, dict) else 0
        banner()
        show_status(username, credits)

        # Delay input
        rprint(Panel("[bold white]Masukkan delay antar misi (detik). Disarankan ≥ 60 detik biar aman.", width=74, style="bold bright_black", title="[bold bright_black]>> [Jeda Misi] <<", subtitle="[bold bright_black]╭─────", subtitle_align="left"))
        try:
            delay = int(Console().input("[bold bright_black]   ╰─> ").strip())
        except ValueError:
            delay = 60

        # Tampilkan menu hanya sekali di awal
        choice = menu()
        if choice == "exit" or choice == "":
            rprint(Panel("[bold white]Keluar. Terima kasih sudah memakai bot!", width=74, style="bold bright_black", title="[bold bright_black]>> [Exit] <<"))
            return

        # Dapatkan detail fitur yang dipilih
        feat = FEATURES[choice]
        feature = feat['feature']
        earn = feat['earn']
        vrsta = feat['vrsta']

        # Dapatkan cookies platform yang relevan
        platform_key = PLATFORM_COOKIE_KEYS[choice]
        platform_label = platform_key.replace('Cookies_', '').replace('_', ' ')
        platform_cookie = self.ensure_platform_cookies(platform_key, platform_label)

        while True:  # Loop ini akan terus berjalan untuk jenis tugas yang sama
            client.warmup(earn)

            # fetch tasks
            tasks = client.get_tasks(feature)
            if not tasks:
                rprint(Panel("[bold red]Tidak ada task saat ini atau terdeteksi bot. Coba lagi nanti.", width=74, style="bold bright_black", title="[bold bright_black]>> [Info] <<"))
                time.sleep(10)
                continue  # Lanjutkan ke iterasi berikutnya dari loop while True

            # process first available task each loop
            processed_any = False
            for t in tasks:
                try:
                    idlink = t['idlink']  # usually username or channel id
                    taskId = t['taskId']
                    code3 = t['code3']
                except KeyError:
                    rprint(f"[bold bright_black]   ╰─>[bold red] Data task tidak lengkap, melewati.     ", end='\r')
                    time.sleep(10)
                    continue

                # Start task
                started = client.start_task(idlink, taskId, feature)
                if not started:
                    rprint(f"[bold bright_black]   ╰─>[bold red] Gagal start task untuk {idlink}     ", end='\r')
                    time.sleep(10)
                    continue

                # Determine target URL by feature
                target_url = None
                if feature == 'instagramfol':
                    target_url = f'https://www.instagram.com/{idlink}'
                elif feature in ('twitter', 'twitterfav', 'twitterret'):
                    target_url = f'https://x.com/{idlink}'
                elif feature in ('youtube', 'youtubes'):
                    if idlink.startswith('watch?v='):
                        target_url = f'https://www.youtube.com/{idlink}'
                    else:
                        target_url = f'https://www.youtube.com/{idlink}' if idlink.startswith('channel/') or idlink.startswith('c/') else f'https://www.youtube.com/watch?v={idlink}'
                else:
                    target_url = f'https://www.instagram.com/{idlink}'

                # checkurl gate
                ok_redirect = client.check_url(target_url)
                if not ok_redirect:
                    rprint(f"[bold bright_black]   ╰─>[bold red] Tidak mendapatkan redirect URL!         ", end='\r')
                    time.sleep(10)
                    continue

                # Perform platform action
                success_action = False
                if feature == 'instagramfol':
                    success_action = Actions.instagram_follow(idlink, self.db.get('Cookies_Instagram', ''))
                else:
                    success_action = Actions.open_with_cookies(target_url, platform_cookie)

                if not success_action:
                    rprint(f"[bold bright_black]   ╰─>[bold red] Gagal melakukan aksi di platform untuk {idlink}!     ", end='\r')
                    time.sleep(10)
                    continue

                time.sleep(10)  # Delay sebelum validasi

                # validate
                credits_str = client.validate(feature, vrsta, idlink, taskId, code3, target_url)
                if credits_str:
                    credits = int(credits_str)
                    rprint(Panel(f"""
[bold white]Status :[bold green] Successfully...
[bold white]Task   :[bold yellow] {feature} / {vrsta}
[bold white]Link   :[bold red] {target_url}
[bold white]Credits:[bold green] +{credits}
""", width=74, style="bold bright_black", title="[bold bright_black]>> [Sukses] <<"))
                    processed_any = True
                    break  # process one task per loop
                else:
                    rprint(f"[bold bright_black]   ╰─>[bold red] Gagal validasi task untuk {idlink}!     ", end='\r')
                    time.sleep(10)
                    continue

            # Delay counter
            if processed_any:
                total = delay
                while total > 0:
                    m, s = divmod(total, 60)
                    rprint(f"[bold bright_black]   ╰─>[bold white] TUNGGU[bold green] {m:02d}:{s:02d}[bold white]    ", end='\r')
                    time.sleep(1)
                    total -= 1
            else:
                rprint(f"[bold bright_black]   ╰─>[bold yellow] Tidak ada task yang diproses, menunggu sebentar...     ", end='\r')
                time.sleep(10)


                

# ------------------------------ MAIN --------------------------------------- #

if __name__ == "__main__":
    try:
        Bot().run()
    except KeyboardInterrupt:
        rprint("\n[bold yellow]Dihentikan oleh user.")
    except Exception as e:
        rprint(Panel(f"[bold red]{str(e)}", width=74, style="bold bright_black", title="[bold bright_black]>> [Error] <<"))
