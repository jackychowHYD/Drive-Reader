# 📁 Google Drive 體系文檔預覽與下載系統 (Drive Reader)

一個基於 Python 和 Streamlit 開發的 Web 應用程式，結合 Google Drive API 與 Service Account（服務帳號），提供簡潔直覺的介面，用於預覽與下載 Google Drive 上的各類 ISO 體系與標準文檔。

---

## ✨ 功能特點

- 🤖 **免登入驗證**：使用 Google Cloud Service Account 進行背景授權，無需使用者手動透過 OAuth 登入。
- 📂 **自動動態載入**：自動搜尋並列出服務帳號擁有存取權限的所有 Google Drive 資料夾。
- 👁️ **線上檔案預覽**：支援線上直接預覽 Google Doc、PDF 及各式常見文件。
- ⬇️ **一鍵快捷下載**：提供下載按鈕，並自動將 Google 原生文件（Docs / Sheets）轉換為 PDF / Excel 格式下載。

---

## 🛠️ 技術堆疊 (Tech Stack)

- **前端/ Web 框架**：Streamlit
- **數據處理**：Pandas
- **API 整合**：Google Drive API v3 (`google-api-python-client`, `google-auth`)

---

## 🚀 本地開發與執行指南 (Local Setup)

### 1. 複製專案 (Clone Repository)

```bash
git clone [https://github.com/你的用戶名/drive-reader.git](https://github.com/你的用戶名/drive-reader.git)
cd drive-reader