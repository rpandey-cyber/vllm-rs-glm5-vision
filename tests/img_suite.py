"""Image-support test suite. usage: img_suite.py BASE_URL LABEL [auth]   (stdlib only)"""
import base64, json, os, ssl, struct, sys, time, urllib.request, zlib
base, label = sys.argv[1].rstrip("/"), sys.argv[2]
auth = len(sys.argv) > 3 and sys.argv[3] == "auth"
MODEL = "nvidia/GLM-5.3-Flash-NVFP4"
def png(w, h):
    raw = b"".join(b"\x00" + bytes(v for x in range(w) for v in ((x * 255) // max(w - 1, 1), (y * 255) // max(h - 1, 1), 128)) for y in range(h))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b"")
uri = lambda w, h: "data:image/png;base64," + base64.b64encode(png(w, h)).decode()
img = lambda w, h: {"type": "image_url", "image_url": {"url": uri(w, h)}}
txt = lambda t: {"type": "text", "text": t}
cases = [
  ("text only (control)",        [txt("Say hi in 3 words.")]),
  ("1 image 256x256",            [txt("Describe this image."), img(256, 256)]),
  ("1 image 640x480 (non-square)", [txt("What colors do you see?"), img(640, 480)]),
  ("1 image 64x64 (tiny)",       [txt("Describe this image."), img(64, 64)]),
  ("2 images",                   [txt("Compare these two images."), img(224, 224), img(320, 240)]),
]
_ca = "/etc/ssl/certs/ca-certificates.crt"; ctx = (ssl.create_default_context(cafile=_ca if os.path.exists(_ca) else None) if base.startswith("https") else None)
hdr = {"Content-Type": "application/json", "User-Agent": "mop-image-test/1.0"}
if auth: hdr["Authorization"] = "Bearer " + os.environ["API_TOKEN"]
bad = 0
for name, content in cases:
    body = {"model": MODEL, "max_tokens": 48, "messages": [{"role": "user", "content": content}]}
    t0 = time.time()
    try:
        r = urllib.request.urlopen(urllib.request.Request(base + "/v1/chat/completions", data=json.dumps(body).encode(), headers=hdr), timeout=120, context=ctx)
        d = json.loads(r.read()); m = d["choices"][0]["message"]
        out = (m.get("content") or m.get("reasoning") or "")[:70].replace("\n", " ")
        print(f"[{label}] OK   {name:<30} http={r.status} prompt_tokens={d['usage']['prompt_tokens']:<5} {time.time()-t0:4.1f}s :: {out}")
    except urllib.error.HTTPError as e:
        bad += 1; print(f"[{label}] FAIL {name:<30} http={e.code} :: {e.read(200).decode()}")
    except Exception as e:
        bad += 1; print(f"[{label}] FAIL {name:<30} {type(e).__name__}: {e}")
print(f"[{label}] SUMMARY: {len(cases)-bad}/{len(cases)} passed"); sys.exit(1 if bad else 0)
