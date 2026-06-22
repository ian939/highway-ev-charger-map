# data.json과 JS 키를 템플릿에 주입해 자립형 index.html을 생성하는 빌드 스크립트
# -*- coding: utf-8 -*-
import os
import json

from dotenv import load_dotenv

BASE = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE, ".env"))

JS_KEY = os.environ["KAKAO_JS_KEY"]

with open(os.path.join(BASE, "data.json"), encoding="utf-8") as f:
    data = json.load(f)

# HTML에 불필요한 내부 디버그 필드 제거
for d in data:
    d.pop("_method", None)
    d.pop("_matched", None)

with open(os.path.join(BASE, "template_index.html"), encoding="utf-8") as f:
    html = f.read()

html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
html = html.replace("__JSKEY__", JS_KEY)

out = os.path.join(BASE, "index.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)

print(f"생성 완료: {out}  ({len(data)}개 휴게소 임베드)")
