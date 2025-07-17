import keyboard
from pynput.keyboard import Controller, Key
from flask import Flask, request, jsonify
import threading
import socket
import time
from datetime import datetime

# Initialize
app = Flask(__name__)
vk = Controller()

# Get local IP address
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

LOCAL_IP = get_local_ip()
PORT = 5000

# State management
state = {
    'code2': False,
    'code3': False,
    'panic': False,
    'headlights': False,
    'hazards': False,
    'siren_blip': False,
    'horn': False,
    'seatbelt': False,
    'last_update': datetime.now().isoformat()
}

# Key simulation
def press_key(key):
    try:
        key_map = {
            'home': Key.home,
            'alt': Key.alt,
            'alt_l': Key.alt_l,
            'backspace': Key.backspace,
            'q': 'q',
            '9': '9',
            'h': 'h',
            'r': 'r',
            'e': 'e',
        }
        actual_key = key_map.get(key, key)
        vk.press(actual_key)
        time.sleep(0.05)
        vk.release(actual_key)
    except Exception as e:
        print(f"Error pressing key {key}: {e}")

# Command handlers
def handle_command(command):
    print(f"Received command: {command}")  # Debug print
    try:
        if command == 'code2':
            state['code2'] = not state['code2']
            if state['code3']:
                state['code3'] = False
            press_key('y')

        elif command == 'code3':
            state['code3'] = not state['code3']
            if state['code2']:
                state['code2'] = False
            press_key('alt_l')

        elif command == 'panic':
            state['panic'] = not state['panic']
            press_key('9')

        elif command == 'headlights':
            state['headlights'] = not state['headlights']
            press_key('h')

        elif command == 'hazards':
            state['hazards'] = not state['hazards']
            press_key('backspace')

        elif command == 'siren_blip':
            if not state['siren_blip']:
                state['siren_blip'] = True
                press_key('r')
                threading.Timer(0.3, lambda: state.update({'siren_blip': False})).start()

        elif command == 'horn':
            if not state['horn']:
                state['horn'] = True
                press_key('e')
                threading.Timer(0.3, lambda: state.update({'horn': False})).start()

        elif command == 'seatbelt':
            state['seatbelt'] = not state['seatbelt']
            press_key('home')

        state['last_update'] = datetime.now().isoformat()
        return state
    except Exception as e:
        print(f"Error handling command {command}: {e}")
        return state

@app.route('/')
def serve_panel():
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>LEO Lighting Control - {LOCAL_IP}</title>
<style>
:root {{
    --code2: #ff3300;
    --code3: #9900ff;
    --panic: #ff0000;
    --headlights: #cccccc;
    --hazards: #ff9900;
    --siren: #00cc66;
    --horn: #ffcc00;
    --seatbelt: #00ffcc;
    --bg: #111;
    --text: #fff;
}}
body {{
    background: var(--bg);
    color: var(--text);
    font-family: Arial;
    margin: 0;
    padding: 10px;
    user-select: none;
}}
.container {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    width: 100%;
    height: 100vh;
    box-sizing: border-box;
}}
.btn {{
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    font-weight: bold;
    font-size: 18px;
    cursor: pointer;
    padding: 10px;
    border: 2px solid transparent;
    text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    transition: all 0.1s;
}}
.btn:active {{ transform: scale(0.97); }}
.btn.active {{ box-shadow: 0 0 15px currentColor; border-color: white; }}
.code2 {{ background: var(--code2); }}
.code3 {{ background: var(--code3); }}
.panic {{ background: var(--panic); }}
.headlights {{ background: var(--headlights); color: #333; }}
.hazards {{ background: var(--hazards); }}
.siren {{ background: var(--siren); }}
.horn {{ background: var(--horn); color: #333; }}
.seatbelt {{ background: var(--seatbelt); color: #333; }}
.ip-display {{
    position: fixed;
    bottom: 10px;
    right: 10px;
    color: #aaa;
    font-size: 12px;
}}
@media (orientation: landscape) {{
    .container {{ grid-template-columns: repeat(3, 1fr); }}
}}
</style>
</head>
<body>
<div class="container">
    <div id="code2" class="btn code2">CODE 2 (y)</div>
    <div id="code3" class="btn code3">CODE 3 (Left Alt)</div>
    <div id="panic" class="btn panic">PANIC (9)</div>
    <div id="headlights" class="btn headlights">HEADLIGHTS (H)</div>
    <div id="hazards" class="btn hazards">HAZARDS (Backspace)</div>
    <div id="siren_blip" class="btn siren">SIREN BLIP (R)</div>
    <div id="horn" class="btn horn">HORN (E)</div>
    <div id="seatbelt" class="btn seatbelt">SEATBELT (Home)</div>
</div>
<div class="ip-display">Server: {LOCAL_IP}:{PORT}</div>
<script>
const buttonCooldown = {{}};

async function sendCommand(command) {{
    if (buttonCooldown[command]) return;
    buttonCooldown[command] = true;
    setTimeout(() => buttonCooldown[command] = false, 500);

    const btn = document.getElementById(command);
    try {{
        const response = await fetch('/control', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ command }})
        }});
        const data = await response.json();

        // Debug logs for code2 and code3
        if(command === 'code2' || command === 'code3') {{
            console.log(`Button ${{command}} toggled, state:`, data.state[command]);
        }}

        Object.keys(data.state).forEach(key => {{
            const el = document.getElementById(key);
            if(el) {{
                if((key === 'siren_blip' || key === 'horn') && data.state[key]) {{
                    el.classList.add('active');
                    setTimeout(() => el.classList.remove('active'), 300);
                }} else {{
                    if(data.state[key]) {{
                        el.classList.add('active');
                    }} else {{
                        el.classList.remove('active');
                    }}
                }}
            }}
        }});
    }} catch(e) {{
        console.error('Connection error:', e);
    }}
}}

document.querySelectorAll('.btn').forEach(btn => {{
    btn.addEventListener('click', () => sendCommand(btn.id));
}});
</script>
</body>
</html>
"""

@app.route('/control', methods=['POST'])
def control():
    data = request.json
    command = data['command']
    handle_command(command)
    return jsonify({'status': 'success', 'state': state})

@app.route('/status')
def get_status():
    return jsonify({'state': state})

def run_flask():
    app.run(host='0.0.0.0', port=PORT, threaded=True)

if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    print(f"""
LEO Lighting Control System
--------------------------
Local Access: http://localhost:{PORT}
Network Access: http://{LOCAL_IP}:{PORT}

Controls:
  CODE 2 = Q (toggle)
  CODE 3 = Left Alt (toggle)
  PANIC = 9 (toggle)
  HEADLIGHTS = H (toggle)
  HAZARDS = Backspace (toggle)
  SIREN BLIP = R (momentary)
  HORN = E (momentary)
  SEATBELT = Home (toggle)
""")
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
