"""Local existing demo identities, rejection paths only, no GPU or DB writes.

Do not run the destructive database seed. The credentials below are the existing
documented seed fixtures. Cookies stay in memory and are never printed/saved.
"""
from http.cookiejar import CookieJar
from io import BytesIO
import json
from pathlib import Path
from urllib.request import build_opener, HTTPCookieProcessor, Request
from urllib.error import HTTPError
from PIL import Image

ORIGIN = 'http://127.0.0.1:3000'
records = {}


def call(opener, path, data=None, content_type=None, origin='http://localhost:3000'):
    headers = {'Origin': origin}
    if content_type:
        headers['Content-Type'] = content_type
    try:
        response = opener.open(Request(ORIGIN + path, data=data, headers=headers), timeout=20)
    except HTTPError as error:
        response = error
    with response:
        return response.status, json.load(response)


def login(opener, email, password):
    return call(opener, '/api/auth/login', json.dumps({'email': email, 'password': password}).encode(), 'application/json')


def multipart(image, style):
    boundary = 'mobile-acceptance-rejection-only'
    data = (f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="test.png"\r\n'
            'Content-Type: image/png\r\n\r\n').encode() + image
    data += (f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="style_id"\r\n\r\n{style}\r\n--{boundary}--\r\n').encode()
    return data, f'multipart/form-data; boundary={boundary}'


anonymous = build_opener(HTTPCookieProcessor(CookieJar()))
records['anonymous_ai'] = call(anonymous, '/api/ai/features')[0]
assert records['anonymous_ai'] == 401
records['invalid_login'] = login(anonymous, 'maria@email.com', 'intentional-invalid-password')[0]
assert records['invalid_login'] == 401

client = build_opener(HTTPCookieProcessor(CookieJar()))
status, body = login(client, 'maria@email.com', 'client123')
assert status == 200 and body['user']['role'] == 'client'
records['client_login'] = status
assert call(client, '/api/auth/session')[1]['user']['role'] == 'client'
records['client_catalogs'] = {}
for feature in ('hairstyle', 'makeup', 'nails'):
    records['client_catalogs'][feature] = call(client, f'/api/ai/features/{feature}/styles')[0]
assert all(status == 200 for status in records['client_catalogs'].values())

invalid_image = multipart(b'not an image', 'crew_cut')
records['invalid_image'] = call(client, '/api/ai/features/hairstyle/generate', *invalid_image)[0]
assert records['invalid_image'] in (400, 415, 422)
png = BytesIO()
Image.new('RGB', (64, 64), 'white').save(png, format='PNG')
invalid_style = multipart(png.getvalue(), 'nonexistent_acceptance_style')
records['invalid_style'] = call(client, '/api/ai/features/hairstyle/generate', *invalid_style)[0]
assert records['invalid_style'] == 400
records['wrong_origin'] = call(client, '/api/ai/features/hairstyle/generate', *invalid_style, origin='https://different.example.test')[0]
assert records['wrong_origin'] == 403

nonclient = build_opener(HTTPCookieProcessor(CookieJar()))
status, body = login(nonclient, 'lara@andreas.com', 'stylist123')
assert status == 200 and body['user']['role'] == 'stylist'
records['nonclient_ai'] = call(nonclient, '/api/ai/features')[0]
assert records['nonclient_ai'] == 403
call(nonclient, '/api/auth/logout', b'')
records['logout'] = call(client, '/api/auth/logout', b'')[0]
assert records['logout'] == 200 and call(client, '/api/auth/session')[1]['user'] is None
records['after_logout_ai'] = call(client, '/api/ai/features')[0]
assert records['after_logout_ai'] == 401
records['gpu_requests'] = 0
Path(__file__).with_name('auth-probe.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
print(json.dumps(records))
