#!/usr/bin/env python3
import socket
import ssl
import time
import json
import urllib.request
import os
import re

LOG_FILE = "/var/log/cf_updater.log"
APPLY_SCRIPT = "/etc/sing-box/apply_custom_nodes.py"
HOST_DOMAIN = "sg.729927.xyz"

# Verified rock-solid Anycast IPs and CNAME domains
DEFAULT_POOLS = {
    "CT": ["172.64.146.125", "104.18.35.200", "104.16.253.157", "162.159.255.229"],
    "CU": ["104.18.37.247", "104.16.252.200", "104.18.40.100", "172.64.67.117"],
    "CM": ["104.26.15.26", "104.17.146.49", "104.17.49.230", "198.41.209.40"],
    "CLEAN": ["104.26.6.138", "104.26.14.26", "104.26.15.26", "172.67.73.167"],
    "MULTI": ["cf.090227.xyz", "cloudflare.182682.xyz", "cf.0sm.com"]
}

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass

def verify_cf_ip(ip, timeout=2.0):
    """Sanity check that the IP accepts TLS connection with valid SNI handshake."""
    try:
        s = socket.create_connection((ip, 443), timeout=timeout)
        ctx = ssl.create_default_context()
        ss = ctx.wrap_socket(s, server_hostname=HOST_DOMAIN)
        ss.close()
        return True
    except Exception:
        return False

def fetch_vps789_candidates():
    candidates = {"CT": [], "CU": [], "CM": []}
    try:
        req = urllib.request.Request(
            "https://vps789.com/public/sum/cfIpApi",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://vps789.com/cfip",
                "Accept": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode()).get("data", {})
            for line, latency_key, loss_key in [
                ("CT", "dxLatencyAvg", "dxPkgLostRateAvg"),
                ("CU", "ltLatencyAvg", "ltPkgLostRateAvg"),
                ("CM", "ydLatencyAvg", "ydPkgLostRateAvg")
            ]:
                nodes = data.get(line, [])
                valid_nodes = [n for n in nodes if n.get(loss_key, 100) < 3.0]
                valid_nodes.sort(key=lambda x: (x.get(loss_key, 0) * 30 + x.get(latency_key, 999)))
                for n in valid_nodes:
                    ip = n.get("ip")
                    if ip and ip not in candidates[line]:
                        candidates[line].append(ip)
            log(f"Fetched candidates from vps789: CT={len(candidates['CT'])}, CU={len(candidates['CU'])}, CM={len(candidates['CM'])}")
    except Exception as e:
        log(f"vps789 fetch error: {e}")
    return candidates

def fetch_164746_candidates():
    ips = []
    try:
        req = urllib.request.Request(
            "https://ip.164746.xyz/ipTop.html",
            headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            text = resp.read().decode().strip()
            for part in text.split(","):
                part = part.strip()
                if part and re.match(r"^\d+\.\d+\.\d+\.\d+$", part):
                    ips.append(part)
        log(f"Fetched {len(ips)} candidates from 164746.xyz")
    except Exception as e:
        log(f"164746.xyz fetch error: {e}")
    return ips

def pick_best_ip(candidates, line_name, top_ips_164746):
    pool = []
    # 1. Add line candidates from vps789 (measured from China)
    if line_name in candidates:
        pool.extend(candidates[line_name])
    # 2. Add top general fast IPs
    for ip in top_ips_164746:
        if ip not in pool:
            pool.append(ip)
    # 3. Add default proven pool
    if line_name in DEFAULT_POOLS:
        for ip in DEFAULT_POOLS[line_name]:
            if ip not in pool:
                pool.append(ip)

    # Validate IP responds to TLS SNI on 443
    for ip in pool:
        if verify_cf_ip(ip, timeout=2.0):
            return ip
    # Fallback
    return DEFAULT_POOLS.get(line_name, ["104.26.15.26"])[0]

def update_apply_script(best_ips):
    if not os.path.exists(APPLY_SCRIPT):
        log(f"Error: {APPLY_SCRIPT} not found")
        return False

    with open(APPLY_SCRIPT, "r") as f:
        content = f.read()

    replacements = {
        "CF_UNICOM_IP": best_ips.get("CU", "104.18.37.247"),
        "CF_TELECOM_IP": best_ips.get("CT", "172.64.146.125"),
        "CF_MOBILE_IP": best_ips.get("CM", "104.26.15.26"),
        "CF_CLEAN_IP": best_ips.get("CLEAN", "104.26.6.138")
    }

    for var, new_ip in replacements.items():
        pattern = rf'^{var}\s*=\s*["\'].*?["\']'
        replacement = f'{var} = "{new_ip}"'
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open(APPLY_SCRIPT, "w") as f:
        f.write(content)

    log(f"Updated {APPLY_SCRIPT} with verified IPs: {replacements}")
    return True

def main():
    log("=== CF 优选节点智能刷新任务开始 ===")
    vps789_candidates = fetch_vps789_candidates()
    top_164746 = fetch_164746_candidates()

    best_ips = {}
    for line in ["CT", "CU", "CM", "CLEAN"]:
        ip = pick_best_ip(vps789_candidates, line, top_164746)
        best_ips[line] = ip
        log(f"Line {line:5}: Selected Best IP = {ip}")

    if update_apply_script(best_ips):
        ret = os.system(f"python3 {APPLY_SCRIPT} >> {LOG_FILE} 2>&1")
        log(f"apply_custom_nodes.py executed, exit_code={ret}")
    log("=== CF 优选节点智能刷新任务完成 ===")

if __name__ == "__main__":
    main()
