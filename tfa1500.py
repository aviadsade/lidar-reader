import serial.tools.list_ports
from serial import Serial
import time


class TFA1500Reader:
    FRAME_SIZE = 5
    FRAME_HEADER = 0x5C

    def __init__(self, port="COM35", baudrate=460800):
        self.ser = Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1,
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
        """Always return the freshest valid frame available."""
        while True:
            # Flush all accumulated bytes except the last 5
            if self.ser.in_waiting > self.FRAME_SIZE * 2:
                self.ser.read(self.ser.in_waiting - self.FRAME_SIZE)

            byte = self.ser.read(1)
            if not byte:
                continue

            if byte[0] != self.FRAME_HEADER:
                continue  # Skip until frame header is found

            remaining = self.ser.read(self.FRAME_SIZE - 1)
            if len(remaining) != self.FRAME_SIZE - 1:
                continue  # Incomplete frame

            frame = byte + remaining
            distance_bytes = frame[1:4]
            received_checksum = frame[4]
            calculated_checksum = self.calculate_checksum(distance_bytes)

            if calculated_checksum != received_checksum:
                continue  # Skip invalid frame

            distance_cm = self.parse_distance(distance_bytes)
            return {"distance": distance_cm}

    def interpret_data(self, data):
        """Interpret the received data"""
        if data is None:
            return

        if data["distance"] == 0:
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
    sensor = TFA1500Reader(port="COM36", baudrate=460800)
    sensor.run()
