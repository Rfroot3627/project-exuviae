import requests
node_id = r'''cam-test-01'''
snapshot_id = r'''s-20260207-223034-a8f71669'''
jpeg = b'\xff\xd8' + b'\x00'*10 + b'\xff\xd9'
r = requests.post(
  'http://127.0.0.1:8000/api/v0/snapshots/upload',
  data={'node_id': node_id, 'snapshot_id': snapshot_id},
  files={'image': ('t.jpg', jpeg, 'image/jpeg')},
  timeout=10
)
print(r.status_code)
print(r.text)
