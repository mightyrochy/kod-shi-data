import asyncio, json, os, time, glob, traceback
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
D = "/mnt/c/tmp/colab-mcp"
def log(*a):
    with open(f"{D}/events.log", "a", encoding="utf-8") as f:
        f.write(time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a) + "\n")
async def main():
    env = dict(os.environ, BROWSER=f"{D}/openurl.sh %s")
    t = StdioTransport(command="uvx", args=["--python", "3.13", "--from", "git+https://github.com/googlecolab/colab-mcp", "colab-mcp", "-l", f"{D}/serverlog"], env=env)
    async with Client(t, timeout=600) as c:
        log("server started; tools:", [x.name for x in await c.list_tools()])
        last = None
        opened = 0
        while True:
            try:
                names = sorted(x.name for x in await c.list_tools())
            except Exception as e:
                names = ["ERR " + repr(e)[:200]]
            st = "open_colab_browser_connection" in names and len(names) > 1
            if st != last:
                log("tools changed; n=", len(names), names)
                last = st
            for jf in sorted(glob.glob(f"{D}/jobs/*.json")):
                if jf.endswith(".out.json"): continue
                out = jf[:-5] + ".out.json"
                if os.path.exists(out): continue
                job = json.load(open(jf, encoding="utf-8"))
                t0 = time.time()
                try:
                    r = await c.call_tool(job["tool"], job.get("args", {}), raise_on_error=False)
                    res = {"is_error": r.is_error, "content": [getattr(x, "text", str(x)) for x in r.content], "data": getattr(r, "structured_content", None)}
                except Exception as e:
                    res = {"exception": repr(e)[:2000], "tb": traceback.format_exc()[-1500:]}
                res["secs"] = round(time.time() - t0, 1); res["t"] = time.strftime("%H:%M:%S")
                json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
                log("job", os.path.basename(jf), "done", res["secs"], "s")
            await asyncio.sleep(2)
asyncio.run(main())
