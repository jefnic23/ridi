import mido
import threading

class Midi:
    def __init__(self, log_callback):
        self.log_callback = log_callback
        self.inport = None
        self.outport = None
        self.routing_thread = None
        self.stop_thread = False

    def get_input_ports(self):
        return mido.get_input_names()

    def get_output_ports(self):
        return mido.get_output_names()

    def start_routing(self, input_port, output_port):
        self.stop_routing()  # Stop any existing routing
        try:
            self.inport = mido.open_input(input_port)
            self.outport = mido.open_output(output_port)

            self.log_callback(f"Listening on {input_port}, sending to {output_port}...")

            # Start a new thread for MIDI routing
            self.stop_thread = False
            self.routing_thread = threading.Thread(target=self.route_midi, daemon=True)
            self.routing_thread.start()

        except Exception as e:
            self.log_callback(f"Error: {str(e)}")

    def route_midi(self):
        while not self.stop_thread:
            try:
                for message in self.inport.iter_pending():
                    self.log_callback(f"Received: {message}")
                    self.outport.send(message)
            except Exception as e:
                self.log_callback(f"Error: {str(e)}")

    def stop_routing(self):
        self.stop_thread = True
        if self.routing_thread is not None:
            self.routing_thread.join()  # Wait for thread to finish
            self.log_callback("MIDI routing stopped.")
        self.routing_thread = None