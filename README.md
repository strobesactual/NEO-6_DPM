# NEO-6_DPM
Python script to change the Dynamic Platform Model of the NEO-6M GPS chip

I wrote this script to enable my GY-NEO GPS chipset to operate above 12km by switching the DPM to "Airborne <2G". 

**BACKGROUND:**

**Chipset**:          	GY-NEO6MV2  https://a.co/d/g0h8dTs  

**u-blox 6 Manual**:  	chrome-extension://efaidnbmnnnibpcajpcglclefindmkaj/https://content.u-blox.com/sites/default/files/products/documents/u-blox6_ReceiverDescrProtSpec_%28GPS.G6-SW-10018%29_Public.pdf
**Computer**:		RaspberryPi Zero and 4B

**Connections**:
- VCC to Pin 1
- RX to Pin 8   (UART TX)
- TX to Pin 10	(UART RX)
- GND to Pin 9

**NOTES:**
1) I am fairly new to coding, and Python is the only language I know
2) This code has the following issues:
   - Messages from the chip arent necessarily received immediately. For example, you could query the receiver and not necessarily get a response back
   - The DPM change message does work, but wont stay if you cycle power
   - The DPM save message does not work and sometimes prevents the GPS from getting a lock
   - The ACK/NAK message is not being read
   - The reset isnt working immediately
3) If you are able to help with this code, I would greatly appreciate it. My goal is to make it widely available to use for other people who have the same challenge I did
