# 도로공사 휴게소 베스트음식 OpenAPI → 휴게소별 대표메뉴 food.json 생성 + 스테이션 매칭 리포트
import io, sys, os, re, json, time, urllib.request, urllib.parse
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(HERE)

# data.ex.co.kr(고속도로 공공데이터 포털) 인증키 — 환경변수 EX_API_KEY 또는 첫 인자
KEY = os.environ.get("EX_API_KEY") or (sys.argv[1] if len(sys.argv) > 1 else "")
if not KEY:
    print("EX_API_KEY(고속도로 공공데이터포털 인증키)가 필요합니다."); raise SystemExit(1)

ENDPOINT = "https://data.ex.co.kr/openapi/restinfo/restBestfoodList"
# 응답 필드명(첫 호출로 확인 후 필요시 조정)
F_REST = "stdRestNm"   # 휴게소명
F_FOOD = "foodNm"      # 음식명
F_COST = "foodCost"    # 가격


def fetch_page(page, rows=100):
    qs = urllib.parse.urlencode({"key": KEY, "type": "json", "numOfRows": rows, "pageNo": page})
    with urllib.request.urlopen(f"{ENDPOINT}?{qs}", timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def normName(s):
    """휴게소명 정규화: 괄호(방향) 제거 + '휴게소' 제거 + 공백 제거. 프론트 normName과 동일 규칙."""
    s = re.sub(r"\(.*?\)", "", s or "")
    s = s.replace("휴게소", "")
    s = re.sub(r"\s+", "", s)
    return s.strip()


# 1) 전체 페이지 수집
first = fetch_page(1)
if first.get("list"):
    print("[확인] 첫 레코드 키:", list(first["list"][0].keys()))
    print("[확인] 첫 레코드 샘플:", json.dumps(first["list"][0], ensure_ascii=False)[:300])
total = int(first.get("count", 0))
rows = int(first.get("numOfRows", 100)) or 100
pages = (total + rows - 1) // rows if total else 1
print(f"[정보] count={total}, numOfRows={rows}, pages={pages}")

records = list(first.get("list", []))
for p in range(2, pages + 1):
    try:
        records += fetch_page(p).get("list", [])
    except Exception as e:
        print(f"  page {p} 실패: {e}")
    time.sleep(0.05)
print(f"[정보] 수집 레코드 {len(records)}개")

# 2) 휴게소(정규화키)별 대표메뉴 집계 (중복 제거, 상위 6개)
bykey = defaultdict(list)
seen = defaultdict(set)
for r in records:
    rest = r.get(F_REST) or ""
    food = (r.get(F_FOOD) or "").strip()
    if not rest or not food:
        continue
    k = normName(rest)
    if food in seen[k]:
        continue
    seen[k].add(food)
    cost = r.get(F_COST)
    bykey[k].append({"menu": food, "price": cost})

food_map = {k: v[:6] for k, v in bykey.items()}

# 3) 우리 스테이션과 매칭 리포트
sk = json.load(open(os.path.join(HERE, "sk_chargers.json"), encoding="utf-8"))
dj = json.load(open(os.path.join(PARENT, "data.json"), encoding="utf-8"))
prep = [d for d in dj if d.get("operators") and any(
    op in ("5차 1권역", "5차 2권역", "5차 3권역") for op in d["operators"])]
stations = [s["name"] for s in sk] + [d["name"] for d in prep]
matched = [n for n in stations if normName(n) in food_map]
print(f"[매칭] 스테이션 {len(stations)}곳 중 음식 매칭 {len(matched)}곳 ({len(matched)*100//max(1,len(stations))}%)")
miss = [n for n in stations if normName(n) not in food_map]
print("[미매칭 예시]", miss[:15])

# 4) 저장 (docs/route 양쪽)
out = json.dumps(food_map, ensure_ascii=False, indent=1)
open(os.path.join(HERE, "food.json"), "w", encoding="utf-8").write(out)
open(os.path.join(PARENT, "docs", "food.json"), "w", encoding="utf-8").write(out)
print(f"[생성] food.json (휴게소 {len(food_map)}곳) → route/, docs/")
