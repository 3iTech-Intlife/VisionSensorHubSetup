import paho.mqtt.client as mqtt
import json
import subprocess
import re
import time


# Function to create wifi profile
def create_wifi_profile(ssid,password):
    profile_template = f"""
    <WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
      <name>{ssid}</name>
      <SSIDConfig>
        <SSID>
          <name>{ssid}</name>
        </SSID>
      </SSIDConfig>
      <connectionType>ESS</connectionType>
      <connectionMode>auto</connectionMode>
      <MSM>
        <security>
          <authEncryption>
            <authentication>WPA2PSK</authentication>
            <encryption>AES</encryption>
            <useOneX>false</useOneX>
          </authEncryption>
          <sharedKey>
            <keyType>passPhrase</keyType>
            <protected>false</protected>
            <keyMaterial>{password}</keyMaterial>
          </sharedKey>
        </security>
      </MSM>
    </WLANProfile>
    """
    profile_path = f"{ssid}.xml"
    with open(profile_path, "w") as profile_file:
        profile_file.write(profile_template)
    return profile_path

# Function to scan for available Wi-Fi SSIDs (Windows)
def scan_wifi():
    try:
        # Use 'mode=bssid' to get all available networks
        command_output = subprocess.check_output("netsh wlan show networks mode=bssid", shell=True).decode("utf-8")
        ssids = re.findall(r"SSID\s\d+\s*:\s(.*)", command_output)
        return [ssid.strip() for ssid in ssids]  # Remove extra spaces
    except Exception as e:
        raise RuntimeError(f"Could not scan for available Wi-Fi networks: {e}")
    
    
# Function to get the currently connected SSID
def get_connected_ssid():
    try:
        command_output = subprocess.check_output("netsh wlan show networks mode=bssid", shell=True).decode("utf-8")
        for line in command_output.splitlines():
            if "SSID" in line and not line.strip().startswith("BSSID"):
                return line.split(":")[1].strip()
    except Exception:
        raise RuntimeError("Could not retrieve connected SSID. Ensure you're connected to an AP.")

# Function to connect to a Wi-Fi network
def connect_to_wifi(ssid, password):
    try:
        print(f"Creating profile for {ssid}...")
        profile_path = create_wifi_profile(ssid,password)
        
        print(f"Adding profile for {ssid}...")
        subprocess.run(["netsh", "wlan", "add", f"profile", f"filename={profile_path}", "user=all"], shell=True, check=True)
        
        print(f"Attempting to connect to {ssid}...")
        subprocess.run(f'netsh wlan connect name="{ssid}" ssid="{ssid}"', shell=True, check=True)
        time.sleep(5)  # Wait for connection to establish
    except subprocess.CalledProcessError:
        raise RuntimeError(f"Failed to connect to SSID: {ssid}")

# Function to replace placeholders with SSID hex part
def replace_placeholders(payload, ssid):
    match = re.search(r"VisionSensorHub_([0-9A-Fa-f]{6})", ssid)
    if not match:
        raise ValueError("SSID format invalid. Expected format: VisionSensorHub_??????")
    hex_part = match.group(1)
    for key in ["TOPIC_AWS_TO_GW", "TOPIC_GW_TO_AWS", "CLIENT_ID"]:
        payload[key] = payload[key].replace("??????", hex_part)
    return payload

# Function to replace placeholders with SSID hex part
def replace_string( ssid):
    match = re.search(r"VisionSensorHub_([0-9A-Fa-f]{6})", ssid)
    if not match:
        raise ValueError("SSID format invalid. Expected format: VisionSensorHub_??????")
    hex_part = match.group(1)
    return '9C65F9' +  hex_part

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker successfully.")
    else:
        print(f"Failed to connect, return code {rc}")

def on_publish(client, userdata, mid):
    print(f"Message {mid} published successfully.")

def on_message(client, userdata, msg):
    userdata["reply"] = json.loads(msg.payload.decode("utf-8"))

# Step 1: User input for SSID search
search_string = input("Enter part of the SSID you want to connect to: ").strip().lower()

# Step 2: Scan Wi-Fi networks and find matches
available_ssids = scan_wifi()
# Debugging: Print all scanned SSIDs
print("Scanned SSIDs:", available_ssids)
# Find SSIDs that match (case insensitive)
matching_ssids = [ssid for ssid in available_ssids if search_string in ssid.lower()]


if not matching_ssids:
    print(f"No SSIDs found containing '{search_string}'. Exiting.")
    exit()

# Step 3: Let the user choose from the list
print("Available networks matching your input:")
for i, ssid in enumerate(matching_ssids, 1):
    print(f"{i}. {ssid}")

selected_index = int(input("Enter the number of the SSID to connect to: ")) - 1
if selected_index < 0 or selected_index >= len(matching_ssids):
    print("Invalid selection. Exiting.")
    exit()

selected_ssid = matching_ssids[selected_index]
wifi_password = input(f"Enter the password for {selected_ssid}: ")

# Step 4: Connect to the selected SSID
connect_to_wifi(selected_ssid, wifi_password)

# Step 5: MQTT Setup
mqtt_broker = "192.168.109.1"  # Replace with your actual broker IP
mqtt_port = 1883
mqtt_topic = "Broker_to_VisionGW"
reply_topic = "VisionGW_to_Broker"

hub_mac_address = ""
userdata = {"reply": None}
client = mqtt.Client(userdata=userdata)
client.on_connect = on_connect
client.on_publish = on_publish
client.on_message = on_message

# Connect to the broker
client.connect(mqtt_broker, mqtt_port, 60)
client.subscribe(reply_topic)
client.loop_start()

# Step 6: Send ROLETYPE_FN command and wait for response
role_payload = {"EVENT": "ROLETYPE_FN"}
while True:
    result = client.publish(mqtt_topic, json.dumps(role_payload))
    result.wait_for_publish()
    print("ROLETYPE_FN command sent. Waiting for reply...")

    timeout = time.time() + 10  # 10-second timeout
    while time.time() < timeout:
        if userdata["reply"]:
            reply = userdata["reply"]
            if reply.get("Session") == "UnsolRpt" and reply.get("Content", {}).get("ZwCmd") == "ROLETYPE_FN":
                print("Expected reply received:", reply)
                break
    else:
        print("Did not receive expected reply. Retrying...")
        continue
    break

# Step 7: Prepare and send first payload
payload_1 = {
    "EVENT": "SET_AWS_SETTING",
    "ENABLE": "1",
    "ROOT_CA": "rootCA.pem",
    "CLIENT_CRT": "cert.crt",
    "CLIENT_KEY": "private.key",
    "ROOT_CA_URL": "https://intlife-prod-iot-keys.s3.ap-southeast-1.amazonaws.com/rootCA.pem",
    "PRIVATE_KEY_URL": "https://intlife-prod-iot-keys.s3.ap-southeast-1.amazonaws.com/private.key",
    "CERT_URL": "https://intlife-prod-iot-keys.s3.ap-southeast-1.amazonaws.com/cert.crt",
    "HOST_NAME": "a1pj7y4tjylv3h-ats.iot.ap-southeast-1.amazonaws.com",
    "TOPIC_AWS_TO_GW": "intlife/9C65F9??????",
    "TOPIC_GW_TO_AWS": "9C65F9??????",
    "CLIENT_ID": "hub_9C65F9??????",
    "MULTI_CMD": "1"
}

# Replace placeholders
updated_payload_1 = replace_placeholders(payload_1, selected_ssid)
hub_mac_address = replace_string(selected_ssid)

# Publish first payload
result = client.publish(mqtt_topic, json.dumps(updated_payload_1))
result.wait_for_publish()
print("First payload (AWS cert setup) sent successfully.")

# Step 8: Wait before sending next command
time.sleep(3)

all_available_ssids = scan_wifi()
print("Scanned SSIDs:", all_available_ssids)

print("Available networks matching your input:")
for i, ssid in enumerate(all_available_ssids, 1):
    print(f"{i}. {ssid}")

selected_index = int(input("Enter the number of the SSID to connect to: ")) - 1
if selected_index < 0 or selected_index >= len(all_available_ssids):
    print("Invalid selection. Exiting.")
    exit()

selected_ssid_for_hub_to_connect = all_available_ssids[selected_index]
wifi_password_for_selected_ssid = input(f"Enter the password for {selected_ssid_for_hub_to_connect}: ")

# Step 9: Send Wi-Fi settings payload
payload_2 = {
    "EVENT": "WIFI_SETTING",
    "MODE": "sta",
    "SSID": selected_ssid_for_hub_to_connect,
    "ENCRYPTION": "psk2",
    "KEY": wifi_password_for_selected_ssid
}

result = client.publish(mqtt_topic, json.dumps(payload_2))
result.wait_for_publish()
    

print("Second payload (Wi-Fi settings) sent successfully.")

# Step 10: Cleanup and disconnect
client.loop_stop()
client.disconnect()
print("MQTT communication completed.")
print("Done setup for Hub, you may now copy the hub mac address to test the AWS cert setup")
print(hub_mac_address)