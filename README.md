# Tada 风格库（客户版）

给客户用的风格选择网页。客户看到喜欢的风格，把编号（如 `#001`）发给 Tada 团队即可。

## 在线预览

部署到 GitHub Pages 后访问：`https://<your-name>.github.io/<repo>/`

## 开发

```bash
# 重新生成（会增量下载新增封面 + 重写 index.html）
python3 build.py

# 本地预览
python3 -m http.server 4567
# 打开 http://localhost:4567
```

依赖：`Pillow`、`requests`

## 数据来源

`build.py` 从 `../workflow/backend/prompt_library/style_items.v1.json` 读 149 条风格，
缩略图自动下载并压成 600px 宽 webp 存到 `thumbs/`。

## 更新风格

1. 在 workflow 项目里更新 `style_items.v1.json`
2. 重跑 `python3 build.py`
3. `git add . && git commit && git push`，GitHub Pages 自动更新

## 部署到 GitHub Pages

1. 在 GitHub 新建一个仓库（公开或私有都行，私有需要 GitHub Pro）
2. `git init && git add . && git commit -m "init"`
3. `git remote add origin git@github.com:<your-name>/<repo>.git`
4. `git push -u origin main`
5. 仓库 Settings → Pages → Source 选 `main` 分支根目录 → Save
6. 等 1 分钟，访问 `https://<your-name>.github.io/<repo>/`
