"""Local block explorer (Flask, binds 127.0.0.1 only).

All dynamic values are HTML-escaped before interpolation; memos are
user-controlled data even on a localhost page.
"""

from html import escape as esc

from flask import Flask, abort

from . import chain, config, crypto, tx as tx_mod


def create_app(node) -> Flask:
    app = Flask(__name__)
    app.config["node"] = node

    def n():
        return app.config["node"]

    @app.route("/")
    def index():
        node = n()
        blocks = node.blocks
        latest = list(reversed(blocks[-10:]))
        genesis = blocks[0]
        return (
            render_page(
                "KLEX explorer",
                f"""
                <section class="card">
                  <h2>Genesis</h2>
                  <p class="mono small">{esc(genesis['hash'])}</p>
                  <blockquote>{esc(genesis['txs'][0]['memo'])}</blockquote>
                </section>
                <section class="card">
                  <h2>Status</h2>
                  <table class="kv">
                    <tr><td>height</td><td>{node.state['height']}</td></tr>
                    <tr><td>difficulty</td><td>{node.state['difficulty']}</td></tr>
                    <tr><td>supply</td><td>{node.state['supply']} / {config.MAX_SUPPLY:,} KLEX</td></tr>
                    <tr><td>reward</td><td>{chain.block_reward(node.state['height'] + 1)} KLEX</td></tr>
                    <tr><td>mempool</td><td>{len(node.mempool)} pending tx(s)</td></tr>
                  </table>
                </section>
                <section class="card">
                  <h2>Latest blocks</h2>
                  {render_block_list(latest)}
                </section>
                """,
            )
        )

    @app.route("/block/<int:height>")
    def block_page(height: int):
        if height < 0 or height >= len(n().blocks):
            abort(404)
        b = n().blocks[height]
        txs_html = "".join(render_tx(t, height) for t in b["txs"])
        return render_page(
            f"block #{height}",
            f"""
            <section class="card">
              <h2>Block #{b['index']}</h2>
              <table class="kv">
                <tr><td>hash</td><td class="mono">{esc(chain.block_hash(b))}</td></tr>
                <tr><td>prev_hash</td><td class="mono">{esc(b['prev_hash'])}</td></tr>
                <tr><td>timestamp</td><td>{esc(str(b['timestamp']))} UTC</td></tr>
                <tr><td>difficulty</td><td>{esc(str(b['difficulty']))} leading hex zeros</td></tr>
                <tr><td>nonce</td><td>{esc(str(b['nonce']))}</td></tr>
                <tr><td>tx_root</td><td class="mono">{esc(b['tx_root'])}</td></tr>
                <tr><td>transactions</td><td>{len(b['txs'])}</td></tr>
              </table>
            </section>
            <section class="card"><h2>Transactions</h2>{txs_html or '<p>none</p>'}</section>
            """,
        )

    @app.route("/addr/<address>")
    def addr_page(address: str):
        node = n()
        if not crypto.address_is_valid(address):
            abort(404)
        hist = node.address_history(address)
        rows = "".join(
            f'<tr><td><a href="/block/{h["height"]}">#{h["height"]}</a></td>'
            f"<td>{esc(str(h['tx'].get('type')))}</td><td>{esc(fmt_delta(h['tx'], address))}</td>"
            f'<td>{esc(h["tx"].get("memo", ""))}</td></tr>'
            for h in hist
        )
        return render_page(
            f"{address}",
            f"""
            <section class="card">
              <h2>{esc(address)}</h2>
              <p>balance: <b>{node.balance(address)}</b> KLEX</p>
              <table class="kv">
                <tr><th>block</th><th>type</th><th>delta</th><th>memo</th></tr>
                {rows or '<tr><td colspan=4>no history</td></tr>'}
              </table>
            </section>
            """,
        )

    @app.route("/api/summary")
    def api_summary():
        node = n()
        return {"height": node.state["height"], "difficulty": node.state["difficulty"],
                "supply": node.state["supply"], "genesis": node.blocks[0]["hash"]}

    @app.route("/api/block/<int:height>")
    def api_block(height: int):
        node = n()
        if height < 0 or height >= len(node.blocks):
            abort(404)
        return {"block": node.blocks[height]}

    return app


def render_tx(t: dict, height: int) -> str:
    if t.get("type") == "coinbase":
        return (
            f'<div class="tx"><b>coinbase</b> +{esc(str(t["amount"]))} KLEX → '
            f'<a href="/addr/{esc(t["to"])}">{esc(t["to"])}</a></div>'
        )
    if t.get("type") == "genesis":
        return f'<div class="tx"><b>genesis payload</b> · "{esc(t.get("memo", ""))}"</div>'
    return (
        f'<div class="tx"><b>{esc(str(t["type"]))}</b> {esc(str(t["amount"]))} KLEX '
        f'from <a href="/addr/{esc(t["from"])}">{esc(t["from"][:18])}…</a> '
        f'to <a href="/addr/{esc(t["to"])}">{esc(t["to"][:18])}…</a>'
        + (f' · memo "{esc(t["memo"])}"' if t.get("memo") else "")
        + "</div>"
    )


def fmt_delta(t: dict, address: str) -> str:
    if t.get("type") == "coinbase":
        return f"+{t['amount']}" if t["to"] == address else "0"
    if t.get("from") == address:
        return f"-{t['amount'] + t.get('fee', 0)}"
    if t.get("to") == address:
        return f"+{t['amount']}"
    return "0"


def render_block_list(blocks) -> str:
    rows = "".join(
        f'<tr><td><a href="/block/{b["index"]}">#{b["index"]}</a></td>'
        f"<td>{b['timestamp']}</td><td>{len(b['txs'])} tx(s)</td>"
        f'<td class="mono small">{esc(chain.block_hash(b)[:24])}…</td></tr>'
        for b in blocks
    )
    return f'<table class="kv"><tr><th>height</th><th>time</th><th>txs</th><th>hash</th></tr>{rows}</table>'


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · KLEX</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin:0; font:16px/1.6 ui-monospace, SFMono-Regular, Menlo, monospace; background:#0b0f14; color:#d7e0ea; }}
  header {{ padding:18px 24px; border-bottom:1px solid #1d2733; display:flex; gap:16px; align-items:baseline; }}
  header a {{ color:#7fd4a8; text-decoration:none; font-weight:700; }}
  main {{ max-width:960px; margin:24px auto; padding:0 16px; }}
  .card {{ background:#111820; border:1px solid #1d2732; border-radius:10px; padding:16px 20px; margin-bottom:16px; }}
  h2 {{ margin:0 0 10px; font-size:15px; letter-spacing:.08em; text-transform:uppercase; color:#8fa3b8; }}
  table.kv {{ width:100%; border-collapse:collapse; }}
  table.kv td, table.kv th {{ padding:4px 8px; border-bottom:1px solid #1d2732; text-align:left; word-break:break-all; }}
  th {{ color:#8fa3b8; font-weight:600; }}
  blockquote {{ margin:8px 0 0; padding:8px 14px; border-left:3px solid #7fd4a8; color:#cfe9db; }}
  .tx {{ padding:6px 0; border-bottom:1px dashed #1d2732; }}
  .mono {{ font-family:inherit; word-break:break-all; }}
  .small {{ font-size:13px; color:#8fa3b8; }}
  a {{ color:#7fd4a8; }}
</style></head><body>
<header><a href="/">KLEX explorer</a><span class="small">localhost only · klex v{version}</span></header>
<main>{body}</main>
</body></html>"""


def render_page(title: str, body: str) -> str:
    from . import __version__

    return PAGE.format(title=title, body=body, version=__version__)


def serve(node, host: str = "127.0.0.1", port: int = 8337) -> None:
    app = create_app(node)
    print(f"explorer: http://127.0.0.1:{port}  (Ctrl-C to stop)")
    app.run(host=host, port=port, debug=False)