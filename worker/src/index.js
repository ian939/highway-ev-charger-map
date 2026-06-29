// 카카오모빌리티 길찾기 REST API 프록시 (CORS 허용 + REST키 은닉)
const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, OPTIONS",
};

export default {
  async fetch(req, env) {
    if (req.method === "OPTIONS") return new Response(null, { headers: CORS });
    const url = new URL(req.url);
    if (url.pathname !== "/route") {
      return new Response("highway-ev-route-proxy ok", { headers: CORS });
    }
    const origin = url.searchParams.get("origin");
    const destination = url.searchParams.get("destination");
    if (!origin || !destination) {
      return json({ error: "origin/destination 필요" }, 400);
    }
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
  },
};

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...CORS },
  });
}
