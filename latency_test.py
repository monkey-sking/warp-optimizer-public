import subprocess
import re
import sys
import platform
from concurrent.futures import ThreadPoolExecutor

# Cloudflare WARP Endpoint Ranges
# We will scan a range of IPs from these subnets to find the most stable one
SUBNETS = [
    "162.159.192",
    "162.159.193",
    "162.159.195",
    "188.114.96",
    "188.114.97",
    "188.114.98",
    "188.114.99"
]

def generate_ip_list():
    ips = []
    for subnet in SUBNETS:
        # Scan .1 to .10 for each subnet (high probability of stable endpoints)
        for i in range(1, 11):
            ips.append(f"{subnet}.{i}")
    return ips

IP_LIST = generate_ip_list()

def ping_ip(ip):
    """
    Pings an IP 3 times.
    Returns: (ip, packet_loss_percent, average_latency_ms)
    """
    try:
        # Determine strict timeout flags based on OS if needed, 
        # but -W is generally reliable on macOS/Linux for per-packet or total.
        # macOS: -W waittime (in ms). Linux: -W timeout (in sec).
        # We assume macOS environment based on user metadata.
        
        # -c 3: Send 3 packets
        # -W 500: Wait 500ms max per packet
        # -i 0.2: Interval 0.2s (might require root, so we skip -i to be safe, or use default 1s)
        # Using default interval to avoid permission issues.
        
        args = ["ping", "-c", "3", "-W", "500", ip]
        
        # Adjust for Linux if needed (user is on mac, but good to likely work)
        if platform.system() == "Linux":
             args = ["ping", "-c", "3", "-W", "2", ip] # Linux uses seconds for -W

        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        loss = 100.0
        latency = 9999.0

        # Parse Packet Loss
        # Output example: "3 packets transmitted, 3 packets received, 0.0% packet loss"
        loss_match = re.search(r"([\d.]+)%\s+packet\s+loss", result.stdout)
        if loss_match:
            loss = float(loss_match.group(1))

        # Parse Latency (avg)
        # MacOS: round-trip min/avg/max/stddev = 13.911/14.970/16.142/0.916 ms
        # Linux: rtt min/avg/max/mdev = ...
        lat_match = re.search(r"(?:round-trip|rtt)\s+min/avg/max/(?:stddev|mdev)\s*=\s*[\d.]+/([\d.]+)/", result.stdout)
        if lat_match:
            latency = float(lat_match.group(1))
        
        return ip, loss, latency

    except Exception as e:
        return ip, 100.0, 9999.0

def main():
    print(f"Scanning {len(IP_LIST)} endpoints with 3-packet integrity check...")
    print(f"{'Endpoint':<16} | {'Loss':<6} | {'Avg Latency':<10}")
    print("-" * 38)
    
    valid_endpoints = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(ping_ip, IP_LIST)
        
    for ip, loss, latency in results:
        # Criteria: 0% packet loss and reasonable latency (<300ms)
        if loss == 0.0 and latency < 300:
            print(f"{ip:<16} | {loss:<5}% | {latency:.2f} ms")
            valid_endpoints.append((ip, latency))
    
    # Sort by latency (lowest first)
    valid_endpoints.sort(key=lambda x: x[1])

    if valid_endpoints:
        # Get Top 5 (or fewer if less than 5 found)
        top_endpoints = valid_endpoints[:5]
        
        print("\nTop 5 Stable Endpoints:")
        with open("best_endpoints.txt", "w") as f:
            for i, (ip, lat) in enumerate(top_endpoints, 1):
                print(f"{i}. {ip} ({lat:.2f} ms)")
                f.write(f"{ip}\n")
                
        # For backward compatibility or single-choice logic in scripts (if any remain)
        # we can still output the best one to the single file or just use the first line of the new file.
        # But optimize.sh currently reads 'best_endpoint.txt'. We should update optimize.sh later.
        # Let's write the BEST one to the old file index for safety until updated? 
        # Actually, let's just stick to the new file and update optimize.sh to read it.
        
        # Write best one to best_endpoint.txt for legacy compatibility (optimize.sh uses it to update profile)
        with open("best_endpoint.txt", "w") as f:
             f.write(f"{top_endpoints[0][0]}:2408")
    else:
        print("\nNo stable endpoints found (0% packet loss criteria).")
        # Fallback? Maybe allow small loss? 
        # For now, strict failure is better than bad connection.
        sys.exit(1)

if __name__ == "__main__":
    main()
