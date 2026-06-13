#!/usr/bin/env python3
"""
A simple web-based text editor - runs a local server
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import urllib.parse

PORT = 8080
FILES_DIR = "/home/user/c"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Simple Text Editor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1e1e1e; color: #d4d4d4; }
        .container { display: flex; flex-direction: column; height: 100vh; }
        .toolbar { background: #2d2d30; padding: 10px; border-bottom: 1px solid #454545; display: flex; gap: 10px; align-items: center; }
        button { background: #0e639c; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-size: 14px; }
        button:hover { background: #1177bb; }
        input[type="text"] { background: #3c3c3c; border: 1px solid #555; color: #d4d4d4; padding: 6px 10px; border-radius: 4px; flex: 1; max-width: 400px; }
        .editor-area { flex: 1; display: flex; flex-direction: column; padding: 10px; }
        textarea { flex: 1; background: #1e1e1e; color: #d4d4d4; border: 1px solid #454545; padding: 15px; font-family: 'Consolas', 'Courier New', monospace; font-size: 14px; line-height: 1.5; resize: none; }
        .status-bar { background: #007acc; color: white; padding: 6px 10px; font-size: 12px; }
        .file-list { background: #252526; padding: 10px; border-right: 1px solid #454545; overflow-y: auto; min-width: 200px; }
        .file-item { padding: 6px 10px; cursor: pointer; border-radius: 3px; margin-bottom: 2px; }
        .file-item:hover { background: #2a2d2e; }
        .main-area { display: flex; flex: 1; overflow: hidden; }
    </style>
</head>
<body>
    <div class="container">
        <div class="toolbar">
            <input type="text" id="filename" placeholder="filename.txt" value="untitled.txt">
            <button onclick="saveFile()">💾 Save</button>
            <button onclick="loadFile()">📂 Load</button>
            <button onclick="newFile()">📄 New</button>
        </div>
        <div class="main-area">
            <div class="file-list" id="fileList">
                <strong style="color: #888; display: block; margin-bottom: 10px;">Files</strong>
            </div>
            <div class="editor-area">
                <textarea id="editor" placeholder="Start typing..."></textarea>
            </div>
        </div>
        <div class="status-bar" id="status">Ready</div>
    </div>

    <script>
        const editor = document.getElementById('editor');
        const filenameInput = document.getElementById('filename');
        const status = document.getElementById('status');
        const fileList = document.getElementById('fileList');

        async function saveFile() {
            const filename = filenameInput.value;
            const content = editor.value;

            const response = await fetch('/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({filename, content})
            });

            const result = await response.json();
            status.textContent = result.message;
            loadFileList();
        }

        async function loadFile(filename = null) {
            if (!filename) filename = filenameInput.value;

            const response = await fetch('/load?filename=' + encodeURIComponent(filename));
            const result = await response.json();

            if (result.success) {
                editor.value = result.content;
                filenameInput.value = filename;
                status.textContent = 'Loaded: ' + filename;
            } else {
                status.textContent = result.message;
            }
        }

        function newFile() {
            editor.value = '';
            filenameInput.value = 'untitled.txt';
            status.textContent = 'New file';
        }

        async function loadFileList() {
            const response = await fetch('/list');
            const files = await response.json();

            fileList.innerHTML = '<strong style="color: #888; display: block; margin-bottom: 10px;">Files</strong>';
            files.forEach(file => {
                const item = document.createElement('div');
                item.className = 'file-item';
                item.textContent = file;
                item.onclick = () => loadFile(file);
                fileList.appendChild(item);
            });
        }

        // Load file list on start
        loadFileList();

        // Ctrl+S to save
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                saveFile();
            }
        });
    </script>
</body>
</html>
"""

class EditorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())

        elif self.path.startswith('/load'):
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            filename = params.get('filename', [''])[0]

            filepath = os.path.join(FILES_DIR, filename)
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                response = {'success': True, 'content': content}
            except Exception as e:
                response = {'success': False, 'message': f'Error: {str(e)}'}

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        elif self.path == '/list':
            try:
                files = [f for f in os.listdir(FILES_DIR) if os.path.isfile(os.path.join(FILES_DIR, f))]
                files.sort()
            except:
                files = []

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(files).encode())

    def do_POST(self):
        if self.path == '/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())

            filename = data.get('filename', 'untitled.txt')
            content = data.get('content', '')

            filepath = os.path.join(FILES_DIR, filename)
            try:
                with open(filepath, 'w') as f:
                    f.write(content)
                response = {'success': True, 'message': f'Saved: {filename}'}
            except Exception as e:
                response = {'success': False, 'message': f'Error: {str(e)}'}

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

    def log_message(self, format, *args):
        pass

def main():
    server = HTTPServer(('localhost', PORT), EditorHandler)
    print(f"""
╔═══════════════════════════════════════════╗
║     Simple Web Text Editor Started       ║
╚═══════════════════════════════════════════╝

📝 Open your browser to: http://localhost:{PORT}

Features:
  • Save files with Ctrl+S or 💾 Save button
  • Load existing files from the file list
  • Create new files
  • Edit in a clean, VS Code-style interface

Press Ctrl+C to stop the server
""")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")

if __name__ == "__main__":
    main()
