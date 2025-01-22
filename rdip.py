import socket
import csv
import ipaddress

def expand_ip_ranges(ip_ranges):
    expanded_ips = []
    for ip_range in ip_ranges:
        ip_range = ip_range.strip()  # Remove spaces
        if "-" in ip_range:
            start_ip, end_ip = ip_range.split("-")
            start = ipaddress.IPv4Address(start_ip.strip())
            end = ipaddress.IPv4Address(end_ip.strip())
            for ip in range(int(start), int(end) + 1):
                expanded_ips.append(str(ipaddress.IPv4Address(ip)))
        else:
            expanded_ips.append(ip_range)
    return expanded_ips

# File paths
input_file = "input_ips.txt"  # Input file containing IP ranges
output_file = "resolved_ips.csv"  # Output CSV file

# Read IP ranges from the file
with open(input_file, "r") as file:
    ip_ranges = file.read().split(",")  # Split by comma

# Expand IP ranges
expanded_ips = expand_ip_ranges(ip_ranges)

# Resolve IPs to domains and write to CSV
with open(output_file, "w", newline="") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["IP Address", "Resolved Domain"])  # Column headers
    
    for ip in expanded_ips:
        try:
            domain = socket.gethostbyaddr(ip.strip())[0]  # Resolve IP to domain
            csv_writer.writerow([ip, domain])  # Write IP and resolved domain
        except socket.herror:  # Handle resolution errors
            csv_writer.writerow([ip, "Resolution Failed"])  # Write IP and error message

print(f"Resolved IPs and domains have been saved to {output_file}")
