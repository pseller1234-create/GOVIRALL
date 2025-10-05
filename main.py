# inside main.py, replace the mock return with this:
import os, json
from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

prompt = {
  "instruction":"Return viral analysis as strict JSON per contract.",
  "media": payload.get("media", {}),
  "platform_focus": payload.get("platform_focus","tiktok"),
  "controls":{
    "readability_grade":"6-8",
    "summary_max_words":28,
    "rationale_max_words":40,
    "ab_tagging_for_hooks":True
  }
}
resp = client.chat.completions.create(
  model=MODEL,
  temperature=0.6,
  messages=[
    {"role":"system","content":"You are ViralNOW… (paste your full system prompt here)"},
    {"role":"user","content":json.dumps(prompt)}
  ],
)
content = resp.choices[0].message.content
# trust but verify: parse JSON or fallback
try:
    data = json.loads(content)
except:
    # light fix if model wrapped text; extract JSON braces
    start, end = content.find("{"), content.rfind("}")
    data = json.loads(content[start:end+1])
return JSONResponse(data)
