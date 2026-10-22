import re
import os
import json
import base64

UUID = "21b64243-979f-4b72-b4cc-7f58bc9991be"
HOST_DOMAIN = "sg.729927.xyz"
REALITY_PUB = "dEHkxjc5euE5tmV2FJBRrEVv24WkBC3z3iB0IsOqRCU"
SERVER_IP = "103.72.62.103"

# Verified ultra-low-latency & zero-packet-loss Cloudflare endpoints in China
CF_DEFAULT_DOMAIN = "cf.090227.xyz"    # 默认高速接入（解决官方域名 Anycast IP 被阻断导致的超时）
CF_MULTI_DOMAIN = "cf.090227.xyz"      # CF多线全球优选域名 (延迟~230ms)
CF_BACKUP_DOMAIN = "cloudflare.182682.xyz" # CF备用优选域名 (延迟~340ms)
CF_UNICOM_IP = "104.18.37.247"         # CF联通优选 Anycast (0%丢包，实测稳定优选)
CF_TELECOM_IP = "172.64.146.125"       # CF电信优选 Anycast (0%丢包，实测极速响应)
CF_MOBILE_IP = "104.26.15.26"          # CF移动优选 Anycast (0%丢包，亚太低延迟)
CF_CLEAN_IP = "104.26.6.138"           # CF亚太纯净高带宽 Anycast

# 1. Custom nodes definition for Clash
custom_nodes_clash = [
    {
        "name": "SmartHost - SG - 2T xtls-reality (443)",
        "yaml": f'  - {{name: "SmartHost - SG - 2T xtls-reality (443)", type: vless, server: {SERVER_IP}, port: 443, uuid: {UUID}, network: tcp, udp: true, tls: true, flow: xtls-rprx-vision, servername: addons.mozilla.org, client-fingerprint: chrome, reality-opts: {{public-key: {REALITY_PUB}, short-id: ""}}, smux: {{ enabled: false, protocol: \'h2mux\', padding: false, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    },
    {
        "name": "SmartHost - SG - 2T vless-ws-tls",
        "yaml": f'  - {{name: "SmartHost - SG - 2T vless-ws-tls", type: vless, server: {CF_DEFAULT_DOMAIN}, port: 443, uuid: {UUID}, udp: true, tls: true, servername: {HOST_DOMAIN}, network: ws, skip-cert-verify: false, ws-opts: {{ path: "/{UUID}-vless", headers: {{Host: {HOST_DOMAIN}}}, max-early-data: 2560, early-data-header-name: Sec-WebSocket-Protocol }}, smux: {{ enabled: true, protocol: \'h2mux\', padding: true, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    },
    {
        "name": "SmartHost - SG - 2T vless-ws-tls (CF多线全球优选)",
        "yaml": f'  - {{name: "SmartHost - SG - 2T vless-ws-tls (CF多线全球优选)", type: vless, server: {CF_MULTI_DOMAIN}, port: 443, uuid: {UUID}, udp: true, tls: true, servername: {HOST_DOMAIN}, network: ws, skip-cert-verify: false, ws-opts: {{ path: "/{UUID}-vless", headers: {{Host: {HOST_DOMAIN}}}, max-early-data: 2560, early-data-header-name: Sec-WebSocket-Protocol }}, smux: {{ enabled: true, protocol: \'h2mux\', padding: true, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    },
    {
        "name": "SmartHost - SG - 2T vless-ws-tls (CF电信优选)",
        "yaml": f'  - {{name: "SmartHost - SG - 2T vless-ws-tls (CF电信优选)", type: vless, server: {CF_TELECOM_IP}, port: 443, uuid: {UUID}, udp: true, tls: true, servername: {HOST_DOMAIN}, network: ws, skip-cert-verify: false, ws-opts: {{ path: "/{UUID}-vless", headers: {{Host: {HOST_DOMAIN}}}, max-early-data: 2560, early-data-header-name: Sec-WebSocket-Protocol }}, smux: {{ enabled: true, protocol: \'h2mux\', padding: true, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    },
    {
        "name": "SmartHost - SG - 2T vless-ws-tls (CF联通优选)",
        "yaml": f'  - {{name: "SmartHost - SG - 2T vless-ws-tls (CF联通优选)", type: vless, server: {CF_UNICOM_IP}, port: 443, uuid: {UUID}, udp: true, tls: true, servername: {HOST_DOMAIN}, network: ws, skip-cert-verify: false, ws-opts: {{ path: "/{UUID}-vless", headers: {{Host: {HOST_DOMAIN}}}, max-early-data: 2560, early-data-header-name: Sec-WebSocket-Protocol }}, smux: {{ enabled: true, protocol: \'h2mux\', padding: true, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    },
    {
        "name": "SmartHost - SG - 2T vless-ws-tls (CF移动优选)",
        "yaml": f'  - {{name: "SmartHost - SG - 2T vless-ws-tls (CF移动优选)", type: vless, server: {CF_MOBILE_IP}, port: 443, uuid: {UUID}, udp: true, tls: true, servername: {HOST_DOMAIN}, network: ws, skip-cert-verify: false, ws-opts: {{ path: "/{UUID}-vless", headers: {{Host: {HOST_DOMAIN}}}, max-early-data: 2560, early-data-header-name: Sec-WebSocket-Protocol }}, smux: {{ enabled: true, protocol: \'h2mux\', padding: true, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    },
    {
        "name": "SmartHost - SG - 2T vless-ws-tls (CF亚太纯净IP)",
        "yaml": f'  - {{name: "SmartHost - SG - 2T vless-ws-tls (CF亚太纯净IP)", type: vless, server: {CF_CLEAN_IP}, port: 443, uuid: {UUID}, udp: true, tls: true, servername: {HOST_DOMAIN}, network: ws, skip-cert-verify: false, ws-opts: {{ path: "/{UUID}-vless", headers: {{Host: {HOST_DOMAIN}}}, max-early-data: 2560, early-data-header-name: Sec-WebSocket-Protocol }}, smux: {{ enabled: true, protocol: \'h2mux\', padding: true, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    },
    {
        "name": "SmartHost - SG - 2T vmess-ws",
        "yaml": f'  - {{name: "SmartHost - SG - 2T vmess-ws", type: vmess, server: {CF_DEFAULT_DOMAIN}, port: 443, uuid: {UUID}, udp: true, tls: true, servername: {HOST_DOMAIN}, alterId: 0, cipher: auto, network: ws, ws-opts: {{ path: "/{UUID}-vmess", headers: {{Host: {HOST_DOMAIN}}} }}, smux: {{ enabled: true, protocol: \'h2mux\', padding: true, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    },
    {
        "name": "SmartHost - SG - 2T vmess-ws (CF多线全球优选)",
        "yaml": f'  - {{name: "SmartHost - SG - 2T vmess-ws (CF多线全球优选)", type: vmess, server: {CF_MULTI_DOMAIN}, port: 443, uuid: {UUID}, udp: true, tls: true, servername: {HOST_DOMAIN}, alterId: 0, cipher: auto, network: ws, ws-opts: {{ path: "/{UUID}-vmess", headers: {{Host: {HOST_DOMAIN}}} }}, smux: {{ enabled: true, protocol: \'h2mux\', padding: true, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    },
    {
        "name": "SmartHost - SG - 2T vmess-ws (CF电信优选)",
        "yaml": f'  - {{name: "SmartHost - SG - 2T vmess-ws (CF电信优选)", type: vmess, server: {CF_TELECOM_IP}, port: 443, uuid: {UUID}, udp: true, tls: true, servername: {HOST_DOMAIN}, alterId: 0, cipher: auto, network: ws, ws-opts: {{ path: "/{UUID}-vmess", headers: {{Host: {HOST_DOMAIN}}} }}, smux: {{ enabled: true, protocol: \'h2mux\', padding: true, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    },
    {
        "name": "SmartHost - SG - 2T vmess-ws (CF联通优选)",
        "yaml": f'  - {{name: "SmartHost - SG - 2T vmess-ws (CF联通优选)", type: vmess, server: {CF_UNICOM_IP}, port: 443, uuid: {UUID}, udp: true, tls: true, servername: {HOST_DOMAIN}, alterId: 0, cipher: auto, network: ws, ws-opts: {{ path: "/{UUID}-vmess", headers: {{Host: {HOST_DOMAIN}}} }}, smux: {{ enabled: true, protocol: \'h2mux\', padding: true, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    },
    {
        "name": "SmartHost - SG - 2T vmess-ws (CF移动优选)",
        "yaml": f'  - {{name: "SmartHost - SG - 2T vmess-ws (CF移动优选)", type: vmess, server: {CF_MOBILE_IP}, port: 443, uuid: {UUID}, udp: true, tls: true, servername: {HOST_DOMAIN}, alterId: 0, cipher: auto, network: ws, ws-opts: {{ path: "/{UUID}-vmess", headers: {{Host: {HOST_DOMAIN}}} }}, smux: {{ enabled: true, protocol: \'h2mux\', padding: true, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    },
    {
        "name": "SmartHost - SG - 2T vmess-ws (CF亚太纯净IP)",
        "yaml": f'  - {{name: "SmartHost - SG - 2T vmess-ws (CF亚太纯净IP)", type: vmess, server: {CF_CLEAN_IP}, port: 443, uuid: {UUID}, udp: true, tls: true, servername: {HOST_DOMAIN}, alterId: 0, cipher: auto, network: ws, ws-opts: {{ path: "/{UUID}-vmess", headers: {{Host: {HOST_DOMAIN}}} }}, smux: {{ enabled: true, protocol: \'h2mux\', padding: true, max-connections: \'8\', min-streams: \'16\', statistic: true, only-tcp: false }}, brutal-opts: {{ enabled: false, up: \'1000 Mbps\', down: \'1000 Mbps\' }} }}'
    }
]

def clean_syntax_errors(content):
    content = content.replace("plugin-opts: {host: ,", "plugin-opts: {host: addons.mozilla.org,")
    content = content.replace("sni: ,", "sni: mozilla.org,")
    content = content.replace("servername: ,", "servername: addons.mozilla.org,")
    content = content.replace("flow: ,", "")
    return content

def update_clash_file(file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r") as f:
        content = f.read()
    content = clean_syntax_errors(content)
    lines = content.splitlines()

    # 1. Replace or insert custom proxy lines
    for node in custom_nodes_clash:
        found = False
        target_name = node["name"]
        for i, line in enumerate(lines):
            if f'name: "{target_name}"' in line or f'name: \'{target_name}\'' in line:
                lines[i] = node["yaml"]
                found = True
                break
        if not found:
            for i, line in enumerate(lines):
                if line.strip().startswith("- {name:"):
                    lines.insert(i, node["yaml"])
                    found = True
                    break
            if not found:
                lines.append(node["yaml"])

    # 2. Update proxy group memberships
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if line.strip() == "- SmartHost - SG - 2T vless-ws-tls":
            indent = line[:line.find("-")]
            for node in custom_nodes_clash:
                if "CF" in node["name"]:
                    new_lines.append(indent + "- " + node["name"])
        elif line.strip() == "- SmartHost - SG - 2T xtls-reality":
            indent = line[:line.find("-")]
            new_lines.append(indent + "- SmartHost - SG - 2T xtls-reality (443)")

    # 3. Deduplicate group proxy entries
    seen = set()
    cleaned_group_lines = []
    in_group_proxies = False
    for line in new_lines:
        if line.strip().startswith("proxies:") and not line.strip().startswith("-"):
            in_group_proxies = True
            seen.clear()
            cleaned_group_lines.append(line)
        elif in_group_proxies:
            if line.strip().startswith("- ") and not line.strip().startswith("- {"):
                item = line.strip()
                if item in seen:
                    continue
                seen.add(item)
                cleaned_group_lines.append(line)
            else:
                in_group_proxies = False
                cleaned_group_lines.append(line)
        else:
            cleaned_group_lines.append(line)

    with open(file_path, "w") as f:
        f.write("\n".join(cleaned_group_lines) + "\n")
    print(f"Updated {file_path}")

# Update proxies and clash2
update_clash_file("/etc/sing-box/subscribe/proxies")
update_clash_file("/etc/sing-box/subscribe/clash2")

# 3. Update /etc/sing-box/subscribe/v2rayn (Clean standard Base64 encoding)
v2rayn_file = "/etc/sing-box/subscribe/v2rayn"
v2rayn_all_nodes = [
    # 1. xtls-reality (8881)
    f"vless://{UUID}@{SERVER_IP}:8881?encryption=none&flow=xtls-rprx-vision&security=reality&sni=addons.mozilla.org&fp=chrome&pbk={REALITY_PUB}&type=tcp&headerType=none#SmartHost%20-%20SG%20-%202T%20xtls-reality",
    # 2. xtls-reality (443)
    f"vless://{UUID}@{SERVER_IP}:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=addons.mozilla.org&fp=chrome&pbk={REALITY_PUB}&type=tcp&headerType=none#SmartHost%20-%20SG%20-%202T%20xtls-reality%20(443)",
    # 3. hysteria2 (8882)
    f"hysteria2://{UUID}@{SERVER_IP}:8882?insecure=1&sni=mozilla.org&mport=50000-51000#SmartHost%20-%20SG%20-%202T%20hysteria2",
    # 4. tuic (8883)
    f"tuic://{UUID}:{UUID}@{SERVER_IP}:8883?congestion_control=bbr&alpn=h3&allow_insecure=1&sni=mozilla.org#SmartHost%20-%20SG%20-%202T%20tuic",
    # 5. shadowsocks (8885)
    f"ss://{base64.b64encode(f'aes-128-gcm:{UUID}'.encode()).decode()}@{SERVER_IP}:8885#SmartHost%20-%20SG%20-%202T%20shadowsocks",
    # 6. trojan (8886)
    f"trojan://{UUID}@{SERVER_IP}:8886?security=tls&sni=mozilla.org&allowInsecure=1#SmartHost%20-%20SG%20-%202T%20trojan",
    # 7. grpc-reality (8890)
    f"vless://{UUID}@{SERVER_IP}:8890?encryption=none&security=reality&sni=addons.mozilla.org&fp=chrome&pbk={REALITY_PUB}&type=grpc&serviceName=grpc&mode=gun#SmartHost%20-%20SG%20-%202T%20grpc-reality",
    # 8. vless-ws-tls (接入优选)
    f"vless://{UUID}@{CF_DEFAULT_DOMAIN}:443?encryption=none&security=tls&sni={HOST_DOMAIN}&type=ws&host={HOST_DOMAIN}&path=%2F{UUID}-vless%3Fed%3D2560#SmartHost%20-%20SG%20-%202T%20vless-ws-tls",
    # 9. vless-ws-tls (CF多线全球优选)
    f"vless://{UUID}@{CF_MULTI_DOMAIN}:443?encryption=none&security=tls&sni={HOST_DOMAIN}&type=ws&host={HOST_DOMAIN}&path=%2F{UUID}-vless%3Fed%3D2560#SmartHost%20-%20SG%20-%202T%20vless-ws-tls%20(CF%E5%A4%9A%E7%BA%BF%E5%85%A8%E7%90%83%E4%BC%98%E9%80%89)",
    # 10. vless-ws-tls (CF电信优选)
    f"vless://{UUID}@{CF_TELECOM_IP}:443?encryption=none&security=tls&sni={HOST_DOMAIN}&type=ws&host={HOST_DOMAIN}&path=%2F{UUID}-vless%3Fed%3D2560#SmartHost%20-%20SG%20-%202T%20vless-ws-tls%20(CF%E7%94%B5%E4%BF%A1%E4%BC%98%E9%80%89)",
    # 11. vless-ws-tls (CF联通优选)
    f"vless://{UUID}@{CF_UNICOM_IP}:443?encryption=none&security=tls&sni={HOST_DOMAIN}&type=ws&host={HOST_DOMAIN}&path=%2F{UUID}-vless%3Fed%3D2560#SmartHost%20-%20SG%20-%202T%20vless-ws-tls%20(CF%E8%81%94%E9%80%9A%E4%BC%98%E9%80%89)",
    # 12. vless-ws-tls (CF移动优选)
    f"vless://{UUID}@{CF_MOBILE_IP}:443?encryption=none&security=tls&sni={HOST_DOMAIN}&type=ws&host={HOST_DOMAIN}&path=%2F{UUID}-vless%3Fed%3D2560#SmartHost%20-%20SG%20-%202T%20vless-ws-tls%20(CF%E7%A7%BB%E5%8A%A8%E4%BC%98%E9%80%89)",
    # 13. vless-ws-tls (CF亚太纯净IP)
    f"vless://{UUID}@{CF_CLEAN_IP}:443?encryption=none&security=tls&sni={HOST_DOMAIN}&type=ws&host={HOST_DOMAIN}&path=%2F{UUID}-vless%3Fed%3D2560#SmartHost%20-%20SG%20-%202T%20vless-ws-tls%20(CF%E4%BA%9A%E5%A4%AA%E7%BA%AF%E5%87%80IP)",
    # 14. vmess-ws (接入优选)
    "vmess://" + base64.b64encode(json.dumps({
        "v": "2", "ps": "SmartHost - SG - 2T vmess-ws",
        "add": CF_DEFAULT_DOMAIN, "port": "443", "id": UUID, "aid": "0", "scy": "auto",
        "net": "ws", "type": "none", "host": HOST_DOMAIN, "path": f"/{UUID}-vmess",
        "tls": "tls", "sni": HOST_DOMAIN, "alpn": ""
    }).encode()).decode(),
    # 15. vmess-ws (CF多线全球优选)
    "vmess://" + base64.b64encode(json.dumps({
        "v": "2", "ps": "SmartHost - SG - 2T vmess-ws (CF多线全球优选)",
        "add": CF_MULTI_DOMAIN, "port": "443", "id": UUID, "aid": "0", "scy": "auto",
        "net": "ws", "type": "none", "host": HOST_DOMAIN, "path": f"/{UUID}-vmess",
        "tls": "tls", "sni": HOST_DOMAIN, "alpn": ""
    }).encode()).decode(),
    # 16. vmess-ws (CF电信优选)
    "vmess://" + base64.b64encode(json.dumps({
        "v": "2", "ps": "SmartHost - SG - 2T vmess-ws (CF电信优选)",
        "add": CF_TELECOM_IP, "port": "443", "id": UUID, "aid": "0", "scy": "auto",
        "net": "ws", "type": "none", "host": HOST_DOMAIN, "path": f"/{UUID}-vmess",
        "tls": "tls", "sni": HOST_DOMAIN, "alpn": ""
    }).encode()).decode(),
    # 17. vmess-ws (CF联通优选)
    "vmess://" + base64.b64encode(json.dumps({
        "v": "2", "ps": "SmartHost - SG - 2T vmess-ws (CF联通优选)",
        "add": CF_UNICOM_IP, "port": "443", "id": UUID, "aid": "0", "scy": "auto",
        "net": "ws", "type": "none", "host": HOST_DOMAIN, "path": f"/{UUID}-vmess",
        "tls": "tls", "sni": HOST_DOMAIN, "alpn": ""
    }).encode()).decode(),
    # 18. vmess-ws (CF移动优选)
    "vmess://" + base64.b64encode(json.dumps({
        "v": "2", "ps": "SmartHost - SG - 2T vmess-ws (CF移动优选)",
        "add": CF_MOBILE_IP, "port": "443", "id": UUID, "aid": "0", "scy": "auto",
        "net": "ws", "type": "none", "host": HOST_DOMAIN, "path": f"/{UUID}-vmess",
        "tls": "tls", "sni": HOST_DOMAIN, "alpn": ""
    }).encode()).decode(),
    # 19. vmess-ws (CF亚太纯净IP)
    "vmess://" + base64.b64encode(json.dumps({
        "v": "2", "ps": "SmartHost - SG - 2T vmess-ws (CF亚太纯净IP)",
        "add": CF_CLEAN_IP, "port": "443", "id": UUID, "aid": "0", "scy": "auto",
        "net": "ws", "type": "none", "host": HOST_DOMAIN, "path": f"/{UUID}-vmess",
        "tls": "tls", "sni": HOST_DOMAIN, "alpn": ""
    }).encode()).decode()
]

combined_links = "\n".join(v2rayn_all_nodes) + "\n"
encoded_v2rayn = base64.b64encode(combined_links.encode()).decode()

with open(v2rayn_file, "w") as f:
    f.write(encoded_v2rayn + "\n")
print(f"Updated v2rayn with {len(v2rayn_all_nodes)} nodes (clean Base64 encoded)")
