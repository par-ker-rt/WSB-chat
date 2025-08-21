import os
# Chat (non-streaming)
@APP.post('/chat')
@limiter.limit('40/minute')
def chat():
data = request.json or {}
msg = data.get('message','')
system = data.get('system','Bạn là trợ lý WSB. Giúp người dùng viết code, giải thích, vẽ.')
model = data.get('model')
if not msg:
return jsonify({'error':'empty message'}), 400
try:
if PROVIDER == 'ollama':
url = f"{OLLAMA_URL.rstrip('/')}/api/chat"
payload = { 'model': model or OLLAMA_MODEL, 'messages': [{'role':'system','content':system},{'role':'user','content':msg}], 'stream': False }
r = requests.post(url, json=payload, timeout=120)
r.raise_for_status()
j = r.json()
if 'message' in j:
reply = j['message'].get('content','')
elif 'choices' in j:
reply = j['choices'][0]['message']['content']
else:
reply = json.dumps(j)
return jsonify({'reply': reply})


# OpenAI path
m = model or OPENAI_MODEL
headers = { 'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json' }
payload = { 'model': m, 'messages': [{'role':'system','content':system},{'role':'user','content':msg}], 'temperature': 0.3 }
r = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload, timeout=120)
r.raise_for_status()
data = r.json()
reply = data['choices'][0]['message']['content']
return jsonify({'reply': reply})
except Exception as e:
return jsonify({'error': str(e)}), 500


# Chat streaming (proxy OpenAI streaming) via fetch reader
@APP.post('/chat/stream')
@limiter.limit('20/minute')
def chat_stream():
data = request.json or {}
msg = data.get('message','')
system = data.get('system','Bạn là trợ lý WSB.')
model = data.get('model') or OPENAI_MODEL
if PROVIDER != 'openai':
return jsonify({'error':'streaming only supported for OpenAI path in this template'}), 400


headers = { 'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json' }
payload = { 'model': model, 'messages':[{'role':'system','content':system},{'role':'user','content':msg}], 'stream': True }
r = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=payload, stream=True, timeout=300)
def generate():
for line in r.iter_lines(decode_unicode=True):
if not line: continue
if line.startswith('data:'):
data_str = line[len('data:'):].strip()
if data_str == '[DONE]':
yield json.dumps({'done': True})
break
try:
j = json.loads(data_str)
for ch in j.get('choices', []):
delta = ch.get('delta', {})
txt = delta.get('content')
if txt:
yield json.dumps({'delta': txt})
except Exception:
yield json.dumps({'raw': data_str})
return Response(generate(), mimetype='application/json')


@APP.get('/health')
def health():
return {'ok': True}


if __name__ == '__main__':
if not os.path.exists(DB_PATH):
print('Initializing sqlite db...')
import subprocess
subprocess.run(['python', 'init_db.py'])
APP.run(host='0.0.0.0', port=10000)
