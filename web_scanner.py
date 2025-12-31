#!/usr/bin/env python3
"""
RTL-SDR Scanner Web Interface
Web-based interface for the RTL-SDR scanner with real-time spectrum display.
"""

import threading
import time
import json
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
import numpy as np

# Web-based RTL-SDR scanner

class WebControlInterface:
    """Web control interface that connects to a running scanner."""

    def __init__(self, scanner, host='0.0.0.0', port=5000):
        self.scanner = scanner
        self.host = host
        self.port = port

        # Web server components
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")

        self.setup_routes()
        self.setup_socket_events()

    def get_html_template(self):
        """Return the HTML template for the web control interface."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>RTL-SDR Scanner Control</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: #ffffff;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .control-group {
            background-color: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
        }
        .status {
            background-color: #2d2d2d;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }
        button:hover {
            background-color: #45a049;
        }
        input, select {
            padding: 8px;
            margin: 4px 0;
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555;
            border-radius: 4px;
        }
        .frequency-display {
            font-size: 24px;
            font-weight: bold;
            color: #ffeb3b;
            text-align: center;
            margin: 10px 0;
        }
        .arrow-buttons {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RTL-SDR Scanner Control</h1>
            <div class="frequency-display" id="frequency">--- MHz</div>
            <div class="arrow-buttons">
                <button id="freqDown">▼ Freq</button>
                <button id="freqUp">▲ Freq</button>
            </div>
        </div>

        <div class="status" id="status">
            Status: Connecting...
        </div>

        <div class="controls">
            <div class="control-group">
                <h3>Frequency</h3>
                <input type="number" id="freqInput" step="0.001" value="100.000">
                <button id="setFreqBtn">Set Frequency</button>
            </div>

            <div class="control-group">
                <h3>Gain</h3>
                <select id="gainSelect">
                    <option value="auto">Auto</option>
                    <option value="-10">-10 dB</option>
                    <option value="0">0 dB</option>
                    <option value="15">15 dB</option>
                    <option value="35">35 dB</option>
                </select>
            </div>

            <div class="control-group">
                <h3>Mode</h3>
                <select id="modeSelect">
                    <option value="none">None</option>
                    <option value="am">AM</option>
                    <option value="fm">FM</option>
                    <option value="ssb">SSB</option>
                    <option value="cw">CW</option>
                    <option value="dmr">DMR</option>
                </select>
            </div>
        </div>
    </div>

    <script>
        const socket = io();
        const freqInput = document.getElementById('freqInput');
        const setFreqBtn = document.getElementById('setFreqBtn');
        const gainSelect = document.getElementById('gainSelect');
        const modeSelect = document.getElementById('modeSelect');
        const frequencyDisplay = document.getElementById('frequency');
        const statusDiv = document.getElementById('status');

        // Arrow button controls
        document.getElementById('freqUp').addEventListener('click', () => {
            socket.emit('adjust_frequency', {direction: 1});
        });

        document.getElementById('freqDown').addEventListener('click', () => {
            socket.emit('adjust_frequency', {direction: -1});
        });

        // Control event listeners
        setFreqBtn.addEventListener('click', () => {
            const freq = parseFloat(freqInput.value);
            if (!isNaN(freq) && freq >= 1 && freq <= 2000) {
                socket.emit('set_frequency', {frequency: freq});
            }
        });

        gainSelect.addEventListener('change', () => {
            socket.emit('set_gain', {gain: gainSelect.value});
        });

        modeSelect.addEventListener('change', () => {
            socket.emit('set_mode', {mode: modeSelect.value});
        });

        // Socket event handlers
        socket.on('connect', () => {
            statusDiv.textContent = 'Status: Connected to scanner';
        });

        socket.on('disconnect', () => {
            statusDiv.textContent = 'Status: Disconnected';
        });

        socket.on('status', (data) => {
            statusDiv.textContent = 'Status: ' + data.message;
        });

        // Periodic status updates
        setInterval(() => {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.frequency) {
                        frequencyDisplay.textContent = data.frequency.toFixed(6) + ' MHz';
                        freqInput.value = data.frequency.toFixed(3);
                        gainSelect.value = data.gain;
                        modeSelect.value = data.mode;
                    }
                })
                .catch(err => {
                    statusDiv.textContent = 'Status: Connection error';
                });
        }, 1000);
    </script>
</body>
</html>
        """

    def setup_routes(self):
        """Set up Flask routes."""

        @self.app.route('/')
        def index():
            return render_template_string(self.get_html_template())

        @self.app.route('/api/status')
        def get_status():
            if self.scanner:
                current_mode = self.scanner.get_current_mode()
                status = {
                    'frequency': self.scanner.center_freq / 1e6,
                    'mode': current_mode,
                    'gain': self.scanner.gain,
                    'spectrum_width': 'normal',  # Fixed for web
                    'signal_type': self.scanner.signal_types[self.scanner.signal_type_index],
                    'ctcss': self.scanner.detected_ctcss,
                    'dmr_info': self.scanner.dmr_info if current_mode == 'dmr' else None
                }
            else:
                status = {'error': 'Scanner not connected'}
            return json.dumps(status)

    def setup_socket_events(self):
        """Set up SocketIO event handlers."""

        @self.socketio.on('connect')
        def handle_connect():
            self.socketio.emit('status', {'message': 'Connected to scanner control'})

        @self.socketio.on('set_frequency')
        def handle_set_frequency(data):
            if self.scanner:
                try:
                    freq_mhz = float(data.get('frequency', 100))
                    self.scanner.center_freq = freq_mhz * 1e6
                    with self.scanner.sdr_lock:
                        if self.scanner.sdr:
                            self.scanner.sdr.center_freq = self.scanner.center_freq
                    self.scanner.freqs = np.fft.fftshift(np.fft.fftfreq(self.scanner.fft_size, 1/self.scanner.sample_rate)) + self.scanner.center_freq
                    self.socketio.emit('status', {'message': f'Frequency set to {freq_mhz:.3f} MHz'})
                except ValueError:
                    self.socketio.emit('status', {'message': 'Invalid frequency'})

        @self.socketio.on('adjust_frequency')
        def handle_adjust_frequency(data):
            if self.scanner:
                direction = int(data.get('direction', 1))
                self.scanner.adjust_frequency(direction)
                self.socketio.emit('status', {'message': 'Frequency adjusted'})

        @self.socketio.on('set_gain')
        def handle_set_gain(data):
            if self.scanner:
                gain_value = data.get('gain', 'auto')
                self.scanner.gain = gain_value
                with self.scanner.sdr_lock:
                    if self.scanner.sdr:
                        if gain_value == 'auto':
                            self.scanner.sdr.gain = 'auto'
                        else:
                            try:
                                self.scanner.sdr.gain = float(gain_value)
                            except ValueError:
                                pass
                self.socketio.emit('status', {'message': f'Gain set to {gain_value}'})

        @self.socketio.on('set_mode')
        def handle_set_mode(data):
            if self.scanner:
                mode = data.get('mode', 'none')
                if mode in ['none', 'am', 'fm', 'ssb', 'cw']:
                    self.scanner.signal_type_index = 0  # Analog
                    mode_index = ['none', 'am', 'fm', 'ssb', 'cw'].index(mode)
                    self.scanner.mode_index = mode_index
                elif mode == 'dmr':
                    self.scanner.signal_type_index = 1  # Digital
                    self.scanner.mode_index = 1  # DMR
                self.socketio.emit('status', {'message': f'Mode set to {mode.upper()}'})

    def run(self):
        """Run the web control interface."""
        print(f"Starting web control interface on http://{self.host}:{self.port}")
        try:
            self.socketio.run(self.app, host=self.host, port=self.port, debug=False)
        except KeyboardInterrupt:
            print("\nWeb control interface stopped")

class WebRTLScanner:
    def __init__(self, sample_rate=2.4e6, center_freq=100e6, gain='auto'):
        self.sample_rate = sample_rate
        self.center_freq = center_freq
        self.gain = gain

        # Initialize RTL-SDR components directly (not using InteractiveRTLScanner)
        self.sdr = None
        self.sdr_lock = threading.Lock()
        self.is_running = True

        # Spectrum analysis components
        self.fft_size = 1024
        self.window = np.hanning(self.fft_size)
        self.freqs = np.fft.fftfreq(self.fft_size, 1/self.sample_rate)
        self.freqs = np.fft.fftshift(self.freqs) + self.center_freq

        # Signal processing settings
        self.gain = gain
        self.signal_types = ['analog', 'digital']
        self.signal_type_index = 0
        self.analog_modes = ['none', 'am', 'fm', 'ssb', 'cw']
        self.digital_modes = ['none', 'dmr']
        self.mode_index = 0

        # CTCSS and DMR detection
        self.ctcss_tones = [
            67.0, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8,
            97.4, 100.0, 103.5, 107.2, 110.9, 114.8, 118.8, 123.0, 127.3, 131.8,
            136.5, 141.3, 146.2, 151.4, 156.7, 162.2, 167.9, 173.8, 179.9, 186.2,
            192.8, 203.5, 210.7, 218.1, 225.7, 233.6, 241.8, 250.3
        ]
        self.detected_ctcss = None
        self.dmr_info = {'talkgroup': None, 'timeslot': None, 'color_code': None, 'active': False}

        # Web server components
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.running = False
        self.clients = set()

        self.setup_routes()
        self.setup_socket_events()

    def get_current_mode(self):
        """Get the current mode based on signal type."""
        if self.signal_type_index == 0:  # Analog
            return self.analog_modes[self.mode_index]
        else:  # Digital
            return self.digital_modes[self.mode_index]

    def get_current_modes_list(self):
        """Get the modes list for current signal type."""
        if self.signal_type_index == 0:  # Analog
            return self.analog_modes
        else:  # Digital
            return self.digital_modes

    def set_mode_index(self, mode_index):
        """Set mode index within current signal type."""
        modes_list = self.get_current_modes_list()
        if 0 <= mode_index < len(modes_list):
            self.mode_index = mode_index

    def cycle_mode(self, direction):
        """Cycle through modes in current signal type."""
        modes_list = self.get_current_modes_list()
        self.mode_index = (self.mode_index + direction) % len(modes_list)

    def adjust_frequency(self, delta):
        """Adjust the center frequency."""
        self.center_freq += delta * 100000  # 100kHz steps
        # Keep frequency within reasonable bounds (1 MHz to 2 GHz)
        self.center_freq = max(1000000, min(2000000000, self.center_freq))
        with self.sdr_lock:
            if self.sdr is not None:
                try:
                    self.sdr.center_freq = self.center_freq
                except (AttributeError, ValueError):
                    pass

    def initialize_device(self):
        """Initialize the RTL-SDR device."""
        with self.sdr_lock:
            try:
                from rtlsdr import RtlSdr
                self.sdr = RtlSdr()
                if self.sdr is None:
                    raise RuntimeError("Failed to create RTL-SDR instance")

                self.sdr.sample_rate = self.sample_rate
                self.sdr.center_freq = self.center_freq
                if self.gain == 'auto':
                    self.sdr.gain = 'auto'
                else:
                    self.sdr.gain = self.gain

                print("RTL-SDR initialized for web interface")

            except Exception as e:
                print(f"Failed to initialize RTL-SDR: {e}")
                raise

    def setup_routes(self):
        """Set up Flask routes."""

        @self.app.route('/')
        def index():
            return render_template_string(self.get_html_template())

        @self.app.route('/api/status')
        def get_status():
            current_mode = self.get_current_mode()
            status = {
                'frequency': self.center_freq / 1e6,
                'mode': current_mode,
                'gain': self.gain,
                'spectrum_width': 'normal',  # Default for web
                'signal_type': self.signal_types[self.signal_type_index],
                'ctcss': self.detected_ctcss,
                'dmr_info': self.dmr_info if current_mode == 'dmr' else None
            }
            return json.dumps(status)

    def setup_socket_events(self):
        """Set up SocketIO event handlers."""

        @self.socketio.on('connect')
        def handle_connect():
            self.clients.add(request.sid)
            emit('status', {'message': 'Connected to RTL-SDR Scanner'})

        @self.socketio.on('disconnect')
        def handle_disconnect():
            self.clients.discard(request.sid)

        @self.socketio.on('start_scan')
        def handle_start_scan():
            if not self.running:
                self.running = True
                self.initialize_device()
                threading.Thread(target=self._spectrum_broadcast_loop, daemon=True).start()
                emit('status', {'message': 'Scanner started'})

        @self.socketio.on('stop_scan')
        def handle_stop_scan():
            self.running = False
            with self.sdr_lock:
                if self.sdr:
                    try:
                        self.sdr.close()
                    except:
                        pass
            emit('status', {'message': 'Scanner stopped'})

        @self.socketio.on('set_frequency')
        def handle_set_frequency(data):
            try:
                freq_mhz = float(data.get('frequency', 100))
                self.center_freq = freq_mhz * 1e6
                with self.sdr_lock:
                    if self.sdr:
                        self.sdr.center_freq = self.center_freq
                self.freqs = np.fft.fftshift(np.fft.fftfreq(self.fft_size, 1/self.sample_rate)) + self.center_freq
                emit('status', {'message': f'Frequency set to {freq_mhz:.3f} MHz'})
            except ValueError:
                emit('status', {'message': 'Invalid frequency'})

        @self.socketio.on('adjust_frequency')
        def handle_adjust_frequency(data):
            direction = int(data.get('direction', 1))
            self.adjust_frequency(direction)
            emit('status', {'message': f'Frequency adjusted'})

        @self.socketio.on('select_digit')
        def handle_select_digit(data):
            # Web interface doesn't have digit selection like terminal
            emit('status', {'message': 'Digit selection not available in web interface'})

        @self.socketio.on('set_gain')
        def handle_set_gain(data):
            gain_value = data.get('gain', 'auto')
            self.gain = gain_value
            with self.sdr_lock:
                if self.sdr:
                    if gain_value == 'auto':
                        self.sdr.gain = 'auto'
                    else:
                        try:
                            self.sdr.gain = float(gain_value)
                        except ValueError:
                            pass
            emit('status', {'message': f'Gain set to {gain_value}'})

        @self.socketio.on('set_mode')
        def handle_set_mode(data):
            mode = data.get('mode', 'none')
            if mode in ['none', 'am', 'fm', 'ssb', 'cw']:
                self.signal_type_index = 0  # Analog
                mode_index = ['none', 'am', 'fm', 'ssb', 'cw'].index(mode)
                self.mode_index = mode_index
            elif mode == 'dmr':
                self.signal_type_index = 1  # Digital
                self.mode_index = 1  # DMR
            emit('status', {'message': f'Mode set to {mode.upper()}'})

        @self.socketio.on('set_spectrum_width')
        def handle_set_spectrum_width(data):
            # Web interface uses fixed spectrum width
            emit('status', {'message': 'Spectrum width fixed in web interface'})

    def capture_samples(self):
        """Capture samples for spectrum analysis."""
        with self.sdr_lock:
            if self.sdr is None:
                return

            try:
                # Capture samples
                samples = self.sdr.read_samples(self.fft_size)

                # Compute FFT for spectrum display
                windowed_samples = samples * self.window
                fft_result = np.fft.fft(windowed_samples)
                fft_result = np.fft.fftshift(fft_result)
                self.power_spectrum = 20 * np.log10(np.abs(fft_result) + 1e-10)

                # Perform demodulation if enabled
                current_mode = self.get_current_mode()
                if current_mode != 'none':
                    # Add demodulation logic here if needed
                    pass

            except Exception as e:
                print(f"Capture error: {e}")
                # Create dummy spectrum data to prevent crashes
                self.power_spectrum = np.zeros(self.fft_size) - 50

    def _spectrum_broadcast_loop(self):
        """Broadcast spectrum data to all connected clients."""
        while self.is_running:
            try:
                if hasattr(self, 'power_spectrum') and len(self.clients) > 0:
                    self.capture_samples()

                    # Convert spectrum data to list for JSON serialization
                    spectrum_data = {
                        'frequencies': np.linspace(
                            self.center_freq - self.sample_rate/2,
                            self.center_freq + self.sample_rate/2,
                            len(self.power_spectrum)
                        ).tolist(),
                        'powers': self.power_spectrum.tolist(),
                        'center_freq': self.center_freq / 1e6,
                        'sample_rate': self.sample_rate / 1e6
                    }

                    self.socketio.emit('spectrum_data', spectrum_data)

                time.sleep(0.1)  # 10 FPS

            except Exception as e:
                print(f"Spectrum broadcast error: {e}")
                time.sleep(0.5)

    def get_html_template(self):
        """Return the HTML template for the web interface."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>RTL-SDR Scanner</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: #ffffff;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .control-group {
            background-color: #2d2d2d;
            padding: 15px;
            border-radius: 8px;
        }
        .spectrum-container {
            background-color: #2d2d2d;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .status {
            background-color: #2d2d2d;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }
        button:hover {
            background-color: #45a049;
        }
        button:disabled {
            background-color: #666;
            cursor: not-allowed;
        }
        input, select {
            padding: 8px;
            margin: 4px 0;
            background-color: #404040;
            color: #ffffff;
            border: 1px solid #555;
            border-radius: 4px;
        }
        .frequency-display {
            font-size: 24px;
            font-weight: bold;
            color: #ffeb3b;
            text-align: center;
            margin: 10px 0;
        }
        .arrow-buttons {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 10px 0;
        }
        canvas {
            width: 100%;
            height: 300px;
            background-color: #000;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RTL-SDR Scanner</h1>
            <div class="frequency-display" id="frequency">--- MHz</div>
            <div class="arrow-buttons">
                <button id="digitLeft">◀ Digit</button>
                <button id="freqDown">▼ Freq</button>
                <button id="freqUp">▲ Freq</button>
                <button id="digitRight">Digit ▶</button>
            </div>
        </div>

        <div class="status" id="status">
            Status: Disconnected
        </div>

        <div class="controls">
            <div class="control-group">
                <h3>Scanner Control</h3>
                <button id="startBtn">Start Scanner</button>
                <button id="stopBtn" disabled>Stop Scanner</button>
            </div>

            <div class="control-group">
                <h3>Frequency</h3>
                <input type="number" id="freqInput" step="0.001" value="100.000" min="1" max="2000">
                <button id="setFreqBtn">Set Frequency</button>
            </div>

            <div class="control-group">
                <h3>Gain</h3>
                <select id="gainSelect">
                    <option value="auto">Auto</option>
                    <option value="-10">-10 dB</option>
                    <option value="0">0 dB</option>
                    <option value="15">15 dB</option>
                    <option value="35">35 dB</option>
                </select>
            </div>

            <div class="control-group">
                <h3>Mode</h3>
                <select id="modeSelect">
                    <option value="none">None</option>
                    <option value="am">AM</option>
                    <option value="fm">FM</option>
                    <option value="ssb">SSB</option>
                    <option value="cw">CW</option>
                    <option value="dmr">DMR</option>
                </select>
            </div>

            <div class="control-group">
                <h3>Spectrum Width</h3>
                <select id="widthSelect">
                    <option value="narrow">Narrow</option>
                    <option value="normal">Normal</option>
                    <option value="wide">Wide</option>
                    <option value="full">Full</option>
                </select>
            </div>
        </div>

        <div class="spectrum-container">
            <h3>Spectrum</h3>
            <canvas id="spectrumCanvas"></canvas>
        </div>
    </div>

    <script>
        const socket = io();
        const canvas = document.getElementById('spectrumCanvas');
        const ctx = canvas.getContext('2d');
        let spectrumData = null;

        // DOM elements
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const freqInput = document.getElementById('freqInput');
        const setFreqBtn = document.getElementById('setFreqBtn');
        const gainSelect = document.getElementById('gainSelect');
        const modeSelect = document.getElementById('modeSelect');
        const widthSelect = document.getElementById('widthSelect');
        const frequencyDisplay = document.getElementById('frequency');
        const statusDiv = document.getElementById('status');

        // Arrow button controls
        document.getElementById('freqUp').addEventListener('click', () => {
            socket.emit('adjust_frequency', {direction: 1});
        });

        document.getElementById('freqDown').addEventListener('click', () => {
            socket.emit('adjust_frequency', {direction: -1});
        });

        document.getElementById('digitLeft').addEventListener('click', () => {
            socket.emit('select_digit', {direction: -1});
        });

        document.getElementById('digitRight').addEventListener('click', () => {
            socket.emit('select_digit', {direction: 1});
        });

        // Control event listeners
        startBtn.addEventListener('click', () => {
            socket.emit('start_scan');
            startBtn.disabled = true;
            stopBtn.disabled = false;
        });

        stopBtn.addEventListener('click', () => {
            socket.emit('stop_scan');
            startBtn.disabled = false;
            stopBtn.disabled = true;
        });

        setFreqBtn.addEventListener('click', () => {
            const freq = parseFloat(freqInput.value);
            if (!isNaN(freq) && freq >= 1 && freq <= 2000) {
                socket.emit('set_frequency', {frequency: freq});
            }
        });

        gainSelect.addEventListener('change', () => {
            socket.emit('set_gain', {gain: gainSelect.value});
        });

        modeSelect.addEventListener('change', () => {
            socket.emit('set_mode', {mode: modeSelect.value});
        });

        widthSelect.addEventListener('change', () => {
            socket.emit('set_spectrum_width', {width: widthSelect.value});
        });

        // Socket event handlers
        socket.on('connect', () => {
            statusDiv.textContent = 'Status: Connected to scanner';
        });

        socket.on('disconnect', () => {
            statusDiv.textContent = 'Status: Disconnected';
            startBtn.disabled = false;
            stopBtn.disabled = true;
        });

        socket.on('status', (data) => {
            statusDiv.textContent = 'Status: ' + data.message;
        });

        socket.on('spectrum_data', (data) => {
            spectrumData = data;
            drawSpectrum();
            frequencyDisplay.textContent = data.center_freq.toFixed(6) + ' MHz';
        });

        function drawSpectrum() {
            if (!spectrumData) return;

            const width = canvas.width;
            const height = canvas.height;

            // Clear canvas
            ctx.fillStyle = '#000000';
            ctx.fillRect(0, 0, width, height);

            // Draw spectrum
            ctx.strokeStyle = '#00ff00';
            ctx.lineWidth = 2;
            ctx.beginPath();

            const powers = spectrumData.powers;
            const maxPower = Math.max(...powers);
            const minPower = Math.min(...powers);
            const powerRange = maxPower - minPower;

            for (let i = 0; i < powers.length; i++) {
                const x = (i / powers.length) * width;
                const power = powers[i];
                const normalizedPower = powerRange > 0 ? (power - minPower) / powerRange : 0.5;
                const y = height - (normalizedPower * height * 0.8);

                if (i === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }

            ctx.stroke();

            // Draw center frequency line
            const centerX = width / 2;
            ctx.strokeStyle = '#ffff00';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(centerX, 0);
            ctx.lineTo(centerX, height);
            ctx.stroke();
        }

        // Handle canvas resize
        function resizeCanvas() {
            const rect = canvas.getBoundingClientRect();
            canvas.width = rect.width * window.devicePixelRatio;
            canvas.height = rect.height * window.devicePixelRatio;
            ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
            canvas.style.width = rect.width + 'px';
            canvas.style.height = rect.height + 'px';
            drawSpectrum();
        }

        window.addEventListener('resize', resizeCanvas);
        resizeCanvas();

        // Periodic redraw
        setInterval(() => {
            drawSpectrum();
        }, 100);
    </script>
</body>
</html>
        """

    def run(self, host='0.0.0.0', port=5000):
        """Run the web server."""
        print(f"Starting RTL-SDR Scanner Web Interface on http://{host}:{port}")
        print("Press Ctrl+C to stop")
        try:
            self.socketio.run(self.app, host=host, port=port, debug=False)
        except KeyboardInterrupt:
            print("\nWeb server stopped")
        finally:
            with self.sdr_lock:
                if self.sdr:
                    try:
                        self.sdr.close()
                    except:
                        pass