import serial.tools.list_ports
from serial import Serial
import time
import struct

class TF350Reader:
    FRAME_SIZE = 9
    FRAME_HEADER = 0x59
    
    def __init__(self, port='COM6', baudrate=115200):
        self.ser = Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        # Clear any leftover data
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
    
    def read_frame(self):
        """Read a complete frame and parse the data"""
        # Clear any stale data
        self.ser.reset_input_buffer()
        
        # Wait for enough data
        while self.ser.in_waiting < self.FRAME_SIZE:
            time.sleep(0.01)
            
        if self.ser.in_waiting >= self.FRAME_SIZE:
            frame = self.ser.read(self.FRAME_SIZE)
            print(f"Raw frame: {' '.join(f'{b:02X}' for b in frame)}")
            
            # Verify frame header (first two bytes should be 0x59)
            if frame[0] != self.FRAME_HEADER or frame[1] != self.FRAME_HEADER:
                print("Invalid frame header")
                return None
            
            # Extract distance (bytes 2-3, LSB first)
            distance = frame[2] | (frame[3] << 8)
            
            # Extract signal strength (bytes 4-5, LSB first)
            strength = frame[4] | (frame[5] << 8)
            
            # Reserved bytes (6-7)
            reserved = frame[6] | (frame[7] << 8)
            
            # Checksum (byte 8)
            received_checksum = frame[8]
            
            # Calculate checksum (sum of first 8 bytes)
            calculated_checksum = sum(frame[:8]) & 0xFF
            
            if calculated_checksum != received_checksum:
                print(f"Checksum mismatch - Calc: {calculated_checksum:02X}, Received: {received_checksum:02X}")
                return None
            
            return {
                'distance': distance,
                'strength': strength,
                'reserved': reserved,
                'checksum': received_checksum
            }
        return None

    def interpret_data(self, data):
        """Interpret the data according to the strength thresholds"""
        if data is None:
            return
        
        print(f"\nDistance: {data['distance']} cm")
        print(f"Signal Strength: {data['strength']}")
        
        # Interpret signal strength according to documentation
        if data['strength'] < 40:
            print("Warning: Signal strength too low, distance may be at maximum value")
        elif 40 <= data['strength'] <= 1200:
            print("Signal strength OK - distance measurement reliable")
        elif data['strength'] > 1500:
            print("High reflectivity object detected")
    
    def run(self):
        """Main loop to continuously read sensor data"""
        try:
            print(f"Reading data from TF350 on {self.ser.port}...")
            while True:
                frame_data = self.read_frame()
                self.interpret_data(frame_data)
                # Shorter delay to be more responsive
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("\nStopping sensor reading...")
        finally:
            self.ser.close()
            print("Serial port closed")

if __name__ == "__main__":
    # You can modify the port and baudrate here if needed
    sensor = TF350Reader(port='COM6', baudrate=115200)
    sensor.run()