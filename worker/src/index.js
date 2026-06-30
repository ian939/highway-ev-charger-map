// 카카오 길찾기 + 네이버(블로그·지역) 검색 프록시 (CORS 허용 + 키 은닉)
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
};

export default {
  async fetch(req, env) {
    if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
    const url = new URL(req.url);
    const p = url.pathname;
    if (p === "/route") return route(url, env);
    if (p === "/blogs") return naverBlogs(url, env);
    if (p === "/local") return naverLocal(url, env);
    return new Response("highway-ev-route-proxy ok", { headers: CORS });
  },
};

// 카카오모빌리티 길찾기
async function route(url, env) {
  const origin = url.searchParams.get("origin");
  const destination = url.searchParams.get("destination");
  if (!origin || !destination) return json({ error: "origin/destination 필요" }, 400);
  const api = "https://apis-navi.kakaomobility.com/v1/directions?" +
    new URLSearchParams({ origin, destination, priority: "RECOMMEND" });
  try {
    const r = await fetch(api, { headers: { Authorization: `KakaoAK ${env.KAKAO_REST_KEY}` } });
    return new Response(await r.text(), {
      status: r.status,
      headers: { "Content-Type": "application/json; charset=utf-8", ...CORS },
    });
  } catch (e) {
    return json({ error: "프록시 실패", detail: String(e) }, 502);
  }
}

// --- 네이버 공통 ---
const naverHeaders = (env) => ({
  "X-Naver-Client-Id": env.NAVER_CLIENT_ID,
  "X-Naver-Client-Secret": env.NAVER_CLIENT_SECRET,
});
const stripTags = (s) => (s || "")
  .replace(/<\/?b>/g, "").replace(/&quot;/g, '"').replace(/&amp;/g, "&")
  .replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&#39;/g, "'");

// 네이버 블로그 검색 (인기=관련도순)
async function naverBlogs(url, env) {
  const q = url.searchParams.get("q");
  if (!q) return json({ error: "q 필요" }, 400);
  if (!env.NAVER_CLIENT_ID) return json({ error: "네이버 키 미설정" }, 500);
  const api = "https://openapi.naver.com/v1/search/blog?" +
    new URLSearchParams({ query: q, display: "5", sort: "sim" });
  try {
    const r = await fetch(api, { headers: naverHeaders(env) });
    if (!r.ok) return json({ error: "네이버 블로그 오류", status: r.status }, r.status);
    const data = await r.json();
    const items = (data.items || []).map((it) => ({
      title: stripTags(it.title),
      desc: stripTags(it.description),
      link: it.link,
      blogger: it.bloggername,
      date: it.postdate,
    }));
    return json({ items }, 200);
  } catch (e) {
    return json({ error: "프록시 실패", detail: String(e) }, 502);
  }
}

// 네이버 지역 검색 (주변 볼거리)
async function naverLocal(url, env) {
  const q = url.searchParams.get("q");
  if (!q) return json({ error: "q 필요" }, 400);
  if (!env.NAVER_CLIENT_ID) return json({ error: "네이버 키 미설정" }, 500);
  const api = "https://openapi.naver.com/v1/search/local?" +
    new URLSearchParams({ query: q, display: "5", sort: "random" });
  try {
    const r = await fetch(api, { headers: naverHeaders(env) });
    if (!r.ok) return json({ error: "네이버 지역 오류", status: r.status }, r.status);
    const data = await r.json();
    const items = (data.items || []).map((it) => ({
      title: stripTags(it.title),
      category: it.category,
      address: it.roadAddress || it.address,
      link: it.link,
    }));
    return json({ items }, 200);
  } catch (e) {
    return json({ error: "프록시 실패", detail: String(e) }, 502);
  }
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...CORS },
  });
}
