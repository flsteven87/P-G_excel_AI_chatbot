# 🚀 Excel AI Chatbot - Zeabur Production Deployment Guide

## 📋 目錄
- [架構概覽](#架構概覽)
- [前置需求](#前置需求)
- [部署步驟](#部署步驟)
- [環境變數配置](#環境變數配置)
- [關鍵技術決策](#關鍵技術決策)
- [監控與健康檢查](#監控與健康檢查)
- [故障排除](#故障排除)
- [效能優化](#效能優化)
- [安全最佳實踐](#安全最佳實踐)

---

## 🏗️ 架構概覽

### Service 架構
```
Excel AI Chatbot (Zeabur Project)
├── backend              # FastAPI + vanna.ai + Excel ETL
├── frontend             # React 19 + Vite + shadcn/ui
└── supabase (外部)      # PostgreSQL + Storage + Auth
```

### 核心技術棧
**後端**:
- FastAPI 0.115.0 (Python 3.11)
- vanna.ai (NL→SQL AI Agent)
- ChromaDB (向量存儲，持久化至 Zeabur Volume)
- pandas/pyarrow (Excel 處理)
- Supabase (Postgres + Storage)

**前端**:
- React 19.1.1 + TypeScript 5.8.3
- Vite 7.1.2 (構建工具)
- Nginx Alpine (生產伺服器)

---

## ✅ 前置需求

### 1. Supabase 專案設置
- [ ] 建立 Supabase 專案
- [ ] 執行資料庫 migrations (如有)
- [ ] 配置 Storage bucket: `user-uploads`
- [ ] 取得 credentials:
  - `SUPABASE_URL`
  - `SUPABASE_ANON_KEY`
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `DATABASE_URL` (直連 PostgreSQL)

### 2. AI Service API Keys
- [ ] vanna.ai API Key: https://vanna.ai/dashboard
- [ ] OpenAI API Key: https://platform.openai.com/api-keys

### 3. 安全性準備
```bash
# 生成 SECRET_KEY (至少 32 字符)
openssl rand -base64 32
```

### 4. Git Repository
- [ ] 確保代碼已推送至 Git (GitHub/GitLab/Bitbucket)
- [ ] 確認 `.gitignore` 已排除 `.env`, `vanna_db/`, `chromadb_data/`

---

## 🚢 部署步驟

### Step 1: 建立 Zeabur Project
1. 前往 [Zeabur Dashboard](https://zeabur.com)
2. 點擊 "New Project"
3. 選擇專案名稱：`excel-ai-chatbot`

---

### Step 2: 部署後端服務 (Backend)

#### 2.1 建立 Git Service
1. 在 Zeabur Project 中點擊 "Add Service" → "Git Service"
2. 連接 Git repository
3. **重要**: 設定 Root Directory = `/backend`
4. Framework: Auto-detected (Python)
5. Build: Docker (自動偵測 Dockerfile)

#### 2.2 配置環境變數
複製 `/backend/.env.zeabur` 內容到 Zeabur Environment Variables，**必須設定**:

```bash
# === Core Infrastructure ===
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres

# === AI Services ===
VANNA_API_KEY=vn-...
OPENAI_API_KEY=sk-...
VANNA_MODEL_NAME=excel-chatbot-prod

# === Application ===
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
PORT=8080

# === Security ===
SECRET_KEY=[your-generated-32-char-key]

# === CORS (待前端部署後更新) ===
CORS_ORIGINS=https://your-frontend.zeabur.app
```

#### 2.3 設置 Persistent Volume (關鍵!)
**ChromaDB 數據持久化配置**:
1. 在 Backend Service 設定中找到 "Volumes"
2. 點擊 "Add Volume"
3. 配置:
   - Mount Path: `/data/vanna_db`
   - Size: 建議至少 1GB
   - 確保環境變數 `CHROMADB_PERSIST_PATH=/data/vanna_db` 已設定

**警告**: 若未配置 Volume，vanna.ai 訓練數據會在每次部署時丢失！

#### 2.4 部署與驗證
1. 點擊 "Deploy" 開始構建 (約 5-10 分鐘)
2. 監控 Build Logs 確認:
   - ✅ UV 依賴安裝成功
   - ✅ Excel 處理庫編譯通過 (pandas, openpyxl)
   - ✅ ChromaDB 初始化完成
3. 取得 Backend URL: `https://[backend-service].zeabur.app`
4. 驗證健康檢查:
   ```bash
   curl https://[backend-service].zeabur.app/health
   # 預期: {"status":"healthy","version":"0.1.0",...}
   ```

---

### Step 3: 部署前端服務 (Frontend)

#### 3.1 建立 Git Service
1. 在同一個 Zeabur Project 中點擊 "Add Service" → "Git Service"
2. 連接相同的 Git repository
3. **重要**: 設定 Root Directory = `/frontend`
4. Framework: Auto-detected (Vite)
5. Build: Docker (自動偵測 Dockerfile)

#### 3.2 配置環境變數
複製 `/frontend/.env.zeabur` 內容，**替換實際值**:

```bash
# Backend API URL (使用 Step 2.4 取得的 URL)
VITE_API_URL=https://[backend-service].zeabur.app

# Supabase (與後端相同的 anon key)
VITE_SUPABASE_URL=https://xxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...
```

**安全警告**: 前端**絕不可**包含 `SUPABASE_SERVICE_ROLE_KEY`！

#### 3.3 部署與驗證
1. 點擊 "Deploy" 開始構建 (約 3-5 分鐘)
2. 監控 Build Logs 確認:
   - ✅ npm 依賴安裝成功
   - ✅ TypeScript 編譯通過
   - ✅ Vite build 完成
   - ✅ Nginx 配置正確
3. 取得 Frontend URL: `https://[frontend-service].zeabur.app`
4. 訪問前端驗證介面正常

#### 3.4 更新後端 CORS
回到 Backend Service 環境變數，更新:
```bash
CORS_ORIGINS=https://[frontend-service].zeabur.app
```
重新部署後端以應用變更。

---

### Step 4: Supabase CORS 配置
在 Supabase Dashboard 中:
1. 前往 Settings → API → CORS Configuration
2. 新增允許的 origins:
   ```
   https://[frontend-service].zeabur.app
   https://[backend-service].zeabur.app
   ```

---

### Step 5: 整合測試

#### 5.1 功能驗證清單
- [ ] 前端可正常訪問
- [ ] 後端健康檢查通過: `GET /health`
- [ ] Excel 上傳功能正常 (測試小檔案 <5MB)
- [ ] ETL Pipeline 執行成功
- [ ] 自然語言查詢可生成 SQL
- [ ] vanna.ai SQL 執行返回結果
- [ ] 前端可正常顯示表格/圖表

#### 5.2 端到端測試流程
```bash
# 1. 測試後端直接調用
curl -X POST https://[backend].zeabur.app/api/v1/files/upload \
  -F "file=@test.xlsx"

# 2. 測試 vanna.ai SQL 生成
curl -X POST https://[backend].zeabur.app/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"顯示前10筆資料","dataset":"test_table"}'

# 3. 前端手動測試
# 訪問 https://[frontend].zeabur.app
# 上傳 Excel → 執行查詢 → 驗證結果
```

#### 5.3 日誌檢查
在 Zeabur Dashboard 查看:
- Backend Logs: 確認 vanna.ai 初始化成功
- 檢查 ChromaDB 連接狀態
- 驗證 Supabase 連接正常

---

## 🔧 環境變數配置

### Backend 完整配置
參考 `/backend/.env.zeabur`

**Category A: 核心基礎設施 (必須)**
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL`
- `VANNA_API_KEY`, `OPENAI_API_KEY`

**Category B: 應用配置 (必須)**
- `ENVIRONMENT=production`, `DEBUG=False`, `PORT=8080`
- `VANNA_MODEL_NAME`, `LOG_LEVEL`

**Category C: 安全性 (必須)**
- `SECRET_KEY` (32+ chars)
- `CORS_ORIGINS`
- `STATEMENT_TIMEOUT_MS=15000`
- `DEFAULT_QUERY_LIMIT=1000`

**Category D: 存儲 (關鍵)**
- `CHROMADB_PERSIST_PATH=/data/vanna_db`
- `STORAGE_BUCKET=user-uploads`

### Frontend 完整配置
參考 `/frontend/.env.zeabur`

**必要變數**:
- `VITE_API_URL` (指向後端 Zeabur URL)
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY` (僅 anon key!)

---

## 💡 關鍵技術決策

### 1. ChromaDB 持久化策略
**問題**: Zeabur 容器是 ephemeral，預設會丟失數據

**短期方案 (已實施)**:
- 使用 Zeabur Volumes 掛載 `/data/vanna_db`
- `CHROMADB_PERSIST_PATH` 環境變數控制存儲路徑

**長期方案 (建議 2-3 週內實施)**:
- 遷移至 Supabase pgvector extension
- 優勢: 完全無狀態、高可用、與現有資料庫整合

### 2. Excel 處理記憶體管理
**挑戰**: 大 Excel 檔案可能導致 OOM

**實施措施**:
- `MAX_FILE_SIZE_MB=100` 嚴格限制
- pandas `chunksize` 分塊處理 (如需要)
- Zeabur Resources: 建議配置至少 1GB RAM

### 3. vanna.ai 初始化時間
**問題**: 冷啟動時 vanna 初始化需要 30-60 秒

**解決方案**:
- Dockerfile `HEALTHCHECK --start-period=60s`
- 首次請求可能較慢 (預期行為)
- 可選: 實施 warmup endpoint

---

## 📊 監控與健康檢查

### 內建健康端點
```bash
# 系統健康
GET /health
# Response: {"status":"healthy","timestamp":...,"version":"0.1.0"}

# API 文檔 (僅在 DEBUG=True 時可用)
GET /docs
```

### Zeabur 監控功能
- **Logs**: 實時日誌查看 (Backend/Frontend)
- **Metrics**: CPU、記憶體、網路使用量
- **Uptime**: 自動健康監控

### 推薦監控指標
- 後端響應時間 (P95 < 5s)
- Excel 上傳成功率 (> 95%)
- vanna.ai SQL 生成成功率 (> 90%)
- ChromaDB 存儲使用量

---

## 🚨 故障排除

### 常見問題 1: ChromaDB 數據丟失
**症狀**: 每次部署後 vanna 訓練數據消失

**解決方案**:
1. 確認 Zeabur Volume 已正確掛載至 `/data/vanna_db`
2. 檢查環境變數 `CHROMADB_PERSIST_PATH=/data/vanna_db`
3. 查看 logs 確認 ChromaDB 使用正確路徑:
   ```
   [INFO] ChromaDB initialized at: /data/vanna_db
   ```

### 常見問題 2: vanna.ai 初始化超時
**症狀**: Backend health check 失敗，logs 顯示 vanna 初始化中

**解決方案**:
1. 確認 `OPENAI_API_KEY` 和 `VANNA_API_KEY` 正確
2. 檢查網路連接至 OpenAI/vanna.ai API
3. 等待 60 秒後重試 (首次啟動需要時間)

### 常見問題 3: Excel 處理失敗
**症狀**: 上傳 Excel 後顯示 500 錯誤

**可能原因與排查**:
```bash
# 1. 檔案過大
# 檢查: MAX_FILE_SIZE_MB 設定
# 測試: 使用 <5MB 小檔案

# 2. 編碼問題
# 確認: Excel 是否為 .xlsx 格式 (非 .xls)

# 3. 記憶體不足
# Zeabur Dashboard: 查看 Memory 使用量
# 解決: 升級 Resources 或降低 MAX_FILE_SIZE_MB
```

### 常見問題 4: CORS 錯誤
**症狀**: 前端 Console 顯示 CORS policy 錯誤

**解決方案**:
1. 確認後端 `CORS_ORIGINS` 包含前端 URL
2. 確認 Supabase CORS 設定包含前端/後端 URL
3. 清除瀏覽器快取重試

### 常見問題 5: SQL 執行失敗
**症狀**: vanna 生成 SQL 但執行時錯誤

**排查步驟**:
```bash
# 1. 檢查 DATABASE_URL 格式
postgresql+asyncpg://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres

# 2. 驗證 Supabase 連接
curl https://[backend].zeabur.app/api/v1/debug/database

# 3. 確認 SQL 安全限制
# STATEMENT_TIMEOUT_MS=15000 (防止慢查詢)
# DEFAULT_QUERY_LIMIT=1000 (限制結果數)
```

---

## ⚡ 效能優化

### 1. 前端優化
**已實施** (透過 Nginx 配置):
- ✅ Gzip 壓縮 (6 級)
- ✅ 靜態資源快取 (1 年)
- ✅ CDN-ready (Zeabur 自動)

**建議優化**:
- 實施 React Code Splitting
- 使用 React.lazy() 延遲載入重型組件

### 2. 後端優化
**已實施**:
- ✅ ChromaDB 向量快取
- ✅ SQL 查詢限制 (LIMIT, TIMEOUT)

**建議優化**:
```python
# 1. Redis 查詢結果快取 (選配)
# 在 Zeabur 新增 Redis Service
# 更新 REDIS_URL 環境變數

# 2. pandas 分塊處理
df = pd.read_excel(file, chunksize=5000)

# 3. Supabase 連接池調整
# DATABASE_URL 加入參數: ?pool_size=20&max_overflow=10
```

### 3. 資料庫優化
在 Supabase 中:
- 建立常用查詢欄位索引
- 考慮 materialized views (彙總資料)
- 啟用 pg_stat_statements 追蹤慢查詢

---

## 🔒 安全最佳實踐

### 1. 機密管理
- ✅ **絕不** commit `.env` 檔案至 Git
- ✅ 使用 Zeabur Environment Variables (加密存儲)
- ✅ `SECRET_KEY` 至少 32 字符，使用 `openssl rand -base64 32` 生成
- ✅ 前端**僅**使用 `SUPABASE_ANON_KEY`，絕不包含 `SERVICE_ROLE_KEY`

### 2. SQL 注入防護
**已實施** (在 `app/core/config.py`):
```python
ALLOWED_SQL_OPERATIONS = ["SELECT", "WITH"]
BLOCKED_SQL_KEYWORDS = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", ...]
```

### 3. 資源保護
- ✅ `STATEMENT_TIMEOUT_MS=15000` (防止慢查詢)
- ✅ `DEFAULT_QUERY_LIMIT=1000` (限制結果數)
- ✅ `MAX_FILE_SIZE_MB=100` (防止大檔案攻擊)

### 4. CORS 策略
```python
# 生產環境僅允許特定 origins
CORS_ORIGINS=https://your-frontend.zeabur.app,https://custom-domain.com

# 絕不使用 CORS_ORIGINS=* 在生產環境
```

### 5. Supabase RLS (Row Level Security)
確保所有表格啟用 RLS policies:
```sql
-- 範例: 用戶僅能存取自己的資料
ALTER TABLE user_uploads ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only access own data"
ON user_uploads FOR ALL
USING (auth.uid() = user_id);
```

---

## 📈 部署後檢查清單

### 立即執行 (P0)
- [ ] 後端健康檢查通過
- [ ] 前端可正常訪問
- [ ] CORS 設定正確
- [ ] ChromaDB Volume 已掛載
- [ ] 環境變數已全部配置

### 第一週 (P1)
- [ ] 完整端到端測試
- [ ] 驗證 Excel 上傳/ETL 流程
- [ ] 測試 vanna.ai SQL 生成
- [ ] 監控系統資源使用量
- [ ] 建立基本告警機制

### 第二週 (P2)
- [ ] ChromaDB 備份策略
- [ ] 效能基準測試
- [ ] 壓力測試 (大檔案、並發查詢)
- [ ] 成本優化分析

### 長期規劃 (P3)
- [ ] 遷移 ChromaDB → Supabase pgvector
- [ ] 實施 CDN (如有自定義域名)
- [ ] CI/CD 自動化 (GitHub Actions)
- [ ] A/B Testing 基礎設施

---

## 🔄 CI/CD 自動部署 (選配)

### Zeabur Auto-Deployment
**預設行為**: Git push → 自動觸發部署

**配置步驟**:
1. Zeabur 已自動連接 Git repository
2. 每次 push 至 main branch 自動部署
3. 監控 Deployment Logs 確認成功

### 回滾策略
```bash
# Zeabur Dashboard 中:
1. 進入 Service → Deployments
2. 選擇先前的 Deployment
3. 點擊 "Rollback to this deployment"

# Git-based 回滾:
git revert <commit-hash>
git push origin main
# Zeabur 會自動部署回滾後的版本
```

---

## 📞 支援資源

### 官方文檔
- [Zeabur Docs](https://zeabur.com/docs)
- [Supabase Docs](https://supabase.com/docs)
- [vanna.ai Docs](https://vanna.ai/docs)

### 專案維護
- 前端 Issues: `/frontend` 相關問題
- 後端 Issues: `/backend` 相關問題
- Deployment Issues: 本文檔 troubleshooting section

---

## 🎉 部署成功驗證

當以下所有檢查通過，代表部署成功：

```bash
# ✅ Backend Health
curl https://[backend].zeabur.app/health
# → {"status":"healthy",...}

# ✅ Frontend Access
curl -I https://[frontend].zeabur.app
# → HTTP/2 200

# ✅ vanna.ai Integration
curl -X POST https://[backend].zeabur.app/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{"question":"測試查詢","dataset":"test"}'
# → 返回 SQL 生成結果

# ✅ ChromaDB Persistence
# 重新部署 Backend → 檢查 vanna 訓練數據仍存在
```

**恭喜！您的 Excel AI Chatbot 已成功部署至 Zeabur 生產環境！** 🚀

---

*最後更新: 2025-09-24*
*版本: 1.0.0*
*維護者: P-G Excel AI Chatbot Team*