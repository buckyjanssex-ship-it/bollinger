# 美股布林通道下軌篩選器

GitHub Actions 每小時自動掃描，結果發布到 GitHub Pages，手機直接看結果。

## 設定步驟（10 分鐘）

### 1. Fork / 建立 Repo
把這個資料夾的檔案上傳到你的 GitHub 新 Repo（Public）。

### 2. 設定 API Key Secret
- Repo → Settings → Secrets and variables → Actions → New repository secret
- Name: `TD_API_KEY`
- Value: 你的 Twelve Data API Key（[免費申請](https://twelvedata.com/register)）

### 3. 開啟 GitHub Pages
- Repo → Settings → Pages
- Source: `Deploy from a branch`
- Branch: `main` / `(root)`
- Save

### 4. 手動觸發第一次掃描
- Repo → Actions → Bollinger Band Scan → Run workflow

### 5. 書籤你的網址
```
https://<你的GitHub帳號>.github.io/<Repo名稱>/
```

之後 GitHub Actions 每小時整點自動掃描，你只要打開網址就看到最新結果。

## 檔案說明
| 檔案 | 說明 |
|------|------|
| `scan.py` | 掃描腳本（GitHub Actions 執行） |
| `data.json` | 掃描結果（自動更新） |
| `index.html` | 前端顯示頁面 |
| `.github/workflows/scan.yml` | 排程設定（每小時） |
