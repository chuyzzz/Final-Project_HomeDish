import base64, json, os, time, uuid
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from config import BASE_URL, MODEL, Budget
ROOT = Path(__file__).resolve().parent; LOG = ROOT / "logs" / "runs.jsonl"
def load_env():
    load_dotenv(ROOT/".env", override=False); load_dotenv(ROOT.parent/".env", override=False)
    key = os.getenv("PORTKEY_API_KEY") or os.getenv("PORTKEY_API")
    if not key: raise RuntimeError("PORTKEY_API_KEY is missing. Put it in Final Project/.env or the parent .env.")
    return key
def get_client():
    key=load_env(); return OpenAI(api_key=key, base_url=BASE_URL, default_headers={"x-portkey-api-key":key,"x-portkey-provider":"openai"})
def image_data_url(path, max_px=768):
    from PIL import Image
    import io
    image=Image.open(path).convert("RGB"); image.thumbnail((max_px,max_px)); buf=io.BytesIO(); image.save(buf,format="JPEG",quality=85)
    return "data:image/jpeg;base64,"+base64.b64encode(buf.getvalue()).decode()
def chat(messages, agent_name, budget: Budget, response_format=None):
    started=time.perf_counter(); kwargs={"model":MODEL,"messages":messages}
    if response_format: kwargs["response_format"]=response_format
    result=get_client().chat.completions.create(**kwargs); usage=result.usage
    inp=getattr(usage,"prompt_tokens",0) or 0; cached=getattr(getattr(usage,"prompt_tokens_details",None),"cached_tokens",0) or 0; out=getattr(usage,"completion_tokens",0) or 0; budget.charge(inp,cached,out)
    LOG.parent.mkdir(exist_ok=True)
    with LOG.open("a",encoding="utf-8") as f: f.write(json.dumps({"run_id":str(uuid.uuid4()),"agent":agent_name,"input_tokens":inp,"cached_input_tokens":cached,"output_tokens":out,"latency_s":round(time.perf_counter()-started,3),"timestamp":time.time(),"cost_usd":budget.cost_usd})+"\n")
    return result.choices[0].message.content or ""
