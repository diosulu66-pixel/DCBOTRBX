import requests
import xml.etree.ElementTree as ET
import os
import ctypes
import time
import sys
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

ctypes.windll.kernel32.SetConsoleTitleW("Clothing Stealer | Clothing Texture Grabber")

if not os.path.isdir('output'):
    os.mkdir('output')

session = requests.Session()

COOKIE_FILE = 'cookie.txt'

def load_cookie():
    if os.path.exists(COOKIE_FILE):
        with open(COOKIE_FILE, 'r') as f:
            return f.read().strip()
    return None

def save_cookie(cookie_value):
    with open(COOKIE_FILE, 'w') as f:
        f.write(cookie_value)

def set_auth_cookie(cookie_value):
    session.cookies.set('.ROBLOSECURITY', cookie_value, domain='.roblox.com')

def get_asset_location(asset_id):
    url = f"https://assetdelivery.roblox.com/v1/assetId/{asset_id}"
    try:
        response = session.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get('location')
        else:
            print(f"{Fore.RED}Error requesting assetdelivery: {response.status_code}")
            return None
    except Exception as e:
        print(f"{Fore.RED}Error requesting: {e}")
        return None

def extract_texture_id(xml_content):
    try:
        root = ET.fromstring(xml_content)
        for elem in root.iter():
            if elem.tag == 'url':
                url_text = elem.text
                if 'id=' in url_text:
                    texture_id = int(url_text.split('=')[1])
                    return texture_id
    except ET.ParseError:
        print(f"{Fore.RED}Error parsing XML for asset")
    return None

def download_texture(asset_id, assetType):
    def a2n(a):
        if str(a) == '11': return '-Shirt'
        if str(a) == '12': return '-Pants'
        return ''

    # Get data
    asset_url = get_asset_location(asset_id)
    if not asset_url:
        print(f"{Fore.RED}Could not get URL for asset {asset_id}")
        return

    response = requests.get(asset_url)
    if response.status_code != 200:
        print(f"{Fore.RED}Error downloading asset {asset_id}")
        return

    content = response.text

    # Determine content type
    if content.startswith('<roblox'):
        # It's XML, find texture ID
        texture_id = extract_texture_id(content)
        if not texture_id:
            print(f"{Fore.RED}Could not extract texture ID for {asset_id}")
            return

        # Download the actual texture
        texture_url = get_asset_location(texture_id)
        if not texture_url:
            print(f"{Fore.RED}Could not get texture URL for {texture_id}")
            return

        img_response = requests.get(texture_url)
        if img_response.status_code != 200:
            print(f"{Fore.RED}Error downloading texture {texture_id}")
            return

        # Save as PNG
        filename = f"output/{asset_id}{a2n(assetType)}.png"
        with open(filename, 'wb') as f:
            f.write(img_response.content)
        print(f"{Fore.GREEN}Saved: {filename}")
    else:
        # It's already PNG
        filename = f"output/{asset_id}{a2n(assetType)}.png"
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"{Fore.GREEN}Saved: {filename}")

def get_clothing_from_group(groupID):
    IDs = []
    cursor = ''
    while True:
        url = f"https://catalog.roblox.com/v1/search/items/details?Category=3&CreatorType=2&IncludeNotForSale=false&Limit=30&CreatorTargetId={groupID}&cursor={cursor}"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"{Fore.YELLOW}Rate limited! Please wait 30 seconds.")
            time.sleep(30)
            continue

        data = response.json()
        if 'nextPageCursor' not in data:
            print(f"{Fore.YELLOW}API Error, skipping...")
            time.sleep(30)
            continue

        cursor = data['nextPageCursor']
        for x in data['data']:
            asset_type = x.get('assetType')
            if str(asset_type) in ['11', '12']:
                IDs.append([x['id'], asset_type])

        if not cursor:
            break
    return IDs

def check_and_load_cookie():
    cookie = load_cookie()
    if cookie:
        set_auth_cookie(cookie)
        return True
    else:
        print(f"{Fore.YELLOW}No cookie found! Please set it in the menu first (Option 3).")
        time.sleep(2)
        return False

def display_menu():
    while True:
        os.system('cls')
        print(f"{Fore.LIGHTMAGENTA_EX}" + r"""
    ███╗   ███╗███████╗███╗   ██╗██╗   ██╗
    ████╗ ████║██╔════╝████╗  ██║██║   ██║
    ██╔████╔██║█████╗  ██╔██╗ ██║██║   ██║
    ██║╚██╔╝██║██╔══╝  ██║╚██╗██║██║   ██║
    ██║ ╚═╝ ██║███████╗██║ ╚████║╚██████╔╝
    ╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ 
""")
        print(f"{Fore.LIGHTYELLOW_EX}═══════════════════════════════════════════════════════════════════════════════════════════════════════")

        print(f"\n{Fore.LIGHTCYAN_EX}┌─────────────────────────────────────────────────────────────────────────────────────────────────┐")
        print(f"{Fore.LIGHTCYAN_EX}│{Fore.LIGHTWHITE_EX}                                    MAIN MENU                                                  {Fore.LIGHTCYAN_EX}│")
        print(f"{Fore.LIGHTCYAN_EX}├─────────────────────────────────────────────────────────────────────────────────────────────────┤")
        print(f"{Fore.LIGHTCYAN_EX}│{Fore.LIGHTYELLOW_EX}  [1] {Fore.LIGHTGREEN_EX}Download clothing by asset ID                                                           {Fore.LIGHTCYAN_EX}│")
        print(f"{Fore.LIGHTCYAN_EX}│{Fore.LIGHTYELLOW_EX}  [2] {Fore.LIGHTGREEN_EX}Download clothing from group by group ID                                                  {Fore.LIGHTCYAN_EX}│")
        print(f"{Fore.LIGHTCYAN_EX}│{Fore.LIGHTYELLOW_EX}  [3] {Fore.LIGHTGREEN_EX}Set/Update .ROBLOSECURITY Cookie                                                          {Fore.LIGHTCYAN_EX}│")
        print(f"{Fore.LIGHTCYAN_EX}│{Fore.LIGHTYELLOW_EX}  [4] {Fore.LIGHTGREEN_EX}Exit                                                                                      {Fore.LIGHTCYAN_EX}│")
        print(f"{Fore.LIGHTCYAN_EX}└─────────────────────────────────────────────────────────────────────────────────────────────────┘")

        mode = input(f"\n{Fore.LIGHTBLUE_EX}Choose action (1-4): ").strip()

        if mode == '1':
            if not check_and_load_cookie(): continue
            id_input = input(f"{Fore.LIGHTBLUE_EX}Enter Asset ID: ").strip()
            if id_input.isdigit():
                print('\n')
                download_texture(int(id_input), 'idk')
                print(f"\n{Fore.GREEN}Done.")
                input(f"{Fore.LIGHTYELLOW_EX}Press ENTER to return to menu.")
            else:
                print(f"{Fore.RED}Invalid ID.")
                time.sleep(1)

        elif mode == '2':
            if not check_and_load_cookie(): continue
            id_input = input(f"{Fore.LIGHTBLUE_EX}Enter Group ID: ").strip()
            if id_input.isdigit():
                print(f"\n{Fore.CYAN}Collecting items from group...")
                catalog = get_clothing_from_group(int(id_input))
                print(f"{Fore.CYAN}Found {len(catalog)} items. Downloading...")
                for item in catalog:
                    download_texture(item[0], item[1])
                print(f"\n{Fore.GREEN}Done.")
                input(f"{Fore.LIGHTYELLOW_EX}Press ENTER to return to menu.")
            else:
                print(f"{Fore.RED}Invalid ID.")
                time.sleep(1)

        elif mode == '3':
            print(f"\n{Fore.YELLOW}Current cookie status: {'Loaded' if load_cookie() else 'Not Set'}")
            cookie = input(f"{Fore.LIGHTBLUE_EX}Enter new .ROBLOSECURITY cookie (or press Enter to cancel): ").strip()
            if cookie:
                save_cookie(cookie)
                set_auth_cookie(cookie)
                print(f"{Fore.GREEN}Cookie saved and updated successfully!")
            else:
                print(f"{Fore.YELLOW}Operation cancelled.")
            time.sleep(1.5)

        elif mode == '4':
            print(f"{Fore.GREEN}Exiting...")
            break

        else:
            print(f"{Fore.RED}Invalid choice. Please try again.")
            time.sleep(1)

if __name__ == '__main__':
    display_menu()
