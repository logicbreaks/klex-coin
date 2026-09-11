"""Printable genesis certificate (HTML + embedded SVG QR, prints on A4)."""

import io
from datetime import datetime, timezone

import qrcode
import qrcode.image.svg

from . import chain, config, crypto

CERT_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>KLEX · Certificate of Genesis</title>
<style>
  @page {{ size: A4; margin: 0; }}
  html,body {{ margin:0; padding:0; }}
  body {{ font: 15px/1.65 Georgia, 'Times New Roman', serif; color:#151a20; background:#e9e4d8; }}
  .sheet {{ box-sizing:border-box; width:210mm; min-height:297mm; margin:0 auto; padding:20mm 22mm;
           background:#f6f1e5; position:relative; }}
  .frame {{ position:absolute; inset:12mm; border:1.6px solid #2a2f38; pointer-events:none; }}
  .frame-inner {{ position:absolute; inset:13.5mm; border:.5px solid #2a2f38; }}
  h1 {{ font-size:34px; letter-spacing:.35em; margin:14mm 0 2mm; text-align:center; font-weight:600; }}
  .subtitle {{ text-align:center; letter-spacing:.22em; text-transform:uppercase; font-size:12px; color:#5a636f; }}
  .rule {{ width:70mm; margin:8mm auto; border-bottom:1px solid #2a2f38; }}
  .message {{ font-size:20px; font-style:italic; text-align:center; margin:12mm 10mm; line-height:1.8; }}
  .hashlabel {{ letter-spacing:.18em; text-transform:uppercase; font-size:10px; color:#5a636f; text-align:center; }}
  .hash {{ font:13px/1.5 ui-monospace, Menlo, monospace; text-align:center; margin:2mm 0 8mm; word-break:break-all; }}
  .grid {{ display:flex; gap:10mm; align-items:flex-start; justify-content:center; margin-top:10mm; }}
  .specs {{ font-size:12.5px; border-collapse:collapse; }}
  .specs td {{ padding:2.5mm 6mm; border-bottom:.5px solid #b9b2a4; }}
  .specs td:first-child {{ letter-spacing:.12em; text-transform:uppercase; font-size:10.5px; color:#5a636f; padding-right:4mm; }}
  .qrbox {{ text-align:center; }}
  .qrbox svg {{ width:52mm; height:52mm; }}
  .addr {{ font:9.5px/1.4 ui-monospace, Menlo, monospace; word-break:break-all; max-width:52mm; margin:4mm auto 0; }}
  .footer {{ position:absolute; bottom:16mm; left:22mm; right:22mm; text-align:center;
            font-size:11px; color:#5a636f; letter-spacing:.08em; }}
  .seal {{ position:absolute; top:16mm; right:16mm; width:22mm; height:22mm; border:1px solid #2a2f38;
          border-radius:50%; display:flex; align-items:center; justify-content:center; text-align:center;
          font-size:8px; letter-spacing:.14em; color:#2a2f38; line-height:1.5; }}
  @media print {{ body {{ background:#f6f1e5; }} }}
</style></head><body>
<div class="sheet">
  <div class="frame"><div class="frame-inner"></div></div>
  <div class="seal">KLEX<br>FAIR LAUNCH<br>NO PREMINE<br>{year}</div>
  <h1>KLEX</h1>
  <div class="subtitle">Certificate of Genesis</div>
  <div class="rule"></div>
  <p class="message">{message}</p>
  <div class="hashlabel">Genesis block hash — permanent, verifiable, unforgeable</div>
  <p class="hash">{genesis_hash}</p>
  <div class="grid">
    <table class="specs">
      <tr><td>Chain</td><td>KLEX · proof of work · SHA3-256 (KlexHash)</td></tr>
      <tr><td>Signatures</td><td>ML-DSA — NIST FIPS 204 (post-quantum)</td></tr>
      <tr><td>Block time</td><td>{block_time} seconds · retarget every {retarget} blocks</td></tr>
      <tr><td>Supply</td><td>{max_supply:,} KLEX · {reward} per block · halving every {halving:,}</td></tr>
      <tr><td>Launch</td><td>Fair launch · genesis allocates zero coins</td></tr>
      <tr><td>First holder</td><td class="mono">{address_short}…</td></tr>
    </table>
    <div class="qrbox">
      {qr_svg}
      <div class="hashlabel" style="margin-top:4mm">first wallet address</div>
    </div>
  </div>
  <div class="footer">
    Issued {issued} · value starts at zero, like everything great · verify with <b>klex verify</b>
  </div>
</div>
</body></html>"""


def qr_svg(address: str) -> str:
    img = qrcode.make(address, image_factory=qrcode.image.svg.SvgPathImage, border=1)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode("utf-8")


def generate_certificate(node, address: str, out_path: str) -> str:
    if not crypto.address_is_valid(address):
        raise ValueError("invalid address for certificate")
    genesis = node.blocks[0]
    html = CERT_TEMPLATE.format(
        message=genesis["txs"][0]["memo"],
        genesis_hash=genesis["hash"],
        address_short=address[:20],
        address=address,
        qr_svg=qr_svg(address),
        block_time=config.BLOCK_TIME,
        retarget=config.RETARGET_INTERVAL,
        max_supply=config.MAX_SUPPLY,
        reward=config.BLOCK_REWARD,
        halving=config.HALVING_INTERVAL,
        issued=datetime.now(timezone.utc).strftime("%d %B %Y"),
        year=datetime.now(timezone.utc).year,
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path