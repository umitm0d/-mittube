import base64
import os
import re
import requests
import urllib3
import sys

# SSL uyarılarını bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Direk GitHub Secret'ten al
ENCRYPTED_URL = os.environ.get('ENCRYPTED_PLAYLIST_URL')
if not ENCRYPTED_URL:
    print("HATA: ENCRYPTED_PLAYLIST_URL GitHub Secret'ı bulunamadı!")
    sys.exit(1)

def create_umittube_folder():
    if not os.path.exists("Ümittube"):
        os.makedirs("Ümittube")

def decrypt_url():
    decrypted_bytes = base64.b64decode(ENCRYPTED_URL)
    return decrypted_bytes.decode("utf-8")

def fetch_playlist(url):
    response = requests.get(url, verify=False, timeout=30)
    response.raise_for_status()
    return response.text

def parse_playlist(content):
    lines = content.strip().split("\n")
    channels = []
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            match = re.search(r",(.+)$", lines[i])
            if match and i + 1 < len(lines) and not lines[i + 1].startswith("#"):
                channel_name = match.group(1).strip()
                channel_url = lines[i + 1].strip()
                channels.append((channel_name, channel_url))
    return channels

def save_channel_as_m3u8(channel_name, stream_url):
    safe_name = "".join(c for c in channel_name if c.isalnum() or c in ".-_").rstrip()
    filename = f"Ümittube/{safe_name}.m3u8"
    content = f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=1280x720
{stream_url}
"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {filename}")
    return safe_name

def create_master_playlist(channels):
    """Ana M3U listesi oluşturur"""
    master_content = ["#EXTM3U"]
    master_content.append("# Playlist: Ümittube")
    master_content.append(f"# Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    master_content.append(f"# Total channels: {len(channels)}")
    master_content.append("")
    
    for channel_name, stream_url in channels:
        # Kanal bilgisi
        master_content.append(f"#EXTINF:-1 tvg-logo=\"\" group-title=\"Ümittube\",{channel_name}")
        master_content.append(stream_url)
        master_content.append("")
    
    master_filename = "Ümittube/umittube.m3u"
    with open(master_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(master_content))
    print(f"✅ Master playlist saved: {master_filename}")
    
    # Ayrıca raw URL için GitHub'a uygun version
    github_filename = "Ümittube/umittube_github.m3u"
    github_content = ["#EXTM3U"]
    for channel_name, stream_url in channels:
        github_content.append(f"#EXTINF:-1,{channel_name}")
        github_content.append(stream_url)
    
    with open(github_filename, "w", encoding="utf-8") as f:
        f.write("\n".join(github_content))
    print(f"✅ GitHub compatible playlist saved: {github_filename}")

def main():
    try:
        create_umittube_folder()
        playlist_url = decrypt_url()
        print(f"Fetching playlist from: {playlist_url[:50]}...")
        playlist_content = fetch_playlist(playlist_url)
        channels = parse_playlist(playlist_content)
        
        if not channels:
            print("No channels found in playlist.")
            return
        
        print(f"\n📺 Found {len(channels)} channels. Processing...\n")
        
        for name, url in channels:
            save_channel_as_m3u8(name, url)
        
        # Ana M3U listesini oluştur
        create_master_playlist(channels)
        
        print(f"\n✅ Successfully saved {len(channels)} channels to Ümittube/")
        print("📁 Files:")
        print("   - Ümittube/umittube.m3u (master playlist)")
        print("   - Ümittube/umittube_github.m3u (GitHub raw friendly)")
        print("   - Ümittube/*.m3u8 (individual channel files)")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
