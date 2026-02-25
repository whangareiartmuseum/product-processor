from http.server import BaseHTTPRequestHandler
import json
import sys
import os
import io
from contextlib import redirect_stdout, redirect_stderr


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            for key in ["SHOPIFY_SHOP_URL", "SHOPIFY_ACCESS_TOKEN", "OPENAI_API_KEY"]:
                val = os.getenv(key)
                if val:
                    os.environ[key] = val

            script_dir = os.path.join(os.path.dirname(__file__), "../../python_scripts")
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)

            import generate_book_categories

            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            result = {}
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    result = generate_book_categories.process_all()
                    success = True
                    error = None
                except Exception as e:
                    success = False
                    error = str(e)
                    result = {"success": False, "error": error}
                    import traceback
                    traceback.print_exc()

            logs = []
            if stdout_capture.getvalue():
                logs.extend([line for line in stdout_capture.getvalue().strip().split("\n") if line])
            if stderr_capture.getvalue():
                logs.extend([f"ERROR: {line}" for line in stderr_capture.getvalue().strip().split("\n") if line])

            response_data = {
                "success": success and result.get("success", True),
                "logs": logs,
                "error": error or result.get("error"),
                "summary": result.get("summary"),
                "data": result.get("data"),
            }

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
