from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import psycopg
from psycopg import OperationalError

from app.config import build_postgres_dsn, load_config

PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Ads Collector Viewer</title>
  <style>
    :root {
      --bg: #f4efe6;
      --panel: rgba(255, 250, 242, 0.92);
      --ink: #1f1a16;
      --muted: #6d6358;
      --line: rgba(31, 26, 22, 0.12);
      --accent: #c65d2e;
      --shadow: 0 20px 60px rgba(80, 48, 20, 0.12);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(198, 93, 46, 0.18), transparent 28%),
        radial-gradient(circle at right 20%, rgba(113, 148, 102, 0.16), transparent 24%),
        linear-gradient(180deg, #f9f4ec 0%, var(--bg) 100%);
      min-height: 100vh;
    }
    .shell { width: min(1280px, calc(100vw - 32px)); margin: 28px auto; display: grid; gap: 18px; }
    .hero, .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .hero { position: relative; }
    .hero::before {
      content: "";
      position: absolute;
      inset: 0;
      background:
        linear-gradient(135deg, rgba(198, 93, 46, 0.12), transparent 32%),
        repeating-linear-gradient(90deg, transparent 0, transparent 18px, rgba(31, 26, 22, 0.03) 18px, rgba(31, 26, 22, 0.03) 19px);
      pointer-events: none;
    }
    .hero-inner { padding: 28px 28px 18px; position: relative; }
    .eyebrow {
      display: inline-block; padding: 6px 12px; border-radius: 999px; border: 1px solid var(--line);
      background: rgba(255,255,255,0.55); font-size: 12px; letter-spacing: 0.18em; text-transform: uppercase; color: var(--muted);
    }
    h1 { margin: 16px 0 8px; font-size: clamp(32px, 5vw, 64px); line-height: 0.95; letter-spacing: -0.04em; max-width: 10ch; }
    .sub { max-width: 68ch; font-size: 16px; line-height: 1.7; color: var(--muted); margin: 0; }
    .controls { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)) auto; gap: 12px; margin-top: 24px; }
    .field { display: grid; gap: 8px; }
    .field label { font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted); }
    .field input, .field select {
      width: 100%; padding: 14px 16px; border-radius: 16px; border: 1px solid var(--line);
      background: rgba(255,255,255,0.78); color: var(--ink); font-size: 15px; outline: none;
    }
    .actions { display: flex; align-items: end; }
    .button {
      height: 48px; padding: 0 20px; border: 0; border-radius: 16px;
      background: linear-gradient(135deg, #b3491c, var(--accent)); color: #fff8f2;
      font-size: 15px; font-weight: 700; cursor: pointer;
      box-shadow: 0 14px 30px rgba(198, 93, 46, 0.24);
    }
    .meta { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; padding: 0 28px 28px; position: relative; }
    .stat { border: 1px solid var(--line); border-radius: 20px; padding: 18px; background: rgba(255,255,255,0.56); }
    .stat .label { font-size: 12px; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); }
    .stat .value { margin-top: 8px; font-size: clamp(22px, 3vw, 34px); line-height: 1; }
    .panel-head { display: flex; justify-content: space-between; gap: 16px; padding: 22px 24px; border-bottom: 1px solid var(--line); align-items: center; }
    .panel-head h2 { margin: 0; font-size: 22px; }
    .status { color: var(--muted); font-size: 14px; }
    .error {
      margin: 18px 24px 0; padding: 14px 16px; border-radius: 16px; color: #7a240f;
      background: rgba(180, 73, 28, 0.12); border: 1px solid rgba(180, 73, 28, 0.18); display: none;
    }
    .table-wrap { overflow: auto; padding: 0 12px 12px; }
    table { width: 100%; border-collapse: separate; border-spacing: 0 10px; min-width: 980px; }
    thead th { text-align: left; font-size: 12px; text-transform: uppercase; letter-spacing: 0.12em; color: var(--muted); padding: 0 12px 8px; }
    tbody tr { transform: translateY(8px); opacity: 0; animation: rise 400ms forwards; }
    tbody td {
      background: rgba(255,255,255,0.72); border-top: 1px solid var(--line); border-bottom: 1px solid var(--line);
      padding: 14px 12px; vertical-align: top; font-size: 14px; line-height: 1.55;
    }
    tbody td:first-child { border-left: 1px solid var(--line); border-top-left-radius: 16px; border-bottom-left-radius: 16px; }
    tbody td:last-child { border-right: 1px solid var(--line); border-top-right-radius: 16px; border-bottom-right-radius: 16px; }
    .pill {
      display: inline-flex; align-items: center; padding: 6px 10px; border-radius: 999px;
      background: rgba(198, 93, 46, 0.1); color: #8d3e1b; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em;
    }
    .empty { padding: 28px 24px 32px; color: var(--muted); display: none; }
    @keyframes rise { to { transform: translateY(0); opacity: 1; } }
    @media (max-width: 960px) {
      .controls, .meta { grid-template-columns: 1fr; }
      .actions { align-items: stretch; }
      .button { width: 100%; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="hero-inner">
        <span class="eyebrow">Ads Data Collector</span>
        <h1>Creative Archive Viewer</h1>
        <p class="sub">启动后直接查看库里的广告内容。可以按平台、游戏名和数量筛选，快速确认抓取结果、Hook 文案和时间区间。</p>
        <form class="controls" id="filters">
          <div class="field">
            <label for="platform">Platform</label>
            <select id="platform" name="platform">
              <option value="">All</option>
              <option value="facebook">Facebook</option>
              <option value="tiktok">TikTok</option>
            </select>
          </div>
          <div class="field">
            <label for="game_name">Game Name</label>
            <input id="game_name" name="game_name" placeholder="Whiteout Survival / Gossip Harbor">
          </div>
          <div class="field">
            <label for="limit">Limit</label>
            <input id="limit" name="limit" type="number" min="1" max="200" value="20">
          </div>
          <div class="field">
            <label for="connect_timeout">DB Timeout</label>
            <input id="connect_timeout" name="connect_timeout" type="number" min="1" max="30" value="5">
          </div>
          <div class="actions">
            <button class="button" type="submit">View Records</button>
          </div>
        </form>
      </div>
      <div class="meta">
        <article class="stat"><div class="label">Total Rows</div><div class="value" id="stat-total">-</div></article>
        <article class="stat"><div class="label">Platforms</div><div class="value" id="stat-platforms">-</div></article>
        <article class="stat"><div class="label">Latest Created</div><div class="value" id="stat-latest">-</div></article>
      </div>
    </section>
    <section class="panel">
      <div class="panel-head">
        <h2>Latest Creative Records</h2>
        <div class="status" id="status">Ready</div>
      </div>
      <div class="error" id="error"></div>
      <div class="empty" id="empty">没有查到数据。先运行采集入库，或者换一个筛选条件再试。</div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Platform</th>
              <th>Game</th>
              <th>Hook</th>
              <th>Material</th>
              <th>Country</th>
              <th>First Seen</th>
              <th>Last Seen</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody id="rows"></tbody>
        </table>
      </div>
    </section>
  </main>
  <script>
    const form = document.getElementById('filters');
    const rowsEl = document.getElementById('rows');
    const errorEl = document.getElementById('error');
    const emptyEl = document.getElementById('empty');
    const statusEl = document.getElementById('status');
    const statTotalEl = document.getElementById('stat-total');
    const statPlatformsEl = document.getElementById('stat-platforms');
    const statLatestEl = document.getElementById('stat-latest');

    const escapeHtml = (value) => String(value ?? '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#039;');

    async function loadData() {
      const params = new URLSearchParams(new FormData(form));
      statusEl.textContent = 'Loading...';
      errorEl.style.display = 'none';
      emptyEl.style.display = 'none';
      try {
        const response = await fetch(`/api/ads?${params.toString()}`);
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.error || 'Failed to load data');
        renderRows(payload.rows);
        renderStats(payload.meta);
        statusEl.textContent = `Loaded ${payload.rows.length} rows`;
      } catch (error) {
        rowsEl.innerHTML = '';
        statTotalEl.textContent = '-';
        statPlatformsEl.textContent = '-';
        statLatestEl.textContent = '-';
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
        statusEl.textContent = 'Error';
      }
    }

    function renderRows(rows) {
      rowsEl.innerHTML = '';
      if (!rows.length) {
        emptyEl.style.display = 'block';
        return;
      }
      rows.forEach((row, index) => {
        const tr = document.createElement('tr');
        tr.style.animationDelay = `${index * 45}ms`;
        tr.innerHTML = `
          <td>${escapeHtml(row.id)}</td>
          <td><span class="pill">${escapeHtml(row.platform)}</span></td>
          <td>${escapeHtml(row.game_name)}</td>
          <td>${escapeHtml(row.hook)}</td>
          <td>${row.material_url ? `<a href="${escapeHtml(row.material_url)}" target="_blank" rel="noreferrer">Open</a>` : 'NULL'}</td>
          <td>${escapeHtml(row.country || 'NULL')}</td>
          <td>${escapeHtml(row.first_seen || 'NULL')}</td>
          <td>${escapeHtml(row.last_seen || 'NULL')}</td>
          <td>${escapeHtml(row.created_at || 'NULL')}</td>
        `;
        rowsEl.appendChild(tr);
      });
    }

    function renderStats(meta) {
      statTotalEl.textContent = meta.total_rows;
      statPlatformsEl.textContent = meta.platforms.length ? meta.platforms.join(' / ') : '-';
      statLatestEl.textContent = meta.latest_created_at || '-';
    }

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      loadData();
    });

    loadData();
  </script>
</body>
</html>
"""


def clamp_int(raw_value: str, minimum: int, maximum: int, default: int) -> int:
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return default
    return min(max(value, minimum), maximum)


def get_rows(limit: int, platform: str | None, game_name: str | None, connect_timeout: int):
    config = load_config()
    dsn = build_postgres_dsn(config["database"])
    query = """
    SELECT id, platform, game_name, hook, material_url, country, first_seen, last_seen, created_at
    FROM ads_creative
    WHERE (%(platform)s = '' OR platform = %(platform)s)
      AND (%(game_name)s = '' OR game_name ILIKE %(game_name_pattern)s)
    ORDER BY id DESC
    LIMIT %(limit)s
    """
    params = {
        "platform": platform or "",
        "game_name": game_name or "",
        "game_name_pattern": f"%{game_name}%" if game_name else "",
        "limit": limit,
    }
    with psycopg.connect(dsn, connect_timeout=connect_timeout) as conn, conn.cursor() as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    columns = ["id", "platform", "game_name", "hook", "material_url", "country", "first_seen", "last_seen", "created_at"]
    normalized_rows = []
    for row in rows:
        item = dict(zip(columns, row))
        for key, value in item.items():
            if hasattr(value, "isoformat"):
                item[key] = value.isoformat(sep=" ", timespec="seconds")
        normalized_rows.append(item)
    return normalized_rows


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.respond_html(PAGE_TEMPLATE)
            return
        if parsed.path == "/api/ads":
            self.handle_api_ads(parsed.query)
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Not Found")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def handle_api_ads(self, query_string: str) -> None:
        query = parse_qs(query_string)
        limit = clamp_int(query.get("limit", ["20"])[0], minimum=1, maximum=200, default=20)
        platform = (query.get("platform", [""])[0] or "").strip().lower()
        game_name = (query.get("game_name", [""])[0] or "").strip()
        connect_timeout = clamp_int(query.get("connect_timeout", ["5"])[0], minimum=1, maximum=30, default=5)

        try:
            rows = get_rows(limit=limit, platform=platform, game_name=game_name, connect_timeout=connect_timeout)
        except OperationalError as exc:
            config = load_config()
            db = config["database"]
            self.respond_json(
                {"error": f"无法连接 Postgres: {db['host']}:{db['port']}/{db['name']}。详情: {exc}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            return
        except Exception as exc:
            self.respond_json({"error": f"读取数据失败: {exc}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        platforms = sorted({row["platform"] for row in rows if row.get("platform")})
        latest_created_at = rows[0]["created_at"] if rows else None
        self.respond_json(
            {
                "rows": rows,
                "meta": {
                    "total_rows": len(rows),
                    "platforms": platforms,
                    "latest_created_at": latest_created_at,
                },
            }
        )

    def respond_html(self, body: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def respond_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main():
    host = os.environ.get("ADS_VIEWER_HOST", "127.0.0.1")
    port = int(os.environ.get("ADS_VIEWER_PORT", "8787"))
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Ads Viewer running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
