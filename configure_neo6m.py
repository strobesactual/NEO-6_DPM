# There is an issue with the hex code to save whereby it shuts off the receiver so that you dont see a blue light.
# Dont use the save function (3)

import serial
import struct
import binascii
import time
from datetime import datetime 
import sys


(RED, ORANGE, YELLOW, GREEN, CYAN, BLUE, MAGENTA, RESET) = ('\033[91m', '\033[38;5;208m', '\033[93m', '\033[92m', '\033[96m', '\033[94m', '\033[95m', '\033[0m')


port = '/dev/ttyAMA0'  # Adjust as necessary
ser = serial.Serial(port, 9600, 8, timeout=1)  

num_iterations = 100     # Change this to the desired number of testing iterations
ck_a, ck_b = 0, 0
# Define the header, ID, and length
ubx_header = [0xB5, 0x62]       # Ublox sync characters
ubx_ack_ack = [0x05, 0x01]      # Message Acknowledged      (page 91)
ubx_ack_nak = [0x05, 0x00]      # Message Not-Acknowledged  (page 91)
ubx_cfg_cfg_id = [0x06, 0x09]   # CFG-CFG ID    (page 106)
ubx_cfg_nav5_id = [0x06, 0x24]  # CFG-NAV5 ID   (page 118)
ubx_cfg_rst_id = [0x06, 0x04]   # CFG-RST ID    (page 140)


print('\n',f"{CYAN}{'Configuring NEO-6M GPS module...'}{RESET}",'\n')


def send_message(message):
    try:
        ser.write(message)
        ser.flush()
        response = ser.read(100)  # Adjust buffer size as needed
        return response
    except Exception as e:
        print(f"Error sending message: {e}")
        return None
    
    
def parse_response(response):
    if response[0:4] == bytes([0xB5, 0x62, 0x06, 0x24]):  # CFG-NAV5 response
        payload = response[6:-2]  # Remove header and checksum
        dyn_model = payload[2]  # Dynamic model is at offset 2
        return (dyn_model, None)  # Return dynamic model with no ACK/NAK info
    elif response[0:4] == bytes([0xB5, 0x62, 0x05, 0x01]):  # ACK-ACK response
        return (None, True)  # Indicate ACK
    elif response[0:4] == bytes([0xB5, 0x62, 0x05, 0x00]):  # ACK-NAK response
        return (None, False)  # Indicate NAK
    else:
        return (None, None)  # Unknown response
   

def calculate_checksum(message):
    ck_a, ck_b = 0, 0
    for byte in message[2:]:
        ck_a = (ck_a + byte) & 0xFF
        ck_b = (ck_b + ck_a) & 0xFF
    return ck_a, ck_b


def poll_gps(): # 1
    global dyn_model
    ubx_cfg_nav5_length_poll = [0x00, 0x00] # 0 bytes in poll payload
    poll_msg = ubx_header + ubx_cfg_nav5_id + ubx_cfg_nav5_length_poll
    ck_a, ck_b = calculate_checksum(poll_msg)
    poll_msg.extend([ck_a, ck_b])     
    poll_msg_bytes = bytearray(poll_msg)
    
    print(f"{'Sending CFG-NAV5 query:':<35}{poll_msg_bytes.hex()}")
    query_count = 0
    
    while query_count < num_iterations:
        query_count += 1
        response = send_message(poll_msg_bytes)
        if response:
            dyn_model, _ = parse_response(response)
            if dyn_model is not None:
                print(f"{'Received response:':<20} {response.hex()}")
                print(f"{'Dynamic Model:':<20}{MAGENTA}{dyn_model}{RESET}")
                print(f"{'Query count:':<20}{query_count}\n")
                return  # Exit the function after finding the dynamic model
        else:
            print("---No response received---")
        
        time.sleep(.1)  # Wait for 0.1 seconds before the next query
        if query_count >= num_iterations:
            print(f"{RED}{'Max queries reached without receiving acknowledgment.'}{RESET}",'\n')
            break  # Exit the loop if max queries are reached1
        


def set_gps(): # 2  (page 119)
    global dpm
    ubx_cfg_nav5_length_set = [0x24, 0x00]      # 36 bytes in get/set payload
    ubx_cfg_nav5_payload_set = [                # Payload configuration
        0xFF, 0xFF,                 # Mask (all on = apply all settings that follow)
        0x07,                       # ~~~~~~~~~~ Dynamic platform model: "Airborne <2g" = 7 [0x07] ~~~~~ (page 119)
        0x03,                       # Position Fixing Mode: 3 (Auto 2D/3D)
        0x00, 0x00, 0x00, 0x00,     # Fixed altitude for 2D Mode
        0x10, 0x27, 0x00, 0x00,     # Fixed altitude variance for 2D Mode (This could probably be all zero?)
        0x05,                       # Min elevation for a satellite to be used
        0x00,                       # Max time to perform an extrapolation if GPS signal lost
        0xFA, 0x00,                 # Position DOP Mask to use
        0xFA, 0x00,                 # Time DOP Mask
        0x64, 0x00,                 # Position Accuracy Mask
        0x2C, 0x01,                 # Time Accuracy Mask
        0x1A,                       # Static Hold Threshold
        0x00,                       # DGPS timeout
        0x00, 0x00, 0x00, 0x00,     # Always zero
        0x00, 0x00, 0x00, 0x00,     # Always zero
        0x00, 0x00, 0x00, 0x00,     # Always zero
    ]
    set_msg = ubx_header + ubx_cfg_nav5_id + ubx_cfg_nav5_length_set + ubx_cfg_nav5_payload_set
    ck_a, ck_b = calculate_checksum(set_msg)
    set_msg.extend([ck_a, ck_b]) 
    set_msg_bytes = bytearray(set_msg)
    
    print(f"{'Sending CFG-NAV5 Set message:':<35}{set_msg_bytes.hex()}")
    query_count = 0

    while query_count < num_iterations:
        query_count += 1
        response = send_message(set_msg_bytes)
        if response:
            ack = parse_response(response)
            if ack is not None:
                if ack:
                    print(f"{'Configuration status:':<35}{GREEN}{'Message acknowledged.'}{RESET}")
                    print(f"{'Query count:':<35}{query_count}\n")
                    return  # Exit the function after receiving acknowledgment
                else:
                    print(f"{'Configuration status:':<35}{RED}{'Message NOT acknowledged.':<35}{RESET}")
        else:
            print("---No response received---")
        
        time.sleep(0.1)  # Wait for 0.1 seconds before the next query
        if query_count >= num_iterations:
            print(f"{RED}{'Max queries reached without receiving acknowledgment.'}{RESET}",'\n')
            break  # Exit the loop if max queries are reached
     

def save_gps(): # 3
    ubx_cfg_cfg_length_save = [0x0D, 0x00] # 0 bytes in store payload
    ubx_cfg_cfg_payload_save = [0x00, 0x00, 0x00, 0x00,   # This is the clear mask--should be all 0
                                0xFF, 0xFF, 0x06, 0x24,   # Save mask (should have appropriate numbers)
                                0x00, 0x00, 0x00, 0x00]   # Load mask (should be all 0)
    save_msg = ubx_header + ubx_cfg_cfg_id + ubx_cfg_cfg_length_save + ubx_cfg_cfg_payload_save
    ck_a, ck_b = calculate_checksum(save_msg)
    save_msg.extend([ck_a, ck_b]) 
    save_msg_bytes = bytearray(save_msg)
    
    print(f"{'Sending CFG-CFG Save message:':<35}{save_msg_bytes.hex()}")
    query_count = 0  
    
    while query_count < num_iterations:
        query_count += 1
        response = send_message(save_msg_bytes)
        if response:
            ack = parse_response(response)
            if ack is not None:
                if ack:
                    print(f"{'Configuration status:':<35}{GREEN}{'Configuration saved to non-volatile memory.'}{RESET}")
                    print(f"{'Query count:':<35}{query_count}\n")
                    return  # Exit the function after receiving acknowledgment
                else:
                    print(f"{'Configuration status:':<35}{RED}{'Message NOT acknowledged.':<35}{RESET}")
        else:
            print("---No response received---")
        
        time.sleep(0.1)  # Wait for 0.1 seconds before the next query
        if query_count >= num_iterations:
            print(f"{RED}{'Max queries reached without receiving acknowledgment.'}{RESET}",'\n')
            break  # Exit the loop if max queries are reached
    

def reset_gps(): # 4
    ubx_cfg_rst_length = [0x04, 0x00]               # Length of payload
    ubx_cfg_rst_payload = [0x00, 0x00, 0x00, 0x00]  # See page 140 of 210
    reset_msg = ubx_header + ubx_cfg_rst_id + ubx_cfg_rst_length + ubx_cfg_rst_payload 
    ck_a, ck_b = calculate_checksum(reset_msg)
    reset_msg.extend([ck_a, ck_b])
    reset_msg_bytes = bytearray(reset_msg)
    
    print(f"{'Sending reset command:':<35}{reset_msg_bytes.hex()}")
    query_count = 0  
    
    while query_count < num_iterations:
        query_count += 1
        response = send_message(reset_msg_bytes)
        if response:
            dyn_model, ack = parse_response(response)
            if ack is not None:
                if ack:
                    print(f"{'Received response:':<35} {response.hex()}")
                    print(f"{'Dynamic Platform Model:':<35}{GREEN}{'Reset to Portable (0).'}{RESET}")
                    print(f"{'Query count:':<35}{query_count}\n")
                    return  # Exit the function after receiving acknowledgment
                else:
                    print(f"{RED}{'Message NOT acknowledged.':<35}{RESET}")
            else:
                print(f"{RED}{'Unknown response format.'}{RESET}")
                break
        else:
            print("---No response received---")
        
        time.sleep(0.1)  # Wait for 0.1 seconds before the next query
        if query_count >= num_iterations:
            print(f"{RED}{'Max queries reached without receiving acknowledgment.'}{RESET}",'\n')
            break  # Exit the loop if max queries are reached


def read_gps(): # 5
    testing = True
    start_time = time.time()
    while testing:
        line = ser.readline().decode('ascii', errors='ignore').strip()  # Use `ser` instead of `port`
        print(line)
        if time.time() - start_time >= 5:
            testing = False


def exit_configuration(): # 6
    timestamp = datetime.now().strftime("%H:%M:%S")
    print('\n', MAGENTA, "Exiting testing", RESET, timestamp, '\n')
    sys.exit()


# ************************** Function map **************************
functions = {
    '1': poll_gps,
    '2': set_gps,
    '3': save_gps,
    '4': reset_gps,
    '5': read_gps,
    '6': exit_configuration
}


def main():
    try:
        for _ in range(num_iterations):
            print("---------------------------------------------------------------------------------------------")
            print(YELLOW, "Dynamic Platform Model (DPM) should be Airborne <2G (7)", RESET,'\n')
            print("Choose a function to perform:")
            print("1. Query current DPM           3. Save DPM to memory                5. Read serial port (5s) ")
            print("2. Set Airborne <2G mode (7)   4. Reset GPS to Portable mode (0)    6. Exit setup            ")
            print()
            choice = input("Selection: ")
            if choice in functions:
                print()
                functions[choice]()
            else:
                print("Invalid choice. Please enter a number from 1 to 8.")
    except KeyboardInterrupt:
        print('\n', CYAN, "User terminated program.",RESET, '\n')


if __name__ == "__main__":
    main()

