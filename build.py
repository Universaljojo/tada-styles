#!/usr/bin/env python3
"""Build a self-contained client-facing style picker page from the Tada style library JSON.

Reads:
    ../workflow/backend/prompt_library/style_items.v1.json
Writes:
    ./index.html (single self-contained file, no external deps besides cover image CDN)
"""
from __future__ import annotations

import io
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from PIL import Image

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "workflow" / "backend" / "prompt_library" / "style_items.v1.json"
OUT = HERE / "index.html"
THUMBS_DIR = HERE / "thumbs"
THUMB_WIDTH = 600          # px — looks crisp on retina at ~300px display width
THUMB_QUALITY = 78         # webp quality
DOWNLOAD_TIMEOUT = 30      # seconds


def ensure_thumb(index: int, url: str) -> str:
    """Download and resize cover to a local webp thumb. Returns relative path or original url on failure."""
    if not url:
        return url
    THUMBS_DIR.mkdir(exist_ok=True)
    filename = f"{index:03d}.webp"
    target = THUMBS_DIR / filename
    if target.exists():
        return f"thumbs/{filename}"
    try:
        resp = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))
        if img.mode in ("P", "RGBA"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
        if img.width > THUMB_WIDTH:
            ratio = THUMB_WIDTH / img.width
            new_size = (THUMB_WIDTH, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        img.save(target, "WEBP", quality=THUMB_QUALITY, method=6)
        print(f"  ✓ {filename}  ({target.stat().st_size // 1024} KB)")
        return f"thumbs/{filename}"
    except Exception as exc:
        print(f"  ✗ {filename}  failed: {exc} — falling back to remote URL")
        return url


def build() -> None:
    raw = json.loads(SOURCE.read_text(encoding="utf-8"))
    meta = raw.get("meta", {})
    items = raw.get("items", [])

    print(f"Generating thumbnails for {len(items)} styles...")
    thumb_paths: dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(ensure_thumb, i, it.get("cover", "")): i
            for i, it in enumerate(items, start=1)
        }
        for fut in as_completed(futures):
            idx = futures[fut]
            thumb_paths[idx] = fut.result()

    slim = []
    for i, it in enumerate(items, start=1):
        slim.append({
            "code": f"#{i:03d}",
            "title": it.get("title", ""),
            "thumb": thumb_paths.get(i, it.get("cover", "")),
            "cover": it.get("cover", ""),
            "categories": it.get("originalCategories", []) or [],
        })

    categories = meta.get("sourceCategoryOptions", []) or []

    payload = {
        "styles": slim,
        "categories": categories,
    }

    html = TEMPLATE.replace(
        "/*__DATA__*/null",
        json.dumps(payload, ensure_ascii=False),
    )
    OUT.write_text(html, encoding="utf-8")
    size_kb = OUT.stat().st_size / 1024
    print(f"Wrote {OUT} ({len(slim)} styles, {size_kb:.1f} KB)")


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tada 风格库</title>
<style>
  :root {
    --accent: #d14d72;
    --accent-soft: #fce7ee;
    --bg: #fafafa;
    --card: #ffffff;
    --text: #1a1a1a;
    --text-soft: #666;
    --border: #ececec;
    --radius: 14px;
    --radius-btn: 980px;
    --shadow: 0 6px 24px rgba(0,0,0,0.06);
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
    background: var(--bg);
    color: var(--text);
    -webkit-font-smoothing: antialiased;
  }
  header {
    padding: 48px 32px 24px;
    text-align: center;
    background: linear-gradient(180deg, #fff 0%, var(--bg) 100%);
    border-bottom: 1px solid var(--border);
  }
  header h1 {
    margin: 0 0 8px;
    font-size: 32px;
    font-weight: 700;
    letter-spacing: -0.5px;
  }
  header p {
    margin: 0;
    color: var(--text-soft);
    font-size: 15px;
  }
  header p strong {
    color: var(--accent);
    font-weight: 600;
  }
  .filters {
    max-width: 1280px;
    margin: 24px auto 0;
    padding: 0 32px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
  }
  .chip {
    padding: 8px 16px;
    border-radius: var(--radius-btn);
    background: #fff;
    border: 1px solid var(--border);
    font-size: 13px;
    color: var(--text);
    cursor: pointer;
    transition: all 0.18s ease;
    user-select: none;
  }
  .chip:hover { border-color: var(--accent); color: var(--accent); }
  .chip.active {
    background: var(--accent);
    border-color: var(--accent);
    color: #fff;
  }
  .count {
    text-align: center;
    color: var(--text-soft);
    font-size: 13px;
    margin: 16px 0 24px;
  }
  main {
    max-width: 1280px;
    margin: 0 auto;
    padding: 0 32px 64px;
  }
  .grid {
    column-count: 4;
    column-gap: 20px;
  }
  @media (max-width: 1100px) { .grid { column-count: 3; } }
  @media (max-width: 780px)  { .grid { column-count: 2; } }
  @media (max-width: 480px)  { .grid { column-count: 2; column-gap: 12px; } }
  .card {
    display: inline-block;
    width: 100%;
    margin: 0 0 20px;
    background: var(--card);
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: var(--shadow);
    cursor: pointer;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
    will-change: transform;
    break-inside: avoid;
  }
  .card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 32px rgba(0,0,0,0.10);
  }
  .card .cover-wrap {
    position: relative;
    width: 100%;
    background: #f0f0f0;
    overflow: hidden;
    line-height: 0;
  }
  .card img {
    width: 100%;
    height: auto;
    display: block;
  }
  .badge {
    position: absolute;
    top: 10px;
    left: 10px;
    padding: 5px 10px;
    border-radius: var(--radius-btn);
    background: rgba(0,0,0,0.65);
    color: #fff;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.5px;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
  }
  .card .title {
    padding: 14px 16px 16px;
    font-size: 15px;
    font-weight: 600;
    color: var(--text);
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .empty {
    text-align: center;
    color: var(--text-soft);
    padding: 64px 0;
    font-size: 14px;
  }

  /* Modal */
  .modal {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.7);
    display: none;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    padding: 32px;
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
  }
  .modal.open { display: flex; }
  .modal-inner {
    background: #fff;
    border-radius: var(--radius);
    max-width: 900px;
    width: 100%;
    max-height: 90vh;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px;
    box-shadow: 0 24px 64px rgba(0,0,0,0.3);
    position: relative;
  }
  .modal-close {
    position: absolute;
    top: 12px;
    right: 12px;
    width: 36px;
    height: 36px;
    border: none;
    background: rgba(0,0,0,0.06);
    border-radius: 50%;
    cursor: pointer;
    font-size: 18px;
    color: var(--text);
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.18s;
  }
  .modal-close:hover { background: rgba(0,0,0,0.12); }
  .modal img {
    max-width: 100%;
    max-height: 70vh;
    border-radius: 10px;
    object-fit: contain;
    background: #f6f6f6;
  }
  .modal-title {
    margin: 20px 0 6px;
    font-size: 22px;
    font-weight: 700;
    text-align: center;
  }
  .modal-code {
    color: var(--accent);
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 1px;
    margin-bottom: 12px;
  }
  .modal-hint {
    color: var(--text-soft);
    font-size: 13px;
    text-align: center;
    background: var(--accent-soft);
    padding: 10px 16px;
    border-radius: var(--radius-btn);
    margin-top: 4px;
  }
  .modal-hint strong { color: var(--accent); }

  @media (max-width: 640px) {
    header { padding: 32px 20px 20px; }
    header h1 { font-size: 24px; }
    main { padding: 0 16px 48px; }
    .filters { padding: 0 16px; }
    .card .title { font-size: 13px; padding: 10px 12px 12px; }
    .badge { font-size: 11px; padding: 4px 8px; }
  }
</style>
</head>
<body>
  <header>
    <h1>Tada 风格库</h1>
    <p>看到喜欢的风格，把<strong>编号</strong>发给我们就行</p>
  </header>

  <div class="filters" id="filters"></div>
  <div class="count" id="count"></div>

  <main>
    <div class="grid" id="grid"></div>
  </main>

  <div class="modal" id="modal">
    <div class="modal-inner" id="modalInner">
      <button class="modal-close" id="modalClose" aria-label="关闭">×</button>
      <img id="modalImg" alt="">
      <div class="modal-title" id="modalTitle"></div>
      <div class="modal-code" id="modalCode"></div>
      <div class="modal-hint">想用这个风格？把编号 <strong id="modalCodeHint"></strong> 发给 Tada 团队即可</div>
    </div>
  </div>

<script>
const DATA = /*__DATA__*/null;
const STYLES = DATA.styles;
const CATEGORIES = DATA.categories;
const activeCats = new Set();

const filtersEl = document.getElementById('filters');
const gridEl = document.getElementById('grid');
const countEl = document.getElementById('count');
const modal = document.getElementById('modal');
const modalImg = document.getElementById('modalImg');
const modalTitle = document.getElementById('modalTitle');
const modalCode = document.getElementById('modalCode');
const modalCodeHint = document.getElementById('modalCodeHint');

function renderFilters() {
  const allChip = document.createElement('div');
  allChip.className = 'chip active';
  allChip.textContent = '全部';
  allChip.dataset.cat = '';
  allChip.addEventListener('click', () => {
    activeCats.clear();
    updateFilterUI();
    renderGrid();
  });
  filtersEl.appendChild(allChip);

  CATEGORIES.forEach(cat => {
    const chip = document.createElement('div');
    chip.className = 'chip';
    chip.textContent = cat;
    chip.dataset.cat = cat;
    chip.addEventListener('click', () => {
      if (activeCats.has(cat)) activeCats.delete(cat);
      else activeCats.add(cat);
      updateFilterUI();
      renderGrid();
    });
    filtersEl.appendChild(chip);
  });
}

function updateFilterUI() {
  filtersEl.querySelectorAll('.chip').forEach(c => {
    const cat = c.dataset.cat;
    if (cat === '') c.classList.toggle('active', activeCats.size === 0);
    else c.classList.toggle('active', activeCats.has(cat));
  });
}

function renderGrid() {
  const filtered = activeCats.size === 0
    ? STYLES
    : STYLES.filter(s => s.categories.some(c => activeCats.has(c)));

  countEl.textContent = `共 ${filtered.length} 个风格`;
  gridEl.innerHTML = '';

  if (filtered.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = '没有匹配的风格';
    gridEl.appendChild(empty);
    return;
  }

  const frag = document.createDocumentFragment();
  filtered.forEach(s => {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <div class="cover-wrap">
        <img src="${s.thumb}" alt="${escapeHtml(s.title)}" loading="lazy" decoding="async">
        <div class="badge">${s.code}</div>
      </div>
      <div class="title">${escapeHtml(s.title)}</div>
    `;
    card.addEventListener('click', () => openModal(s));
    frag.appendChild(card);
  });
  gridEl.appendChild(frag);
}

function openModal(s) {
  modalImg.src = s.cover;
  modalImg.alt = s.title;
  modalTitle.textContent = s.title;
  modalCode.textContent = s.code;
  modalCodeHint.textContent = s.code;
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  modal.classList.remove('open');
  document.body.style.overflow = '';
}

modal.addEventListener('click', (e) => {
  if (e.target === modal) closeModal();
});
document.getElementById('modalClose').addEventListener('click', closeModal);
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeModal();
});

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

renderFilters();
renderGrid();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    build()
