import argparse

from .server import serve

ap = argparse.ArgumentParser(prog='python -m playmaker_web')
ap.add_argument('--port', type=int, default=8765)
ap.add_argument('--host', default='0.0.0.0', help='0.0.0.0 to accept other machines (or a tunnel)')
a = ap.parse_args()
httpd = serve(a.port, a.host)
print(f'Playmaker playtest server on http://localhost:{a.port}  (Ctrl+C to stop; logs in playtest_logs/)')
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
