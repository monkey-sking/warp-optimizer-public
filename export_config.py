import sys
import os
import json
import base64
import urllib.parse

# Known Cloudflare Warp Fallback Ports
PORTS = [2408, 500, 1701, 4500]

def parse_wg_conf(filename):
    """
    Parses a WireGuard .conf file manually because configparser 
    doesn't strictly follow WG format (e.g. spaces around =).
    """
    config = {
        "Interface": {},
        "Peer": {}
    }
    
    current_section = None
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if current_section in config:
                    if key in config[current_section]:
                        # Append with comma if key already exists (e.g. multiple Address lines)
                        config[current_section][key] += ", " + value
                    else:
                        config[current_section][key] = value
                    
    return config

def get_common_params(wg_conf):
    """Extracts common parameters for all generators."""
    interface = wg_conf['Interface']
    peer = wg_conf['Peer']

    private_key = interface.get('PrivateKey')
    # Address might be list
    addresses = interface.get('Address', '').split(',')
    ipv4 = next((a.strip() for a in addresses if '.' in a), "")
    ipv6 = "" # Default disable IPv6
    
    # DNS might be present or default
    raw_dns = interface.get('DNS', '1.1.1.1').split(',')
    # Filter only IPv4 DNS since we disabled IPv6
    dns_list = [d.strip() for d in raw_dns if ':' not in d]
    if not dns_list:
        dns_list = ['1.1.1.1', '1.0.0.1'] # Fallback
    
    dns = ", ".join(dns_list)

    public_key = peer.get('PublicKey')
    endpoint = peer.get('Endpoint', '')
    if endpoint:
        host, _ = endpoint.split(':')
    else:
        host = "162.159.192.1"
        
    allowed_ips = peer.get('AllowedIPs', '0.0.0.0/0,::/0')
    
    # Pre-shared key is sometimes used, though not always in standard warp
    psk = peer.get('PresharedKey')

    return {
        "private_key": private_key,
        "public_key": public_key,
        "host": host,
        "ipv4": ipv4,
        "ipv6": ipv6,
        "dns": dns,
        "psk": psk,
        "mtu": 1120 # Lower MTU to improve stability
    }

def generate_clash_proxies(params):
    content = ["# --- Clash Meta (MiHomomo) Configuration ---", "proxies:"]
    hosts = params.get('endpoints', [params['host']])
    target_ports = [2408] if len(hosts) > 1 else PORTS
    
    for host in hosts:
        for port in target_ports:
            name = f"☁️ WARP-{host}:{port}" if len(hosts) > 1 else f"☁️ WARP-Port-{port}"
            
            entry = f"""  - name: {name}
    type: wireguard
    server: {host}
    port: {port}
    ip: {params['ipv4']}
    private-key: {params['private_key']}
    public-key: {params['public_key']}
    udp: true
    mtu: {params['mtu']}"""
            content.append(entry)
        
    return "\n".join(content)

def generate_loon_proxies(params):
    content = ["# --- Loon Configuration ---", "[Proxy]"]
    
    primary_dns = params['dns'].split(',')[0].strip()
    
    hosts = params.get('endpoints', [params['host']])
    target_ports = [2408] if len(hosts) > 1 else PORTS

    for i, host in enumerate(hosts, 1):
        for port in target_ports:
            # Simple ASCII name to avoid parsing issues
            safe_host = host.replace('.', '_')
            name = f"WARP_{i}_{safe_host}_{port}"
            
            # Official Loon WireGuard format from https://nsloon.app/docs/Node/
            # wireguardNode = wireguard,interface-ip=...,private-key="...",mtu=...,dns=...,keeyalive=...,peers=[{public-key="...",endpoint=IP:PORT,allowed-ips="0.0.0.0/0"}],udp=true
            # Note: Loon uses "keeyalive" (double 'e') based on their docs.
            line = f'{name} = wireguard,interface-ip={params["ipv4"]},private-key="{params["private_key"]}",mtu={params["mtu"]},dns={primary_dns},keeyalive=45,peers=[{{public-key="{params["public_key"]}",allowed-ips="0.0.0.0/0",endpoint={host}:{port}}}],udp=true'
            content.append(line)
    
    return "\n".join(content)

def generate_surge_proxies(params):
    content = ["# --- Surge Configuration ---", "[Proxy]"]
    hosts = params.get('endpoints', [params['host']])
    target_ports = [2408] if len(hosts) > 1 else PORTS
    
    for host in hosts:
        for port in target_ports:
            name = f"☁️ WARP-{host}:{port}" if len(hosts) > 1 else f"☁️ WARP-Port-{port}"
            # Using key-value format (Surge 4/5):
            line = f"{name} = wireguard, section-name={name}-Section"
            content.append(line)
    
    content.append("\n[WireGuard Section]")
    for host in hosts:
        for port in target_ports:
            name = f"☁️ WARP-{host}:{port}" if len(hosts) > 1 else f"☁️ WARP-Port-{port}"
            # Surge WireGuard Section
            section = f"""[{name}-Section]
private-key = {params['private_key']}
peer = (public-key={params['public_key']}, allowed-ips="0.0.0.0/0", endpoint={host}:{port}, keepalive=20)
dns-server = {params['dns']}
mtu = {params['mtu']}
self-ip = {params['ipv4']}
"""
            content.append(section)
        
    return "\n".join(content)

def generate_quanx_proxies(params):
    content = ["# --- Quantumult X Configuration ---", "[server_local]"]
    hosts = params.get('endpoints', [params['host']])
    target_ports = [2408] if len(hosts) > 1 else PORTS
    
    for host in hosts:
        for port in target_ports:
            name = f"☁️ WARP-{host}:{port}" if len(hosts) > 1 else f"☁️ WARP-Port-{port}"
            line = f"wireguard={name}, section-name={name}-Section"
            content.append(line)

    content.append("\n# [wireguard] section (paste this into your QX config)")
    for host in hosts:
        for port in target_ports:
            name = f"☁️ WARP-{host}:{port}" if len(hosts) > 1 else f"☁️ WARP-Port-{port}"
            section = f"""[{name}-Section]
private-key = {params['private_key']}
peer = (public-key={params['public_key']}, allowed-ips="0.0.0.0/0", endpoint={host}:{port}, keepalive=20)
dns-server = {params['dns']}
mtu = {params['mtu']}
self-ip = {params['ipv4']}
"""
            content.append(section)
        
    return "\n".join(content)

def generate_shadowrocket_proxies(params):
    # Shadowrocket supports standard "wireguard://" URIs which is the most portable way to import 'servers'.
    # Format: wireguard://private_key@server:port?public_key=...&...
    content = ["# --- Shadowrocket (URIs) ---", "# Copy the links below and add via 'Import from Clipboard'"]
    hosts = params.get('endpoints', [params['host']])
    target_ports = [2408] if len(hosts) > 1 else PORTS
    
    for host in hosts:
        for port in target_ports:
            name = f"WARP-{host}:{port}" if len(hosts) > 1 else f"WARP-Port-{port}"
            safe_name = urllib.parse.quote(name)
            
            # Construct URI query params
            query_params = {
                "public_key": params['public_key'],
                "address": params['ipv4'],
                "mtu": params['mtu'],
                "clean": "0" # Often used param
            }
            
            base = f"{params['private_key']}@{host}:{port}"
            
            # For valid WG URI, usually params are URI encoded.
            query_string = urllib.parse.urlencode(query_params)
            
            uri = f"wireguard://{base}?{query_string}#{safe_name}"
            content.append(uri)
        
    return "\n".join(content)

def generate_singbox_proxies(params):
    outbounds = []
    hosts = params.get('endpoints', [params['host']])
    target_ports = [2408] if len(hosts) > 1 else PORTS
    
    for host in hosts:
        for port in target_ports:
            name = f"☁️ WARP-{host}:{port}" if len(hosts) > 1 else f"☁️ WARP-Port-{port}"
            outbound = {
                "type": "wireguard",
                "tag": name,
                "server": host,
                "server_port": port,
                "system_interface": False,
                "local_address": [params['ipv4']], # IPv4 only
                "private_key": params['private_key'],
                "peer_public_key": params['public_key'],
                "mtu": params['mtu']
            }
            outbounds.append(outbound)
        
    # Wrapper JSON
    config = {
        "outbounds": outbounds
    }
    
    return json.dumps(config, indent=2)


def main():
    try:
        conf_path = "wgcf-profile.conf"
        if not os.path.exists(conf_path):
             print(f"Error: '{conf_path}' not found. Please run ./optimize.sh first or ensure wgcf-profile.conf exists.")
             sys.exit(1)

        conf = parse_wg_conf(conf_path)
        params = get_common_params(conf)
        
        # Determine endpoints to use
        # If best_endpoints.txt exists, use those. Otherwise fallback to config endpoint.
        endpoints = []
        if os.path.exists("best_endpoints.txt"):
            with open("best_endpoints.txt", "r") as f:
                endpoints = [line.strip() for line in f if line.strip()]
        
        if not endpoints:
             # Fallback to single endpoint from config
             endpoints = [params['host']]
             print("Using single endpoint from config.")
        else:
             print(f"Loaded {len(endpoints)} endpoints from scan.")
        
        # Pass endpoints to params for generators
        params['endpoints'] = endpoints

        # Generators mapping: Function -> Filename
        generators = [
            (generate_clash_proxies, "warp_clash.yaml"),
            (generate_loon_proxies, "warp_loon.conf"),
            (generate_surge_proxies, "warp_surge.conf"),
            (generate_quanx_proxies, "warp_quanx.conf"),
            (generate_shadowrocket_proxies, "warp_shadowrocket.conf"),
            (generate_singbox_proxies, "warp_singbox.json"),
        ]
        
        print(f"Exporting configurations...")
        
        for gen_func, filename in generators:
            content = gen_func(params)
            with open(filename, "w") as f:
                f.write(content)
            print(f"✅ Generated {filename}")
            
    except Exception as e:
        print(f"Error parsing config: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
