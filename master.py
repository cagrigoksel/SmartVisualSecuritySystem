import azure.mgmt.compute
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient
import time
from datetime import datetime, timedelta
import os

# Azure configuration
subscription_id = "b903a5ae-4f9d-471b-9f44-23da231efa40"
resource_group = "ResourceGroup1"
vm_name = "MusicStreamVM1"
location = "eastus"  # Change this to your preferred region

# Create Azure clients
credential = DefaultAzureCredential()
compute_client = ComputeManagementClient(credential, subscription_id)
resource_client = ResourceManagementClient(credential, subscription_id)

# Create or update resource group
resource_client.resource_groups.create_or_update(resource_group, {"location": location})

# VM configuration
vm_parameters = {
    "location": location,
    "os_profile": {
        "computer_name": vm_name,
        "admin_username": "azureuser",
        "admin_password": "ComplexPassword123!"  # Change this to a secure password
    },
    "hardware_profile": {
        "vm_size": "Standard_DS1_v2"
    },
    "storage_profile": {
        "image_reference": {
            "publisher": "Canonical",
            "offer": "UbuntuServer",
            "sku": "18.04-LTS",
            "version": "latest"
        },
    },
    "network_profile": {
        "network_interfaces": [{
            "id": "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Network/networkInterfaces/{}".format(
                subscription_id, resource_group, f"{vm_name}-nic"
            ),
        }]
    }
}

# Create the VM
print(f"Creating VM {vm_name}...")
async_vm_creation = compute_client.virtual_machines.begin_create_or_update(
    resource_group,
    vm_name,
    vm_parameters
)
async_vm_creation.wait()

# Get VM public IP
nic_name = f"{vm_name}-nic"
network_client = azure.mgmt.network.NetworkManagementClient(credential, subscription_id)
nic = network_client.network_interfaces.get(resource_group, nic_name)
public_ip_address = network_client.public_ip_addresses.get(
    resource_group,
    nic.ip_configurations[0].public_ip_address.id.split('/')[-1]
).ip_address

print(f"VM created with public IP: {public_ip_address}")

# Install necessary packages and start music streaming
vm_command = f"""
sudo apt-get update
sudo apt-get install -y xvfb firefox python3-pip
export DISPLAY=:99
Xvfb :99 -ac &
pip3 install selenium
cat <<EOT > login_script.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from datetime import datetime, timedelta

options = webdriver.FirefoxOptions()
options.add_argument('-headless')
driver = webdriver.Firefox(options=options)

driver.get('https://play.fizy.com/explore')
time.sleep(5)  # Wait for page to load

# Click login button
login_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Giriş Yap')]"))
)
login_button.click()

# Enter phone number
phone_input = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "phone"))
)
phone_input.send_keys("5317249752")

# Click continue button
continue_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Devam Et')]"))
)
continue_button.click()

try:
    # Wait for 2FA code input field
    code_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "code"))
    )
    
    print("2FA code sent to your phone. Please check your messages.")
    
    # Wait for user to input 2FA code
    code = input("Enter the 2FA code: ")
    
    # Enter 2FA code
    code_input.send_keys(code)
    
    # Click login button
    login_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Giriş Yap')]"))
    )
    login_button.click()
except (TimeoutException, NoSuchElementException):
    print("2FA code not required. Proceeding with login.")

print("Logged in successfully. Starting music playback...")

# Search for 2000's and 2010's hits playlist
search_input = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Ara']"))
)
search_input.send_keys("2000's and 2010's hits")

# Click search button
search_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Ara']"))
)
search_button.click()

# Click on the first playlist result
playlist = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'playlist-item')]"))
)
playlist.click()

# Start playing the playlist
play_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'play-button')]"))
)
play_button.click()

# Mute the audio
mute_button = WebDriverWait(driver, 10).until(
    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'volume-button')]"))
)
mute_button.click()

print("Started playing 2000's and 2010's hits playlist (muted).")

# Set end time to 3 weeks from now
end_time = datetime.now() + timedelta(weeks=3)

# Function to check if music is playing
def is_music_playing():
    try:
        play_pause_button = driver.find_element(By.XPATH, "//button[contains(@class, 'play-pause-button')]")
        return "pause" in play_pause_button.get_attribute("class")
    except:
        return False

# Keep the browser open and music playing for 3 weeks
while datetime.now() < end_time:
    time.sleep(300)  # Sleep for 5 minutes
    if not is_music_playing():
        print("Music stopped. Attempting to restart...")
        try:
            play_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'play-button')]"))
            )
            play_button.click()
            print("Music restarted successfully.")
        except:
            print("Failed to restart music. Refreshing page...")
            driver.refresh()
            time.sleep(5)
            try:
                play_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'play-button')]"))
                )
                play_button.click()
                print("Music restarted after page refresh.")
            except:
                print("Failed to restart music after refresh. Continuing to monitor...")

print("3 weeks have passed. Stopping music playback.")
driver.quit()
EOT

nohup python3 login_script.py > music_stream.log 2>&1 &
"""

print("Installing packages and starting music streaming...")
compute_client.virtual_machines.begin_run_command(
    resource_group,
    vm_name,
    {
        'command_id': 'RunShellScript',
        'script': [vm_command]
    }
)

print("Music streaming setup completed. The VM will continue running for 3 weeks.")
print("The VM will keep running even if you close your laptop.")
print("To stop the VM, use: compute_client.virtual_machines.begin_power_off(resource_group, vm_name)")

# Exit the script, allowing the VM to continue running independently
print("This script will now exit. The VM will continue running in the background.")





