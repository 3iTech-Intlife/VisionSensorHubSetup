# Vision Sensor Hub Setup

## Version 0.1

This script automates the process of connecting to a Vision Sensor Hub Wi-Fi network, configuring MQTT communication, and sending necessary payloads to set up AWS certificates and Wi-Fi settings.

## Features

- Scans for available Wi-Fi SSIDs.
- Allows the user to search and select an SSID.
- Connects to the selected SSID using a provided password.
- Establishes an MQTT connection and sends configuration payloads.
- Configures AWS certificates for the Vision Sensor Hub.
- Sets up Wi-Fi settings for the Hub to connect to another network.

## Requirements

- Python 3.x
- Windows OS (uses `netsh` commands for Wi-Fi management)
- Required Python libraries:
  - `paho-mqtt`
  - `json`
  - `subprocess`
  - `re`
  - `time`

## Installation

1. Clone the repository or download the script.
2. Install required dependencies:
   ```sh
   pip install paho-mqtt
   ```
3. Ensure your system supports `netsh` commands for Wi-Fi management.

## Usage

1. Run the script:
   ```sh
   python script.py
   ```
2. Enter a part of the SSID you want to connect to when prompted.
3. Select the desired SSID from the available networks.
4. Provide the Wi-Fi password for the selected SSID.
5. The script will connect to the selected network and establish an MQTT connection.
6. AWS certificate setup payload will be sent.
7. You will be prompted to select another SSID for the Vision Sensor Hub to connect to.
8. Enter the Wi-Fi password for the new SSID.
9. The script will send the Wi-Fi configuration payload to the Hub.

## MQTT Configuration

- **Broker Address:** `192.168.109.1`
- **Port:** `1883`
- **Topics:**
  - `Broker_to_VisionGW` (Sending messages to the Hub)
  - `VisionGW_to_Broker` (Receiving responses from the Hub)

## Payload Details

1. **AWS Certificate Setup Payload:**
   ```json
   {
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
   ```
2. **Wi-Fi Settings Payload:**
   ```json
   {
     "EVENT": "WIFI_SETTING",
     "MODE": "sta",
     "SSID": "<New_SSID>",
     "ENCRYPTION": "psk2",
     "KEY": "<Wi-Fi_Password>"
   }
   ```

## Expected Output

- Successful Wi-Fi connection messages.
- MQTT messages being published and acknowledged.
- The hub's MAC address printed at the end for AWS certificate verification.

## Notes

- Ensure the correct Wi-Fi credentials are entered.
- The script relies on `netsh` commands, which may require administrative privileges.
- MQTT broker should be reachable within the network.

## Troubleshooting

- **No SSIDs found:** Ensure your Wi-Fi adapter is enabled and scanning properly.
- **Failed to connect to SSID:** Double-check the Wi-Fi password.
- **MQTT messages not being sent:** Verify broker IP and network connectivity.

## License

MIT License
