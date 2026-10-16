import json, os, ssl, sys, time, urllib.request
base = sys.argv[1].rstrip("/"); _ca = "/etc/ssl/certs/ca-certificates.crt"
ctx = ssl.create_default_context(cafile=_ca if os.path.exists(_ca) else None)
hdr = {"Content-Type": "application/json", "User-Agent": "mop-image-test/1.0", "Authorization": "Bearer " + os.environ["API_TOKEN"]}
urls = ["https://raw.githubusercontent.com/github/explore/main/topics/python/python.png",
        "https://httpbin.org/image/jpeg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"]
for u in urls:
    body = {"model": "nvidia/GLM-5.3-Flash-NVFP4", "max_tokens": 32, "messages": [{"role": "user", "content": [{"type": "text", "text": "What is in this image? One sentence."}, {"type": "image_url", "image_url": {"url": u}}]}]}
    t0 = time.time()
    try:
        r = urllib.request.urlopen(urllib.request.Request(base + "/v1/chat/completions", data=json.dumps(body).encode(), headers=hdr), timeout=120, context=ctx)
        d = json.loads(r.read()); m = d["choices"][0]["message"]; print(f"OK   {u.split('/')[2]:<28} prompt_tokens={d['usage']['prompt_tokens']:<5} {time.time()-t0:4.1f}s :: {(m.get('content') or m.get('reasoning') or '')[:80]!r}")
    except urllib.error.HTTPError as e:
        msg = json.loads(e.read().decode()).get("error", {}).get("message", "")[:150]; print(f"FAIL {u.split('/')[2]:<28} http={e.code} :: {msg}")
