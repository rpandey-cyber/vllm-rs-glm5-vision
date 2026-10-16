"""Extended image checks through a gateway: formats, size, remote URL, concurrency. usage: img_ext.py BASE_URL [auth]"""
import base64, io, json, os, ssl, sys, time, concurrent.futures as cf, urllib.request
from PIL import Image
base = sys.argv[1].rstrip("/"); auth = len(sys.argv) > 2 and sys.argv[2] == "auth"
MODEL = "nvidia/GLM-5.3-Flash-NVFP4"
_ca = "/etc/ssl/certs/ca-certificates.crt"
ctx = ssl.create_default_context(cafile=_ca if os.path.exists(_ca) else None) if base.startswith("https") else None
hdr = {"Content-Type": "application/json", "User-Agent": "mop-image-test/1.0"}
if auth: hdr["Authorization"] = "Bearer " + os.environ["API_TOKEN"]
def pic(w, h, fmt, **kw):
    im = Image.new("RGB", (w, h)); px = im.load()
    for x in range(0, w): 
        for y in range(0, h): px[x, y] = ((x * 255) // w, (y * 255) // h, (x * y) % 255)
    b = io.BytesIO(); im.save(b, fmt, **kw); return f"data:image/{fmt.lower()};base64," + base64.b64encode(b.getvalue()).decode(), len(b.getvalue())
def ask(content, label):
    body = {"model": MODEL, "max_tokens": 32, "messages": [{"role": "user", "content": content}]}
    t0 = time.time()
    try:
        r = urllib.request.urlopen(urllib.request.Request(base + "/v1/chat/completions", data=json.dumps(body).encode(), headers=hdr), timeout=180, context=ctx)
        d = json.loads(r.read()); return (True, f"{label:<34} http={r.status} prompt_tokens={d['usage']['prompt_tokens']:<5} {time.time()-t0:4.1f}s")
    except urllib.error.HTTPError as e: return (False, f"{label:<34} http={e.code} {e.read(160).decode()}")
    except Exception as e: return (False, f"{label:<34} {type(e).__name__}: {e}")
T = {"type": "text", "text": "Describe this image briefly."}
img = lambda u: {"type": "image_url", "image_url": {"url": u}}
cases = []
u, n = pic(800, 600, "JPEG", quality=85);  cases.append((f"JPEG 800x600 ({n//1024} KB)", [T, img(u)]))
u, n = pic(512, 512, "WEBP");              cases.append((f"WebP 512x512 ({n//1024} KB)", [T, img(u)]))
u, n = pic(3000, 2000, "JPEG", quality=90); cases.append((f"large JPEG 3000x2000 ({n//1024} KB)", [T, img(u)]))
cases.append(("remote https image URL", [T, img("https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png")]))
ok = 0
for label, content in cases:
    good, msg = ask(content, label); ok += good; print(("OK   " if good else "FAIL ") + msg)
# concurrency: 24 simultaneous image requests
u, _ = pic(448, 448, "PNG")
with cf.ThreadPoolExecutor(24) as ex:
    t0 = time.time(); res = list(ex.map(lambda i: ask([T, img(u)], f"c{i}"), range(24)))
g = sum(1 for r in res if r[0]); print(f"{'OK   ' if g == 24 else 'FAIL '}24 concurrent image requests: {g}/24 ok in {time.time()-t0:.1f}s")
bad = [m for gd, m in res if not gd][:2]; [print("   ", m) for m in bad]
print(f"SUMMARY: sequential {ok}/{len(cases)} ok, concurrent {g}/24 ok")
