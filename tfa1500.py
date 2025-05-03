import serial.tools.list_ports
from serial import Serial
import time

class TFA1500Reader:
    FRAME_SIZE = 5
    FRAME_HEADER = 0x5C
    
    def __init__(self, port='COM6', baudrate=9600):
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
    
    def calculate_checksum(self, data_bytes):
        """Calculate checksum by taking inverse of sum of data bytes"""
        return (~sum(data_bytes)) & 0xFF  # Mask to keep only last byte
    
    def parse_distance(self, data_bytes):
        """Convert 3 bytes to distance value using little endian format"""
        return data_bytes[0] + (data_bytes[1] << 8) + (data_bytes[2] << 16)
    
    def read_frame(self):
        """Read a complete frame and parse the data"""
        # Clear any stale data
        self.ser.reset_input_buffer()
        
        # Wait for enough data
        while self.ser.in_waiting < self.FRAME_SIZE:
            time.sleep(0.01)
            
        if self.ser.in_waiting >= self.FRAME_SIZE:
            frame = self.ser.read(self.FRAME_SIZE)
            # print(f"Raw frame: {' '.join(f'{b:02X}' for b in frame)}")
            
            # Verify frame header
            if frame[0] != self.FRAME_HEADER:
                print(f"Invalid frame header: {hex(frame[0])}")
                return None
            
            # Extract distance bytes
            distance_bytes = frame[1:4]
            
            # Verify checksum
            calculated_checksum = self.calculate_checksum(distance_bytes)
            received_checksum = frame[4]
            
            if calculated_checksum != received_checksum:
                print(f"Checksum mismatch - Calc: {hex(calculated_checksum)}, Received: {hex(received_checksum)}")
                return None
            
            # Calculate distance
            distance_cm = self.parse_distance(distance_bytes)
            return {'distance': distance_cm}
            
        return None

    def interpret_data(self, data):
        """Interpret the received data"""
        if data is None:
            return
            
        if data['distance'] == 0:
            print("No object detected or out of range")
        else:
            print(f"Distance: {data['distance']} cm")
    
    def run(self):
        """Main loop to continuously read sensor data"""
        try:
            print(f"Reading data from TFA1500 on {self.ser.port}...")
            while True:
                frame_data = self.read_frame()
                self.interpret_data(frame_data)
                time.sleep(0.05)  # Small delay to prevent CPU overuse
                
        except KeyboardInterrupt:
            print("\nStopping sensor reading...")
        finally:
            self.ser.close()
            print("Serial port closed")

if __name__ == "__main__":
    sensor = TFA1500Reader(port='COM8', baudrate=460800)
    sensor.run()