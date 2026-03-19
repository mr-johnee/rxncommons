# RxnCommons 系统整体设计方案

> 版本：v1.0 | 日期：2026-03-13

---

## 目录

1. [项目概述](#1-项目概述)
2. [用户分类与权限](#2-用户分类与权限)
3. [技术架构](#3-技术架构)
4. [数据库设计](#4-数据库设计)
5. [文件存储方案](#5-文件存储方案)
6. [后端 API 设计](#6-后端-api-设计)
7. [前端框架与页面总览](#7-前端框架与页面总览)
8. [各页面详细设计](#8-各页面详细设计)
9. [页面跳转逻辑](#9-页面跳转逻辑)
10. [安全策略（上线必做）](#10-安全策略上线必做)
11. [部署方案](#11-部署方案)

---

## 1. 项目概述

### 1.1 平台定位

RxnCommons 是一个面向化学研究社区的**化学反应数据集共享平台**，类似 Kaggle 但专注于化学反应数据。

### 1.2 核心原则

| 原则 | 说明 |
|------|------|
| 数据原始性 | 平台不修改用户上传的任何数据内容 |
| 信息透明 | 元信息、Tag、列说明公开展示，便于使用者判断 |
| 安全优先 | 默认拒绝、最小权限、后端强校验 |
| 选择权下放 | 通过社区投票与讨论，将数据取舍权交给使用者 |
| 学术严谨 | 版本控制、引用格式、DOI 支持，满足学术引用需求 |

### 1.3 平台功能范围

- 化学反应数据集的上传、存储、检索、下载
- 基于 Tag 的数据集分类与检索
- 社区投票（Upvote）机制
- 数据集版本控制
- 管理员审核与建议推送

---

## 2. 用户分类与权限

### 2.1 用户类型

```
未注册访客
未激活用户（已注册但未验证邮箱，防滥用）
普通注册用户（已验证邮箱）
管理员（后台配置，无公开注册入口）
```

### 2.2 权限矩阵

| 功能 | 未注册访客 | 未激活用户 | 普通用户 | 管理员 |
|------|-----------|-----------|---------|--------|
| 浏览首页 | ✅ | ✅ | ✅ | ✅ |
| 浏览数据集列表 | ✅ | ✅ | ✅ | ✅ |
| 查看数据集详情 | ✅ | ✅ | ✅ | ✅ |
| 下载数据集 | ❌ | ✅ | ✅ | ✅ |
| 上传数据集 | ❌ | ❌ | ✅ | ✅ |
| Upvote | ❌ | ❌ | ✅ | ✅ |
| 参与讨论 | ❌ | ❌ | ✅ | ✅ |
| 管理自己的数据集 | ❌ | ❌ | ✅ | ✅ |
| 查看所有用户数据集（含私有） | ❌ | ❌ | ❌ | ✅ |
| 推送修改建议给用户 | ❌ | ❌ | ❌ | ✅ |
| 下架数据集 | ❌ | ❌ | ❌ | ✅ |
| 用户管理 | ❌ | ❌ | ❌ | ✅ |

---

## 3. 技术架构

### 3.1 整体架构图

```
┌─────────────────────────────────────────────────────────┐
│                        用户浏览器                         │
└──────────────────────────┬──────────────────────────────┘
            │ HTTPS
┌──────────────────────────▼──────────────────────────────┐
│                  Nginx / CDN / WAF 层                    │
│          HTTPS 终止 + 静态资源缓存 + 基础防护             │
└───────────────┬───────────────────────┬─────────────────┘
      │                       │
┌───────────────▼──────────────┐   ┌────▼─────────────────┐
│       前端（Next.js）          │   │   后端 API（FastAPI） │
│ React 组件 + TailwindCSS + SWR │   │ 路由层→业务层→数据层  │
└──────────────────────────────┘   └────┬─────────────────┘
                │
          ┌───────────────┼────────────────┬──────────────────┐
          │               │                │                  │
      ┌────────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐  ┌────────▼────────┐
      │ PostgreSQL    │ │   Redis     │ │   MinIO     │  │ 文件安全扫描服务 │
      │ 主数据 + 搜索读模│ │ 会话/限流/队列 │ │ 对象存储      │  │ （隔离区→正式区）│
      └────────┬──────┘ └──────┬──────┘ └─────────────┘  └─────────────────┘
          │               │
      ┌────────▼────────┐ ┌────▼──────────────┐
      │ Celery Worker   │ │ Scheduler / Beat  │
      │ 解析/预览/清理/投影│ │ 定时巡检/重试/补偿 │
      └─────────────────┘ └───────────────────┘
```

### 3.2 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 14+ | React 框架，SSR/SSG |
| TailwindCSS | 3+ | 样式系统 |
| SWR | 2+ | 数据请求与缓存 |
| Zustand | 4+ | 客户端状态管理 |
| React Table | 8+ | 数据表格渲染 |
| React Dropzone | — | 文件拖拽上传 |

### 3.3 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.110+ | API 框架 |
| SQLAlchemy | 2+ | ORM |
| PostgreSQL | 15+ | 主数据库 |
| pg_trgm / PostgreSQL FTS | — | 标题/Tag 搜索与排序支持（无需单独 ES） |
| Redis | 7+ | 缓存 + 会话 + 限流 + 消息队列 Broker |
| Celery / RQ | — | 异步任务队列（大文件解析、物理文件清理） |
| MinIO | — | 对象存储（兼容 S3） |
| ClamAV | — | 上传文件恶意内容扫描 |
| Pandas / openpyxl | 2+ | CSV 流式处理与 Excel 逐行解析去 OOM 化 |
| python-magic | — | 文件类型检测 |

---

## 4. 数据库设计

### 4.1 核心数据表

#### users（用户表）

```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      VARCHAR(50) UNIQUE NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    institution   VARCHAR(255),
    research_area VARCHAR(255),
    role          VARCHAR(20) DEFAULT 'user',  -- 'user' | 'admin'
    storage_used  BIGINT DEFAULT 0,            -- 单位：字节
    storage_quota BIGINT DEFAULT 5368709120,   -- 默认 5GB（普通用户）
    is_active     BOOLEAN DEFAULT TRUE,
    is_email_verified BOOLEAN DEFAULT FALSE,   -- 邮箱是否已验证（防滥用）
    created_at    TIMESTAMP DEFAULT NOW(),
    last_login    TIMESTAMP
);
```

#### physical_storage_objects（物理存储对象表）

```sql
CREATE TABLE physical_storage_objects (
    file_key        VARCHAR(500) PRIMARY KEY, -- MinIO 持久对象键
    owner_id        UUID NOT NULL REFERENCES users(id),
    file_size       BIGINT NOT NULL,
    ref_count       INTEGER DEFAULT 0,        -- 引用计数（跨版本复用计数）
    upload_status   VARCHAR(20) DEFAULT 'pending', 
    created_at      TIMESTAMP DEFAULT NOW()
);
```
**设计目的**：解决多版本继承同名文件时的“物理防重”与“配额扣减黑洞”。用户 `storage_used` 仅与此表挂钩。为实现用户级别的去重并防止跨用户配额计费混乱，`file_key` 强制采用 `{owner_id}_{sha256}` 规则生成。新版本继承文件时 `ref_count + 1`；当删除历史版本导致 `ref_count = 0` 时，才跨事务异步删除 MinIO 文件并退还配额。

#### datasets（数据集表）

```sql
CREATE TABLE datasets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id        UUID REFERENCES users(id),
    slug            VARCHAR(255) NOT NULL,     -- URL 友好名称（空格→下划线）
    title           VARCHAR(255) NOT NULL,
    description     TEXT NOT NULL,
    source_type     VARCHAR(50),               -- 'lab' | 'literature' | 'patent' | 'database' | 'other'
    source_ref      VARCHAR(500),              -- DOI / 专利号 / 链接
    license         VARCHAR(100),
    dataset_status  VARCHAR(30) DEFAULT 'draft',
    pre_archive_status VARCHAR(30),                 
    status_reason   TEXT,                           
    status_updated_at TIMESTAMP DEFAULT NOW(),
    publish_requested_at TIMESTAMP,                 
    current_version INTEGER DEFAULT 1,
    view_count      INTEGER DEFAULT 0,
    download_count  INTEGER DEFAULT 0,
    upvote_count    INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    deleted_at      TIMESTAMP,                      
    deleted_by      UUID REFERENCES users(id)
);

-- 使用局部唯一索引代替 UNIQUE 约束，允许同一用户在软删除后重新使用原名称（slug）
CREATE UNIQUE INDEX uniq_dataset_slug_active ON datasets(owner_id, slug) WHERE deleted_at IS NULL;

CREATE INDEX idx_datasets_dataset_status ON datasets(dataset_status);
```

说明：`datasets` 不再保留 `visibility` 字段，可见性完全由 `dataset_status` 决定（`published/revision_required/archived` 公开，其余非公开）。

#### dataset_tags（数据集标签表）

```sql
CREATE TABLE dataset_tags (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    tag        VARCHAR(100) NOT NULL,         -- 写入前必须转小写并做正则过滤
    tag_type   VARCHAR(20) DEFAULT 'custom',  -- 'task' | 'field' | 'custom'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(dataset_id, tag)                   -- 防重复冗余标签
);

CREATE INDEX idx_dataset_tags_tag ON dataset_tags(tag);
```

**Tag 使用约定（字段覆盖通过 Tag 表达）**

- `task`：任务类标签，如 `yield_prediction`、`condition_prediction`、`retrosynthesis`
- `field`：字段类标签，如 `has_yield_data`、`has_solvent_data`、`has_ligand_data`
- `custom`：用户自定义标签，如具体反应类型、底物家族、数据来源特征等

#### dataset_authors（数据集作者表）

```sql
CREATE TABLE dataset_authors (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    name       VARCHAR(255) NOT NULL,
    institution VARCHAR(255),
    orcid      VARCHAR(50),
    role       VARCHAR(20) DEFAULT 'co-author',  -- 'first' | 'co-author' | 'corresponding'
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### dataset_versions（版本表）

```sql
CREATE TABLE dataset_versions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id   UUID REFERENCES datasets(id) ON DELETE CASCADE,
    version_num  INTEGER NOT NULL,
    status       VARCHAR(20) DEFAULT 'draft',    -- 'draft' | 'pending_review' | 'published' | 'rejected'
    version_note TEXT,                       -- 草稿阶段可为空；提交上线审核前必须非空
  base_version_num INTEGER,               -- 本版本变更所基于的上一版本号；V1 为空
    download_count INTEGER DEFAULT 0,        -- 该版本下载次数
    metadata_complete BOOLEAN DEFAULT FALSE, -- 服务端校验结果：该版本文件描述/列说明是否全部完成
    change_manifest JSONB,                   -- 相对上一版本的变更清单（固定 JSON schema，见下）
    created_at   TIMESTAMP DEFAULT NOW(),
    created_by   UUID REFERENCES users(id),
    UNIQUE(dataset_id, version_num)
);
```

`change_manifest` JSON schema 约定（前后端统一）：

```json
{
  "files_added": ["reagent_map.xlsx"],
  "files_replaced": ["train_set.csv"],
  "files_removed": [],
  "metadata_changed": ["description", "source_ref"],
  "note": "修正 ligand 命名；新增 500 条反应"
}
```

#### dataset_files（文件逻辑表）

```sql
CREATE TABLE dataset_files (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      UUID NOT NULL REFERENCES dataset_versions(id) ON DELETE CASCADE,
    filename        VARCHAR(500) NOT NULL,
    file_key        VARCHAR(500) NOT NULL REFERENCES physical_storage_objects(file_key),
    description     TEXT,                   -- 文件描述，公开时必填
    row_count       INTEGER,                -- 解析后的行数
    col_count       INTEGER,                -- 解析后的列数
    error_message   TEXT,                   -- 解析或扫描失败时的错误原因
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(version_id, filename)
);
```

#### file_columns（列信息表）

```sql
CREATE TABLE file_columns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id         UUID REFERENCES dataset_files(id) ON DELETE CASCADE,
    column_name     VARCHAR(255) NOT NULL,
    column_index    INTEGER NOT NULL,
    description     TEXT,                   -- 列说明，公开时必填
    null_rate       NUMERIC(5,2),           -- 缺失率 %
    unique_count    INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

**版本继承落库规则（必须）**：

1. 新版本继承旧文件时，创建新的 `dataset_files` 记录（关联到新的 `version_id`），不复用旧 `id`
2. 若文件内容未变化，可复用旧 `file_key`（指向同一对象存储文件），避免重复存储
3. 继承文件时同步复制 `file_columns` 记录，并关联新的 `file_id`
4. 任何版本的文件说明/列说明修改只影响本版本记录，不回写历史版本
5. `version_id` 为版本归属唯一事实来源；所有文件上传、继承、删除动作都必须先解析到目标 `version_id` 后再写入
6. `base_version_num` 必须在创建 V2+ 时写入，用于固定记录该版本的比较基准；即使前端未来展示 change manifest，也不能依赖“现算上一版本”

#### upvotes（投票表）

```sql
CREATE TABLE upvotes (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(dataset_id, user_id)
);
```

#### discussions（讨论表）

```sql
CREATE TABLE discussions (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    user_id    UUID REFERENCES users(id),
    content    TEXT NOT NULL,
    root_id    UUID REFERENCES discussions(id) ON DELETE CASCADE, -- 顶级评论 ID，空则为自身
    parent_id  UUID REFERENCES discussions(id) ON DELETE CASCADE, -- 回复的目标 ID（可以为同级或子级）
    deleted_at TIMESTAMP,                        -- 软删除时间
    deleted_by UUID REFERENCES users(id),        -- 删除人
    created_at TIMESTAMP DEFAULT NOW(),
    edited_at  TIMESTAMP,                        
    updated_at TIMESTAMP DEFAULT NOW()           
);
CREATE INDEX idx_discussions_root_id ON discussions(root_id);
```
**优化点**：引入 `root_id`，避免在无限嵌套场景下采用耗时的 Recursive CTE（递归查询）。所有子回复强制打平关联到其顶层主评论，使查询列表可简化为 `O(1)`，性能更优（类似掘金、知乎的二级评论树设计）。

#### admin_suggestions（管理员建议表）

```sql
CREATE TABLE admin_suggestions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id  UUID REFERENCES datasets(id) ON DELETE CASCADE,
    recipient_user_id UUID REFERENCES users(id), -- 数据集作者（消息接收人）
    admin_id    UUID REFERENCES users(id),
    version_num INTEGER,                  -- 建议针对的数据集版本
    content     TEXT NOT NULL,
    status      VARCHAR(20) DEFAULT 'pending',  -- 'pending' | 'resolved' | 'dismissed'
    is_read     BOOLEAN DEFAULT FALSE,     -- 是否已读
    created_at  TIMESTAMP DEFAULT NOW(),
    read_at     TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_admin_suggestions_recipient_status
    ON admin_suggestions(recipient_user_id, status, is_read);
```

#### dataset_review_requests（上线审核请求表）

```sql
CREATE TABLE dataset_review_requests (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id    UUID REFERENCES datasets(id) ON DELETE CASCADE,
    version_id    UUID NOT NULL REFERENCES dataset_versions(id) ON DELETE CASCADE,
    version_num   INTEGER NOT NULL,                 -- 提交审核的版本号
    requester_id  UUID REFERENCES users(id),        -- 提交人（通常为 owner）
    pre_review_status VARCHAR(30),                  -- 提交审核前的数据集状态（用于驳回时精准回退，如回退到 revision_required）
    status        VARCHAR(20) DEFAULT 'pending',    -- 'pending' | 'approved' | 'rejected' | 'canceled_by_user'
    submit_note   TEXT,                             -- 作者补充说明（可选）
    decision_note TEXT,                             -- 管理员审核意见
    reviewed_by   UUID REFERENCES users(id),
    submitted_at  TIMESTAMP DEFAULT NOW(),
    reviewed_at   TIMESTAMP,
    CONSTRAINT fk_review_requests_dataset_version
        FOREIGN KEY (dataset_id, version_num)
        REFERENCES dataset_versions(dataset_id, version_num)
);

CREATE INDEX idx_review_requests_status_time
    ON dataset_review_requests(status, submitted_at DESC);

CREATE UNIQUE INDEX uniq_review_request_pending_per_dataset
    ON dataset_review_requests(dataset_id)
    WHERE status = 'pending';
```

#### notifications（全站消息通知表）

```sql
CREATE TABLE notifications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    actor_id    UUID REFERENCES users(id),                -- 触发该动作的用户/管理员（可空）
    target_type VARCHAR(50) NOT NULL,                     -- 来源类型：'review_request', 'admin_suggestion', 'discussion', 'system'
    target_id   UUID,                                     -- 关联的业务记录 ID
    title       VARCHAR(255) NOT NULL,                    -- 消息短标题
    content     TEXT,                                     -- 消息具体内容/驳回原因
    is_read     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_recipient ON notifications(recipient_id, is_read, created_at DESC);
```
**设计目的**：目前系统中有回复（discussions）、审核（review_requests）、建议（admin_suggestions）等多处需要通知用户的场景。如果前端每次都要联合查询所有子表来判断未读数或聚合消息列表，会造成不必要的复杂度和性能消耗。本表作为统一消息归档表使用前缀发布-订阅策略（在主逻辑执行通过后触发向此表写入）。

#### dataset_search_documents（检索读模型表）

```sql
CREATE TABLE dataset_search_documents (
    dataset_id      UUID PRIMARY KEY REFERENCES datasets(id) ON DELETE CASCADE,
    owner_username  VARCHAR(50) NOT NULL,
    slug            VARCHAR(255) NOT NULL,
    title           VARCHAR(255) NOT NULL,
    title_normalized VARCHAR(255) NOT NULL,
    searchable_text TEXT NOT NULL,
    task_tags       TEXT[] DEFAULT '{}',
    field_tags      TEXT[] DEFAULT '{}',
    custom_tags     TEXT[] DEFAULT '{}',
    source_type     VARCHAR(50),
    dataset_status  VARCHAR(30) NOT NULL,
    current_version INTEGER NOT NULL,
    total_rows      INTEGER DEFAULT 0,         -- 当前已发布版本的总行数（所有文件 row_count 之和），用于 P02 数据规模筛选
    total_file_size BIGINT DEFAULT 0,           -- 当前已发布版本的总文件大小（字节），用于卡片展示
    description     TEXT DEFAULT '',             -- 数据集描述原文（冗余存储），用于列表 API 直接返回
    created_at      TIMESTAMP NOT NULL,          -- 数据集创建时间，用于 P02「最新上传」排序
    upvote_count    INTEGER DEFAULT 0,
    download_count  INTEGER DEFAULT 0,
    view_count      INTEGER DEFAULT 0,
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dataset_search_documents_status
  ON dataset_search_documents(dataset_status);
CREATE INDEX idx_dataset_search_documents_title_trgm
  ON dataset_search_documents USING GIN (title_normalized gin_trgm_ops);
CREATE INDEX idx_dataset_search_documents_searchable_text_trgm
  ON dataset_search_documents USING GIN (searchable_text gin_trgm_ops);
```

用途说明：

- P01 精选卡片、P02 列表筛选、站内搜索统一读取 `dataset_search_documents`，避免线上列表页每次拼接 `datasets + dataset_tags + versions + counters` 的多表热点查询
- 该表由异步投影任务维护：数据集元信息、Tag、状态、计数变化后增量更新
- v1 阶段不强制引入 Elasticsearch；先用 PostgreSQL 读模型 + trigram/FTS 即可支撑中等规模站点

**投影触发策略（必须）**：

| 事件 | 投影方式 | 可接受延迟 |
|------|----------|------------|
| 数据集创建 / 元信息更新 | 事务提交后发异步任务 | 5 秒内 |
| Tag 变更 | 事务提交后发异步任务 | 5 秒内 |
| 审核状态变更 / 归档 / 下架 / 恢复 | 事务提交后发异步任务 | 5 秒内 |
| Upvote / 取消 Upvote | 事务提交后发异步任务 | 10 秒内 |
| download-all 计数变化 | 事务提交后发异步任务 | 30 秒内 |
| view_count 变化 | 定时批量回刷读模型 | 5 分钟内 |

说明：P02 列表页与搜索页允许读模型存在短暂最终一致性延迟；详情页中的最新状态与计数以主表查询结果为准。

#### auth_refresh_tokens（Refresh Token 表）

```sql
CREATE TABLE auth_refresh_tokens (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash    VARCHAR(255) NOT NULL,        -- 只存 hash，不存明文 token
    issued_at     TIMESTAMP DEFAULT NOW(),
    expires_at    TIMESTAMP NOT NULL,
    revoked_at    TIMESTAMP,
    issued_ip     VARCHAR(64),
    user_agent    VARCHAR(500)
);

CREATE INDEX idx_auth_refresh_tokens_user_id ON auth_refresh_tokens(user_id);
```

#### security_audit_logs（安全审计日志表）

```sql
CREATE TABLE security_audit_logs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type    VARCHAR(100) NOT NULL,      -- login_failed / token_revoked / admin_action / download_denied 等
    actor_user_id UUID REFERENCES users(id),
    target_type   VARCHAR(50),                -- 'dataset' | 'file' | 'user' | 'auth'
    target_id     UUID,
    ip_addr       VARCHAR(64),
    user_agent    VARCHAR(500),
    detail        JSONB,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_security_audit_logs_event_type ON security_audit_logs(event_type);
CREATE INDEX idx_security_audit_logs_created_at ON security_audit_logs(created_at);
```

### 4.2 数据集状态维护（必须）

为避免“可见性”和“治理动作”混在一起，数据集状态单独维护在 `datasets.dataset_status`：

平台约束：严禁重新引入独立 `visibility` 字段，所有对外可见性判断统一走 `dataset_status`。

- `draft`：草稿（默认）；仅作者可见
- `pending_review`：待审核；作者已提交上线申请，等待管理员审核
- `published`：已发布；允许公开展示与下载
- `revision_required`：待修订；保持公开可见和可下载，但作者需处理管理员建议
- `archived`：归档；作者主动停止维护，仍可浏览和下载，但关闭 Upvote 与讨论
- `takedown`：已下架；管理员主动隐藏，仅作者与管理员可见，下载入口关闭（**不回收物理空间，支持恢复**）
- `deleted`：已删除；用户主动删除的软删除记录（**回收配额，不可恢复，前台彻底隐藏**）

**状态迁移规则**：

1. 新建数据集并保存草稿：`draft`
2. 作者点击「提交上线审核」：`draft/revision_required -> pending_review`（同时在 `dataset_review_requests.pre_review_status` 记录提交前状态，如 `draft` 或 `revision_required`）
3. 管理员审核通过：`pending_review -> published`
4. 管理员驳回：`pending_review -> pre_review_status`（回退到提交审核前的状态，防止此前已发布的大基座记录意外掉线隐藏，并写入驳回原因）
5. 管理员推送关键建议（已发布数据）：`published -> revision_required`
6. 作者创建修订版本并再次提交：`revision_required -> pending_review`
7. 作者主动归档：`published/revision_required -> archived`，并写入 `pre_archive_status`
8. 作者取消归档：`archived -> pre_archive_status`（为空时回退到 `published`）
9. 管理员下架：`* -> takedown`
10. 管理员恢复：`takedown -> draft` 或 `takedown -> published`（按审核结果）
11. 用户删除：`* (当前非 takedown 状态) -> deleted`

说明：数据集级 `dataset_status` 反映的是当前已发布/已提交版本的暴露状态。新版本草稿的 `dataset_versions.status=draft` 独立存在，不影响数据集级状态；只有在提交其审核时，才会触发数据集级的 `pending_review` 变更，发布后触发 `published`，确保处于线上的基座数据在此期间不受干扰。

**前端展示约定**：

- P03 头部显示状态徽标（`pending_review`/`published`/`revision_required`/`archived`/`takedown`）
- P07「我的数据集」列表显示状态，优先展示 `dataset_status`
- `revision_required`：访客可见并可下载；仅作者/管理员看到“待处理建议”提示
- `archived`：访客可见并可下载；隐藏 Upvote 按钮、关闭讨论输入框
- `archived`：默认可被 P02 搜索与列表检索到，卡片与详情页需显示“已归档”状态徽标；P02 提供状态筛选项供用户只看或排除归档数据集

### 4.3 数据集链接与分享规则（必须）

每个数据集在首次保存时即生成稳定 slug，并对应固定主链接：

- 主链接（最新版本）：`/datasets/{owner}/{slug}`
- 版本链接（固定版本）：`/datasets/{owner}/{slug}/v{n}`

**访问与分享规则**：

1. `draft/pending_review/takedown`：链接仅作者与管理员可访问；其他用户访问返回 403/404
2. `published/revision_required/archived`：主链接可公开分享，默认指向最新已发布版本
3. 历史复现实验/论文引用使用版本链接 `v{n}`，避免“最新版漂移”
4. 页面提供一键复制：
- `复制数据集链接`（主链接）
- `复制当前版本链接`（v{n}）

### 4.4 Slug 生成规则（必须）

为保证 URL 稳定与可读，slug 规则统一如下：

1. 首次保存时由标题生成 slug；后续标题修改不影响 slug（链接永久稳定）
2. 统一小写；仅保留 `a-z`、`0-9`、`_`
3. 空格和分隔符（空格、`-`、`.`）统一替换为 `_`
4. 其他字符（如 `/`、`#`、`%`、中文符号）移除或替换为 `_`，并合并连续 `_`
5. 首尾 `_` 去除；最大长度 100 字符（超长截断）
6. 若清洗后为空，回退为 `dataset_{short_id}`
7. 同一 `owner` 下冲突时追加后缀（如 `_2`、`_3`）

### 4.5 数据集删除与下架语义（必须分离）

为避免管理员下架后恢复（Restore）时发生数据与配额冲突，对记录的隐藏需分为两种不同行为：

1. **用户主动删除 (Delete `DELETE /api/datasets/{owner}/{slug}`)**
   - 写入 `datasets.deleted_at` 与 `datasets.deleted_by`，并将 `dataset_status` 置为 `deleted`。
   - 前台列表与详情彻底隐藏（不在任何状态列表展示）。
   - **配额操作**：立即触发数据库级原子操作回收占用配额（`UPDATE users SET storage_used = storage_used - :size`）。
   - **文件清理**：软删除同时将包含所有 MinIO 物理文件的清理任务打入后端离线异步队列（Celery/RQ）去执行。
   - **审核清理**：如果当前处于 `pending_review` 状态，自动回写对应的 `dataset_review_requests` 置为 `canceled_by_user` 以避免悬挂等待。

2. **管理员下架 (Takedown `PUT /api/admin/datasets/{id}/takedown`)**
   - 将 `dataset_status` 置为 `takedown`（不填写 `deleted_at`）。
   - 仅对公众隐藏，作者/管理员仍可见，但不可正常下载。
   - **配额操作**：**不清理**物理文件，**不退回**配额。
   - **审核清理**：如果当前处于 `pending_review` 状态，同样将对应的 `dataset_review_requests` 置为 `canceled_by_admin` 以避免悬挂等待。
   - 保证后续可以通过 `restore` 安全地恢复回原来的正常状态（`draft` 或 `published`）。

---

## 5. 文件存储方案

### 5.1 存储结构

使用 **MinIO**（兼容 AWS S3 API）进行对象存储，文件路径按以下规则组织：

```
rxncommons-bucket/
├── objects/
│   └── {owner_id}_{sha256}              ← 物理文件：对应 physical_storage_objects.file_key
│                                         ← 同一用户相同内容仅存一份，跨版本复用
├── previews/
│   └── {dataset_id}/
│       └── v{n}/
│           └── {file_id}_preview.json   ← 前 50 行预览缓存，可按需重建
├── archives/
│   └── {dataset_id}/
│       └── v{n}/
│           └── dataset_v{n}.zip         ← 离线打包的全量下载 ZIP
└── avatars/
    └── {user_id}/
        └── avatar.jpg
```

**路径规则说明**：
- 原始文件统一存储在 `objects/` 下，以 `{owner_id}_{sha256}` 为对象键（即 `physical_storage_objects.file_key`），实现同用户去重
- 预览缓存和 ZIP 归档按 `dataset_id + version_num` 组织，与物理文件解耦
- `dataset_files.filename` 仅为逻辑文件名（用户上传时的原始名），不参与 MinIO 对象键生成

### 5.2 存储策略

| 文件类型 | 策略 | 说明 |
|---------|------|------|
| 原始上传文件 | 永久保留，只读 | 保证数据可复现性 |
| 预览缓存（JSON） | 可重建，可删除 | 节省带宽 |
| 历史版本文件 | 永久保留（有下载记录的版本） | 保证引用持久性 |
| 历史版本删除 | 仅允许删除无下载记录版本 | 保护已被使用/引用的数据 |
| 未发布草稿文件 | 永久保留（作为用户工作区持续保存，不自动清理） | 保证草稿随时可继续编辑 |
| 对象访问控制 | 默认私有，下载使用短时签名 URL | 防止对象存储被直接遍历 |

### 5.3 配额管理

```
普通注册用户：5 GB
认证用户（提供机构邮箱/ORCID）：10 GB
超出配额：后端拒绝写入（HTTP 403），前端仅做友好提示
```

### 5.4 单次上传限制

```
单文件：200 MB
单数据集（所有文件之和）：1 GB
每个数据集最多：10 个文件
```

### 5.5 上传安全与大文件防 OOM 策略（强制）

- **恶意攻防**：
  - 后端双重校验文件类型：扩展名白名单 + `python-magic` MIME 校验，任一不匹配即拒绝
  - 文件名净化与随机对象键：禁止路径穿越字符（如 `../`），存储时统一改为系统生成 key
  - 压缩包安全：限制解压层级、解压后总大小和文件数，防止 zip bomb
  - 恶意内容扫描：文件入库前进入隔离区，扫描通过后再转正式存储区
  - 失败即阻断：扫描失败、类型不合法、超限均标记关联 `physical_storage_objects.upload_status=error`，并写入 `dataset_files.error_message`，不可发布
- **防服务 OOM (内存溢出) 限制**：
  - **严禁**在 FastAPI 接收线程中直接使用 `pd.read_csv()` 或 `pd.read_excel()` 将大文件一把读入内存。
  - **CSV 处理**：强制使用 `chunksize` 流式分块解析并统计 `row_count` 截取预览。
  - **Excel 处理**：限定通过 `openpyxl(read_only=True)` 迭代生成器逐行扫描；若处理困难，可限制前端大于 50MB 的表格强制转为 `.csv` 后再上传。
  - 解析计算过程必须通过 Celery/RQ 投递到独立的 Worker 节点异步执行，不可阻塞 Web 服务导致宕机。
  - **upload_status 状态流转规则**：
    1) 初始挂起：`pending`（客户端开始上传前或传回前）
    2) 扫描通过 + 隔离区转存 MinIO 成功：`pending -> ready`
    3) 格式非法、病毒扫描失败、防 OOM 截断检测失败：`pending -> error`（标记后中断且文件无法用于发布）

### 5.6 下载计数口径（统一）

- 统计口径针对“全量下载当前版本”（download-all），不统计单文件下载
- 采用“签发 download-all URL 即计数”的策略（实现简单、性能稳定）
- `datasets.download_count` 与 `dataset_versions.download_count` 在 download-all 时同步递增
- 在前端标注口径：下载量表示“发起全量下载次数”，不保证文件完整传输

### 5.7 全量打包下载（Download-all）技术实现

为了避免大文件动态打包导致服务端内存溢出（OOM）或网络断流，采用以下策略：
1. **离线打包**：当版本状态变更为 `published` 时，立刻触发后台 Celery 任务，将该版本所有相关文件打包成一个独立的 `.zip` 归档文件。
2. **独立存储**：将生成的 ZIP 文件回传至 MinIO（例如 `v{n}/archive/dataset_v{n}.zip`）。
3. **短时签发**：用户点击下载当前版本全量文件时，直接签发这个 ZIP 对象的临时访问 URL，直接通过底层存储加速下载，不再经由后端应用层中转数据。

### 5.8 预览文件生成与继承策略

为避免版本继承后预览缺失，统一采用“每版本独立预览缓存”：

1. 新上传/替换文件：在对应 `v{n}/preview/` 生成预览 JSON
2. 继承未改动文件：复制上一版本预览 JSON 到新版本 `v{n}/preview/`
3. 预览 API 优先读取预览缓存；不存在时后端按需重建并回写缓存
4. 预览缓存与 `dataset_versions.version_num` 一一对应，禁止跨版本复用路径

### 5.9 physical_storage_objects 引用计数补偿机制

为避免 `ref_count` 与实际版本文件引用关系不一致，统一采用以下规则：

1. 新文件入库、版本继承、版本删除导致的 `ref_count +/- 1`，必须与对应的 `dataset_files` 增删在同一数据库事务内提交
2. 若事务回滚，则 `ref_count` 变更一并回滚，禁止出现“版本创建失败但引用计数已增加”的脏状态
3. 物理文件异步清理仅在事务提交后触发；任务执行前再次校验 `ref_count = 0`
4. Scheduler 每日执行一次对账任务：按 `dataset_files.file_key` 聚合实际引用数，并与 `physical_storage_objects.ref_count` 比对；若不一致，以实际引用数回写修正并记录审计日志
5. 对账任务属于补偿机制，不替代事务内维护；日常写入逻辑仍以事务一致性为第一原则

---

## 6. 后端 API 设计

### 6.1 API 路由总览

```
认证
  POST   /api/auth/register
  POST   /api/auth/verify-email/request
  POST   /api/auth/verify-email/confirm
  POST   /api/auth/login
  POST   /api/auth/logout
  POST   /api/auth/refresh
  POST   /api/auth/forgot-password
  POST   /api/auth/reset-password

用户
  GET    /api/users/me
  PUT    /api/users/me
  GET    /api/notifications                 # 获取消息列表（对应 P14）
  PUT    /api/notifications/{id}/read       # 标记消息已读
  PUT    /api/notifications/read-all        # 标记全部已读

公共
  GET    /api/stats/overview                # 首页统计数据（数据集数/反应条数/注册用户），结果缓存 5 分钟

数据集
  GET    /api/datasets                      # 列表 + 搜索（走 dataset_search_documents 读模型）
  POST   /api/datasets                      # 创建数据集并初始化 V1 草稿版本（version_note 可空）
  POST   /api/datasets/{id}/submit-review   # 提交上线审核（创建 review request，请求体需显式传 { "version_num": X }）
  POST   /api/datasets/{owner}/{slug}/archive    # 作者归档（写入 pre_archive_status 后置为 archived）
  POST   /api/datasets/{owner}/{slug}/unarchive  # 取消归档（恢复到 pre_archive_status）
  GET    /api/datasets/{owner}/{slug}        # 详情（最新版）
  GET    /api/datasets/{owner}/{slug}/v{n}   # 指定版本
  PUT    /api/datasets/{owner}/{slug}        # 更新元信息（pending_review 时拒绝编辑）
  DELETE /api/datasets/{owner}/{slug}        # 软删除（回收配额 + 异步清理文件）

文件
  POST   /api/datasets/{id}/files            # 上传文件（Body 必须显式传 version_num；P08 固定传 1，P15 传当前草稿版本号）
  GET    /api/datasets/{id}/files/{file_id}/preview   # 预览数据
  GET    /api/datasets/{id}/files/{file_id}/download  # 下载
  GET    /api/datasets/{id}/versions/{n}/download-all # 下载当前版本全量文件（zip 或 signed-url manifest）

版本
  POST   /api/datasets/{id}/versions         # 创建新版本草稿记录，返回 version_num（P15 步骤 1 入口）
  PUT    /api/datasets/{id}/versions/{n}     # 更新草稿版本信息（version_note / change_manifest / 元信息暂存）
  GET    /api/datasets/{id}/versions         # 版本列表（含 status 字段，前端可据此判断是否存在未完成草稿）
  DELETE /api/datasets/{id}/versions/{n}     # 删除历史版本（无下载记录才允许）

文件继承
  POST   /api/datasets/{id}/versions/{n}/inherit-files  # 从上一版本批量继承未改动文件（传入 { "file_ids": [...] }，需与 ref_count 递增在同一事务内完成，详见5.3）

管理员建议
  PUT    /api/suggestions/{id}/status         # 作者更新建议状态（resolved/dismissed）

互动
  POST   /api/datasets/{id}/upvote           # 投票
  DELETE /api/datasets/{id}/upvote           # 取消投票
  GET    /api/datasets/{id}/discussions      # 讨论列表
  POST   /api/datasets/{id}/discussions      # 发表评论
  PUT    /api/datasets/{id}/discussions/{discussion_id}     # 编辑本人评论
  DELETE /api/datasets/{id}/discussions/{discussion_id}  # 软删除评论

管理员
  GET    /api/admin/review-requests         # 待审核/历史审核列表
  GET    /api/admin/review-requests/{id}    # 审核详情（元数据+文件信息+列说明）
  POST   /api/admin/review-requests/{id}/approve  # 审核通过并上线
  POST   /api/admin/review-requests/{id}/reject   # 驳回并附原因
  GET    /api/admin/datasets                 # 所有数据集
  POST   /api/admin/datasets/{id}/suggest    # 推送建议（仅 published/revision_required 可用）
  PUT    /api/admin/datasets/{id}/takedown   # 下架（置 dataset_status=takedown）
  PUT    /api/admin/datasets/{id}/restore    # 恢复（回 draft 或 published）
  GET    /api/admin/users                    # 用户列表
  PUT    /api/admin/users/{id}/quota         # 调整配额
```

### 6.2 关键 API 响应示例

#### POST /api/auth/login

```json
{
  "access_token": "jwt_access_token",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "uuid",
    "username": "yi_zhang",
    "email": "yi@pku.edu.cn",
    "role": "user",
    "is_email_verified": false
  }
}
```

说明：前端必须以响应体中的 `user.is_email_verified` 作为界面权限判断依据（是否展示上传、评论、Upvote 入口）；JWT payload 仅承载鉴权所需最小字段，不要求前端从 token 自行解析邮箱验证状态。

#### GET /api/datasets（列表）

```json
{
  "total": 128,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": "uuid",
      "owner": "yi_zhang",
      "slug": "Suzuki_coupling_HTE",
      "title": "Suzuki coupling HTE",
      "description": "...",
      "tags": ["yield_prediction", "C-C_coupling", "has_yield_data", "has_solvent_data", "has_ligand_data"],
      "tag_groups": {
        "task": ["yield_prediction", "C-C_coupling"],
        "field": ["has_yield_data", "has_solvent_data", "has_ligand_data"]
      },
      "current_version": 2,
      "total_rows": 2233,
      "total_file_size": 618496,
      "upvote_count": 234,
      "download_count": 1820,
      "view_count": 5430,
      "dataset_status": "published",
      "created_at": "2025-11-02T08:00:00Z",
      "updated_at": "2026-03-13T10:00:00Z"
    }
  ]
}
```

### 6.3 API 安全约束（统一）

1. 认证与会话
- Access Token 有效期 15 分钟，Refresh Token 有效期 7 天
- Refresh Token 采用轮换机制：每次刷新签发新 token，旧 token 立即作废
- Refresh Token 仅以 hash 存库（`auth_refresh_tokens`），登出时服务端撤销
- 普通用户必须完成邮箱验证（`is_email_verified=true`）后才可上传、评论、Upvote

2. 权限与对象级鉴权
- 所有 `dataset/file/version` 读写接口均执行对象级鉴权（owner/状态可公开/admin）
- `file_id` 下载与预览必须二次校验其归属 `dataset_status`，防止 IDOR 越权
- 管理员接口要求 `role=admin`，并记录审计日志

3. 防暴力与防滥用
- 登录接口限流：同 IP 每分钟 10 次，连续 5 次失败触发 15 分钟冻结
- 上传、下载、评论、搜索接口均设置速率限制，超限返回 HTTP 429
- 关键操作（登录失败、封禁、下架、权限变更）写入 `security_audit_logs`

4. 输入与输出安全
- 所有输入走 Pydantic 校验（长度、格式、枚举）；禁用未声明字段。
- **自定义 Tag 一致性强校验**：写入前强制转换为纯小写，并通过正则限制只允许字母、数字、下划线，阻断变体和乱码刷库行为。
- 用户可见文本（标题、描述、讨论内容）在渲染前做 XSS 过滤
- 错误响应不返回堆栈和内部路径，仅返回可追踪错误码

### 6.4 草稿与公开校验规则（强制）

该逻辑由后端强校验，前端仅做引导提示，不能替代服务端校验。

**0. 数据集创建与 V1 初始化时序（强制）**

1. 调用 `POST /api/datasets` 时，后端原子创建：
- `datasets` 记录（`dataset_status='draft'`）
- `dataset_versions(dataset_id, version_num=1, status='draft', version_note=NULL)` 草稿记录
2. P08 上传文件调用 `POST /api/datasets/{id}/files`，默认写入 `version_num=1`
3. P09 填写“初始版本说明（V1）”时，回写到已存在的 V1 `version_note`
4. 提交上线审核时（B 组校验）强制 `version_note` 非空

**0.1 新版本草稿创建时序（P15，强制）**

1. 作者点击 `+ New Version` 后，前端先调用 `POST /api/datasets/{id}/versions`
2. 后端在单事务内完成：
- 校验当前数据集不存在 `status='draft'` 的版本（同一时刻仅允许1个新版本草稿）
- 计算 `next_version_num = max(version_num) + 1`
- 创建 `dataset_versions(dataset_id, version_num=next_version_num, base_version_num=current_version, status='draft', version_note=NULL, change_manifest={})`
- 返回 `version_num`
3. P15 步骤 1 的所有文件上传与继承操作，必须显式携带这个 `version_num`
4. P15 步骤 2 完成前，该版本 `status='draft'`，即“草稿版本”，不对外展示在公开详情页中，仅作者可见。提交审核后变为 `pending_review`，发布后变为 `published`。
5. 若用户中途放弃：
- 草稿版本将一直保存于系统内，作为用户的私人工作区，不会被系统自动清理或丢弃，确保用户随时能回来继续编辑。
6. 一个数据集同一时刻只允许存在 1 个 `status='draft'` 的版本，避免 P15 上传时目标版本歧义

**0.2 文件上传接口契约（强制）**

`POST /api/datasets/{id}/files` 请求体必须包含：

```json
{
  "version_num": 3,
  "file_role": "data",
  "filename": "train_set.csv"
}
```

约束：

1. `version_num` 为必填字段，不允许后端按“当前版本”自动猜测
2. P08 固定传 `version_num = 1`
3. P15 只能传由 `POST /api/datasets/{id}/versions` 返回的草稿版本号
4. 后端收到上传请求后，必须先校验：
- 该 `version_num` 属于当前 `dataset_id`
- 当前用户为 owner 或 admin
- 该版本尚未提交审核，且未被删除
5. 若校验失败，返回 `409 invalid_target_version`

**A. 保存草稿（宽松校验）**

- 允许元数据不完整写库（用于中断后继续编辑）
- 最低要求：
1. 至少存在 1 个上传文件记录
2. 数据集存在 V1 版本记录（`version_num=1`）
3. 数据集归属合法（owner 一致）
4. 字段类型/长度/枚举合法（Pydantic）

**B. 提交上线审核（严格校验）**

调用 `POST /api/datasets/{id}/submit-review` 时必须全部通过：

1. 数据集基础信息完整：`title/description/source_type/license` 非空
2. `description` 长度满足最小限制（当前设计：>=50 字）
3. 至少 1 个任务类 Tag
4. 当前提交版本 `version_note` 非空
5. 该版本所有文件关联的 `physical_storage_objects.upload_status=ready`
6. 该版本所有文件 `description` 非空
7. 该版本所有列 `description` 非空
8. 文件与列引用关系完整（无孤儿列、无跨版本错配）

校验失败返回 `422`，并返回字段级错误（如 `missing_file_description`, `missing_column_description`）。

**C. 管理员审核通过前复核（防绕过）**

- `POST /api/admin/review-requests/{id}/approve` 前再次执行 B 组校验
- 若校验失败，拒绝通过并提示管理员“提交内容已变化，请作者修正后重提”
- 通过后原子更新：
1. `dataset_status -> published`
2. `datasets.current_version` 更新为本次审核通过的版本号（若大于当前值）
3. `dataset_versions.status -> 'published'`，`metadata_complete=true`
4. 写入 `dataset_review_requests(status=approved, reviewed_at, reviewed_by)`
5. 触发异步任务：生成该版本的 ZIP 归档包并投影更新 `dataset_search_documents`

**D. 审核中锁定元信息（避免“审核快照漂移”）**

- 当 `dataset_status=pending_review` 时，`PUT /api/datasets/{owner}/{slug}` 返回 `409 Conflict`
- 错误码建议：`dataset_under_review_locked`
- 提示文案建议：“数据集审核中，暂不可编辑；请等待审核结果后再修改”

### 6.5 历史版本删除规则（强制）

`DELETE /api/datasets/{id}/versions/{n}` 仅允许所有者删除“未被使用”的历史版本：

1. 至少保留 1 个版本（不能删空数据集版本）
2. `dataset_versions.download_count > 0` 时拒绝删除，返回 `409 Conflict`
3. 若存在任意更高版本 `m > n`，则禁止删除 `Vn`，返回 `409 version_has_descendants`；删除操作仅允许作用于“当前版本之前且无后继版本依赖”的叶子历史版本，避免 `change_manifest` 比较基准断裂
4. 若删除的是 `current_version`，自动回退到现存最大版本号
5. 删除与 `current_version` 回退需在同一事务内完成，避免读到中间态
6. 当数据集处于 `takedown` 状态时，禁止作者删除任何版本（返回 `409`）

### 6.6 建议处理闭环（编辑联动）

- 用户从 P14 收到提醒并点击“去处理”时，前端不仅获取到通知本身，还会从 `notifications.target_id` 提取出原始的 `admin_suggestions.id`。
- 然后带此暗示转入 P10（元信息编辑组件），保存时页面底层自动弹出联动动作钩子：“检测到 1 条待处理管理员建议，是否标记为已完成？”
- 用户确认后，前端主表单保存数据成功后，通过 `PUT /api/suggestions/{suggestion_id}/status` 将状态设为 `resolved`。
- 业务表更新成功后，可以视情况通过异步事件一并消化掉最初的 `notifications` 并置为“已读”。
- 若用户取消，仅保存数据，不改变建议状态
- 若需改文件，用户在 P10 点击「创建修订版本」进入 P15 两步流程
- 当前不对管理员建议做结构化类型判断（无 `suggestion_type` 字段），避免错误自动分流

### 6.7 讨论编辑与软删除规则

- `PUT /api/datasets/{id}/discussions/{discussion_id}` 仅允许评论作者编辑文本内容
- 编辑成功写入 `edited_at` 与 `updated_at`，前端显示“（已编辑）”
- 当前不保留编辑历史版本（仅保留最后一版）
- `DELETE /api/datasets/{id}/discussions/{discussion_id}` 仅做软删除：
- 写入 `deleted_at`、`deleted_by`，保留原记录与回复关系
- 前端将被删评论渲染为占位文案：“该评论已删除”
- 子回复正常保留，避免讨论链断裂

### 6.8 数据集删除与配额原子回收

- `DELETE /api/datasets/{owner}/{slug}` 针对用户主动删除执行软删除：
- 软删除动作事务内完成：
1. 写入 `datasets.deleted_at/deleted_by`
2. `dataset_status -> deleted`
3. 若当前状态存在于 `dataset_review_requests` 的 `pending` 状态，原子更新为 `canceled_by_user`。
4. **配额安全扣减**：必须使用数据库原子操作扣减，防止高并发上传/删除导致的配额“脏写”：
   `UPDATE users SET storage_used = GREATEST(storage_used - :total_size, 0) WHERE id = :user_id`
- 文件物理清理排入 Celery 异步队列离线执行；失败进入死信队列报警重试，不影响主请求返回。

### 6.9 全量下载与单文件下载语义

- 头部下载按钮对应 `GET /api/datasets/{id}/versions/{n}/download-all`
- 单文件下载继续使用 `GET /api/datasets/{id}/files/{file_id}/download`
- `datasets.download_count` 与 `dataset_versions.download_count` 只统计 `download-all`
- 单文件下载不计入头部下载量统计

### 6.10 审核并发控制（必须）

- `POST /api/admin/review-requests/{id}/approve|reject` 必须在同一事务内检查并更新
- 推荐实现：
1. `SELECT ... FOR UPDATE` 锁定该 review request
2. 仅当 `status='pending'` 才允许决策写入
3. 若状态已变化，返回 `409 Conflict`（如 `review_request_already_decided`）
- 确保任一审核请求只会有一个最终决策

### 6.11 管理员建议接口适用状态

- `POST /api/admin/datasets/{id}/suggest` 仅允许 `published` 或 `revision_required`
- 对 `draft` / `pending_review` / `takedown` / `archived` 返回 `409`
- `pending_review` 阶段管理员意见应通过审核通过/驳回流程表达，不走建议通道

### 6.12 密码重置流程约束（必须）

- `POST /api/auth/forgot-password` 无论邮箱是否存在都返回统一成功响应，避免账号枚举
- 重置令牌采用一次性短时 token（建议 30 分钟）并保存哈希（Redis 或数据库）用于核销
- `POST /api/auth/reset-password` 成功后立即失效该 token，并撤销用户全部 Refresh Token
- 密码重置事件写入 `security_audit_logs`（`event_type=password_reset`）

### 6.13 业务错误码体系（强制）

错误响应统一格式：

```json
{
  "error": {
    "code": "dataset_under_review_locked",
    "message": "数据集审核中，暂不可编辑",
    "details": {
      "dataset_id": "uuid"
    }
  }
}
```

命名规则：

1. 统一使用小写蛇形命名法
2. 前缀按领域划分：`auth_*`、`dataset_*`、`version_*`、`review_*`、`file_*`、`suggestion_*`
3. `message` 为可直接展示的默认文案；前端允许按 `code` 覆盖本地化文案

首批必须实现的错误码：

| HTTP | code | 默认文案 |
|------|------|----------|
| 401 | `auth_invalid_credentials` | 邮箱或密码错误 |
| 403 | `auth_email_not_verified` | 邮箱未验证，当前操作不可用 |
| 403 | `dataset_access_denied` | 你没有权限访问该数据集 |
| 404 | `dataset_not_found` | 数据集不存在或不可见 |
| 409 | `dataset_under_review_locked` | 数据集审核中，暂不可编辑 |
| 409 | `review_request_already_decided` | 该审核请求已处理 |
| 409 | `invalid_target_version` | 目标版本不可写入 |
| 409 | `version_has_descendants` | 该版本仍被后续版本作为比较基准，不能删除 |
| 409 | `draft_version_already_exists` | 当前已有未完成的新版本草稿 |
| 409 | `dataset_status_conflict` | 当前数据集状态不支持该操作 |
| 422 | `missing_file_description` | 存在未填写说明的文件 |
| 422 | `missing_column_description` | 存在未填写说明的列 |
| 422 | `invalid_tag_format` | Tag 格式非法 |

---

## 7. 前端框架与页面总览

### 7.1 设计风格

- **风格定位**：简约学术风，参考 Semantic Scholar、arXiv、Zenodo
- **色彩方案**：白底 + 深蓝主色（`#1E3A5F`）+ 浅灰辅助（`#F8F9FA`）+ 绿色成功（`#28A745`）+ 橙色警告（`#FD7E14`）
- **字体**：正文 `Inter`，代码/SMILES `JetBrains Mono`
- **布局**：最大宽度 `1200px`，左右留白，内容居中

### 7.2 页面清单（共 18 页）

| 编号 | 页面名称 | 路由 | 访问权限 |
|------|---------|------|---------|
| P01 | 首页 | `/` | 所有人 |
| P02 | 数据集市场 | `/datasets` | 所有人 |
| P03 | 数据集详情 | `/datasets/{owner}/{slug}` | 所有人 |
| P04 | 数据集详情（指定版本） | `/datasets/{owner}/{slug}/v{n}` | 所有人 |
| P05 | 注册页 | `/register` | 未登录 |
| P06 | 登录页 | `/login` | 未登录 |
| P18 | 邮箱验证结果页 | `/verify-email` | 未登录 |
| P16 | 忘记密码 | `/forgot-password` | 未登录 |
| P17 | 重置密码 | `/reset-password` | 未登录 |
| P07 | 个人主页 | `/profile` | 已登录 |
| P14 | 消息中心 | `/messages` | 已登录 |
| P08 | 上传步骤一（文件上传） | `/upload/step1` | 已验证登录 |
| P09 | 上传步骤二（信息填写） | `/upload/step2` | 已验证登录 |
| P10 | 数据集元信息编辑 | `/datasets/{owner}/{slug}/edit` | 所有者/管理员 |
| P15 | 数据集新增版本（两步） | `/datasets/{owner}/{slug}/new-version` | 所有者/管理员 |
| P11 | 管理员登录 | `/admin/login` | — |
| P12 | 管理员控制台 | `/admin/datasets` | 管理员 |
| P13 | 管理员用户管理 | `/admin/users` | 管理员 |

---

## 8. 各页面详细设计

---

### P01 首页

**目标**：面向访客的宣传入口，快速传达平台价值，引导进入市场或注册。

**布局**：

```
┌──────────────────────────────────────────────────────────┐
│  NAVBAR                                                   │
│  [Logo] RxnCommons    首页  数据集  关于       登录  注册  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  HERO                                                     │
│                                                           │
│         化学反应数据共享平台                               │
│    开放 · 可信 · 专为化学研究设计                          │
│                                                           │
│    ┌──────────────────────────────────┐  [搜索]           │
│    │  搜索数据集标题或 Tag...          │                   │
│    └──────────────────────────────────┘                   │
│                                                           │
│    [浏览数据集 →]   [上传我的数据集]                       │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  STATS（统计数字，实时）                                   │
│                                                           │
│   1,284          8,920,000+        542                    │
│   数据集          反应条数           注册用户               │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  精选数据集（3张卡片横排）                                  │
│                                                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ 数据集标题    │ │ 数据集标题    │ │ 数据集标题    │      │
│  │              │ │              │ │              │      │
│  │ Tag Tag      │ │ Tag Tag      │ │ Tag Tag      │      │
│  │ 2,233 条     │ │ 4,821 条     │ │ 52,430 条    │      │
│  │ ▲234  ↓1820 │ │ ▲891  ↓3872 │ │ ▲102  ↓940  │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
│                                         [查看全部 →]      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  平台特点（3列）                                           │
│                                                           │
│   🔬 专为化学反应设计    🏷️ 结构化Tag检索   🔒 原始数据不改  │
│   支持多种文件格式        元信息可追溯      上传即存档        │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  FOOTER                                                   │
│  关于  联系  GitHub  隐私政策  Terms                       │
└──────────────────────────────────────────────────────────┘
```

**交互细节**：
- 搜索框回车直接跳转到 P02，并带上搜索参数
- "上传我的数据集"按钮：未登录则跳转 P06 登录页，登录后跳转 P08
- 精选数据集选取规则：v1 限定查询 `dataset_search_documents` 中 `dataset_status IN ('published', 'revision_required')` 的数据集，按 `upvote_count` 倒序截取 Top 3 展示（后续版本可扩展手动置顶配置）
- STATS 统计数字数据来源：`数据集` = `COUNT(*) FROM dataset_search_documents WHERE dataset_status IN ('published','revision_required','archived')`；`反应条数` = `SUM(total_rows) FROM dataset_search_documents WHERE ...`；`注册用户` = `COUNT(*) FROM users`。建议后端提供 `GET /api/stats/overview` 接口，结果可缓存 5 分钟

---

### P02 数据集市场

**目标**：数据集的发现与检索，支持按 Tag 和条件筛选。

**布局**：

```
┌──────────────────────────────────────────────────────────┐
│  NAVBAR（同上）                                           │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  搜索栏                                                   │
│  ┌──────────────────────────────────────────┐  [搜索]    │
│  │  搜索数据集标题或 Tag...                   │           │
│  └──────────────────────────────────────────┘           │
│  共找到 128 个数据集    排序: [最新上传 ▼]                 │
└──────────────────────────────────────────────────────────┘

┌──────────────┬───────────────────────────────────────────┐
│  筛选面板     │  数据集卡片列表                             │
│  （左侧固定） │                                           │
│              │  ┌────────────────────────────────────┐   │
│  适用任务    │  │ Suzuki coupling HTE                │   │
│  □ 产率预测  │  │ by yi_zhang  ·  2,233条  ·  604KB  │   │
│  □ 条件预测  │  │                                    │   │
│  □ 逆合成    │  │ #yield_prediction  #C-C_coupling   │   │
│  □ 正向预测  │  │ #HTE                               │   │
│  □ 反应分类  │  │                                    │   │
│              │  │（卡片仅展示任务Tag）                │   │
│  ──────────  │  │ ▲ 234    ↓ 1,820                   │   │
│  数据规模    │  └────────────────────────────────────┘   │
│  □ <1000条   │                                           │
│  □ 1k~10k条  │  ┌────────────────────────────────────┐   │
│  □ >10k条    │  │ Buchwald-Hartwig Amination          │   │
│              │  │ by doyle_group  ·  3,956条  ·  2MB  │   │
│  ──────────  │  │                                    │   │
│  数据来源    │  │ #yield_prediction  #C-N_coupling   │   │
│  □ 实验室    │  │                                    │   │
│  □ 文献提取  │  │（字段覆盖信息在详情页展示）          │   │
│  □ 专利提取  │  │                                    │   │
│  □ 数据库导出│  │                                    │   │
│  ──────────  │  │                                    │   │
│  数据状态    │  │                                    │   │
│  □ 已发布    │  │                                    │   │
│  □ 待修订    │  │                                    │   │
│  □ 已归档    │  │                                    │   │
│              │  │ ▲ 891    ↓ 3,872                   │   │
│              │  └────────────────────────────────────┘   │
│              │  [← 上一页]  第1/7页  [下一页 →]          │
└──────────────┴───────────────────────────────────────────┘
```

**卡片字段说明**：
- `▲ 234`：社区 Upvote 数
- `↓ 1,820`：下载次数
- 卡片仅展示任务类 Tag；字段覆盖信息在详情页右侧“包含字段”区域展示

**搜索逻辑**：
- P02 不直接扫业务主表，而是查询 `dataset_search_documents` 读模型
- v1 采用“标题模糊匹配 + Tag 精确过滤 + 状态过滤 + 排序字段”组合方案
- 左侧“数据规模”筛选：对应后端对读模型的 `total_rows` 字段进行范围过滤（如 `<1000`, `BETWEEN 1000 AND 10000`, `>10000`）
- 默认搜索范围包含 `published`、`revision_required`、`archived`
- 用户可通过左侧“数据状态”筛选仅查看已发布、待修订或已归档数据集
- 暂不引入独立搜索引擎，但数据库需启用 `pg_trgm` 或 FTS 索引，否则列表页会在规模增长后退化为慢查询热点

---

### P03 数据集详情页（最新版）

**目标**：完整展示数据集信息，支持数据预览、讨论、下载。

**布局**：

```
┌──────────────────────────────────────────────────────────┐
│  NAVBAR（登录后右上显示消息入口）                            │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  数据集头部                                               │
│                                                           │
│  Suzuki coupling HTE      [▲ Upvote 234]  [↓ 下载 1,820] │
│  by yi_zhang  ·  更新于 2026-03-13  ·  V2（最新）         │
│  [下载当前版本（全量）]  [复制数据集链接]  [复制当前版本链接] │
│  状态：已发布（Published）                                │
│                                                           │
│  #yield_prediction  #C-C_coupling  #HTE  #Pd-catalysis   │
│                                                           │
│  这是一个关于Suzuki偶联反应的高通量筛选数据集，            │
│  包含不同配体和碱组合下的产率数据...                       │
│                                                           │
│  当前版本统计（V2）：2,233 条反应 · 3 个文件 · 604 KB      │
│                 当前版本下载 1,820 次（发起下载次数）        │
└──────────────────────────────────────────────────────────┘

┌────────────────────────────────────┬─────────────────────┐
│  Tab 导航                           │  右侧信息栏          │
│  [数据预览] [讨论(12)]              │                     │
│                                    │  文件列表（点击切换） │
│  ─────────────────────────────     │  train_set.csv 4.2MB ● [下载]│
│                                    │  test_set.csv  1.1MB   [下载]│
│  【数据预览 Tab】                   │  metadata.xlsx 0.6MB   [下载]│
│  表头（同一表格框内，双行固定）：     │                     │
│  ┌────────────┬────────────┬──────┐│  ─────────────────   │
│  │反应物SMILES │产物SMILES  │产率(%)││  包含字段（field Tag） │
│  │reactants   │products    │yield ││  #has_reactants_data │
│  ├────────────┼────────────┼──────┤│  #has_products_data  │
│  │CC(=O)...   │CC(=O)...   │88.2  ││  #has_yield_data     │
│  │c1ccc...    │c1ccc...    │91.5  ││  #has_solvent_data   │
│  │...         │...         │...   ││  #has_ligand_data    │
│  └────────────┴────────────┴──────┘│  ─────────────────   │
│  横向滚动浏览数据；表头两行固定不动。 │  元信息              │
│  显示 50 / 2,233 行                │  状态：已发布         │
│                                    │  数据来源：文献提取   │
│                                    │  DOI: 10.1021/...    │
│                                    │  License: CC BY 4.0  │
│                                    │                     │
│                                    │  ─────────────────   │
│                                    │  版本历史            │
│                                    │  V2  2026-03-13 当前 │
│                                    │  V1  2025-11-02      │
│                                    │       [查看] [下载] [删除] │
│                                    │  *注：[删除]按钮仅在该版本无后继版本且无下载记录时展示* │
│                                    │                     │
│                                    │  ─────────────────   │
│                                    │  版本操作（仅所有者） │
│                                    │  [+ New Version]     │
│                                    │  [归档/取消归档]      │
│                                    │  （若 V1 未完成字段说明│
│                                    │   则按钮禁用并提示）  │
└────────────────────────────────────┴─────────────────────┘
```

**信息分层建议**：
- 字段类 Tag 放在右侧信息栏展示，不作为左侧筛选依据
- 文件选择放在右侧“文件列表”，高亮即表示当前文件，左侧无需重复展示文件名
- 列说明直接放在列名上方并保持对齐，减少来回比对成本
- 数据集统计信息上移到头部区域，作为全局信息优先展示
- 表格支持横向滚动，列说明+列名两行表头固定，浏览长表时不丢失语义
- 新增版本入口固定在右侧栏底部，避免与浏览信息混淆
- 新增版本前置条件：V1 的文件描述与列说明必填项全部完成
- 管理员建议统一进入“消息中心”，详情页/编辑页仅显示跳转提示，不重复展示全文
- `published/revision_required/archived` 支持公开分享；其余状态复制链接仅供作者/管理员内部访问
- `revision_required` 状态下保持公开和可下载，仅作者可见“待处理建议”提示条
- 头部下载按钮固定为“下载当前版本全量文件”，右侧文件列表的 `[下载]` 为单文件下载
- 头部下载量仅统计全量下载，不包含单文件下载
- 浏览量计数触发：每次加载 `GET /api/datasets/{owner}/{slug}` 详情页时，后端异步递增 `datasets.view_count`（同一用户/IP 短时间内多次访问建议去重，可通过 Redis 窗口计数实现；v1 简化处理可不去重）

**讨论 Tab 详细交互（必须）**：

- 展示形式：顶层评论平铺，回复使用二级缩进列表，不再向下无限嵌套
- 每页加载 20 条顶层评论，默认按“最新发布”倒序；v1 不提供“最热排序”
- 每条顶层评论默认展示最近 3 条回复，超出部分点击“展开更多回复”异步加载
- 回复时支持前端展示 `@username`，但数据库仅保存纯文本内容，不单独建 mention 表
- `archived` 状态下讨论区只读：可浏览历史讨论，但隐藏输入框与回复按钮
- 删除后的评论显示占位文案，保留楼层结构和回复计数
- 顶层评论卡片字段：作者、时间、正文、编辑标记、回复按钮、删除按钮（本人/管理员可见）

---

### P04 数据集详情（历史版本）

与 P03 相同，但顶部增加版本警告横幅：

```
┌──────────────────────────────────────────────────────────┐
│ ⚠️  你正在查看历史版本 V1（2025-11-02）                   │
│     此版本已被引用，永久保留。当前最新版本为 V2  [查看 →]  │
└──────────────────────────────────────────────────────────┘
```

版本区域高亮显示当前浏览版本，其余内容展示该版本对应的文件和列信息。
页面顶部统计仅显示“当前浏览版本”的下载量（例如 V1 下载量），不显示其他版本或全量聚合下载。

---

### P05 注册页

**布局**：

```
┌──────────────────────────────────────────────────────────┐
│  NAVBAR                                                   │
└──────────────────────────────────────────────────────────┘

                ┌────────────────────────────┐
                │  创建你的 RxnCommons 账号   │
                │                            │
                │  用户名 *                   │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │  3~50字符，字母/数字/下划线  │
                │                            │
                │  邮箱 *                    │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  密码 *                    │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │  至少8位，含字母和数字       │
                │                            │
                │  确认密码 *                │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  机构/单位（可选）          │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  研究方向（可选）           │
                │  ┌────────────────────┐    │
                │  │  请选择...      ▼  │    │
                │  └────────────────────┘    │
                │  有机合成/药物化学/计算化学/其他│
                │                            │
                │  [    注册    ]             │
                │                            │
                │  注册成功后将发送验证邮件      │
                │  未验证邮箱前不可上传/评论/点赞 │
                │                            │
                │  已有账号？ 去登录           │
                └────────────────────────────┘
```

---

### P06 登录页

```
                ┌────────────────────────────┐
                │  登录 RxnCommons            │
                │                            │
                │  邮箱                       │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  密码                       │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │  忘记密码？                 │
                │                            │
                │  [    登录    ]             │
                │                            │
                │  若邮箱未验证，登录后提示      │
                │  [重新发送验证邮件]          │
                │                            │
                │  没有账号？ 去注册          │
                └────────────────────────────┘
```

---

### P18 邮箱验证结果页

```
                ┌────────────────────────────┐
                │  邮箱验证结果                │
                │                            │
                │  ✅ 邮箱验证成功             │
                │  你的账号已具备上传与互动权限 │
                │                            │
                │  [去登录]   [返回首页]       │
                └────────────────────────────┘
```

---

### P16 忘记密码

```
                ┌────────────────────────────┐
                │  找回密码                    │
                │                            │
                │  注册邮箱 *                 │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  [发送重置邮件]             │
                │                            │
                │  已发送后提示：              │
                │  请在 30 分钟内点击邮件链接   │
                └────────────────────────────┘
```

---

### P17 重置密码

```
                ┌────────────────────────────┐
                │  重置密码                    │
                │                            │
                │  新密码 *                   │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  确认新密码 *               │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  [确认重置]                 │
                └────────────────────────────┘
```

---

### P07 个人主页

**布局**：

```
┌──────────────────────────────────────────────────────────┐
│  NAVBAR                                       [🔔 消息 2] │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  个人信息                                                  │
│                                                           │
│  [头像]  yi_zhang                              [设置]     │
│          北京大学  ·  有机合成                             │
│                                                           │
│  5 个数据集    12,450 条反应    3,820 次下载               │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  存储配额                                                  │
│  ████████░░░░░░░░░░░░░░░░░░░░░  1.54 MB / 5 GB           │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  消息摘要（最近 3 条）                                      │
│                                                           │
│  [未读] Suzuki_coupling_HTE · V2 · ligand 列建议         │
│        2026-03-13  admin01    [查看并处理]               │
│                                                           │
│  [已读] Buchwald_dataset · V1 · 来源链接补充建议          │
│        2026-03-10  admin02    [查看详情]                 │
│                                                           │
│  [进入消息中心]                                            │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  我的数据集                            [+ 上传新数据集]   │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Suzuki_coupling_HTE         已发布  V2  2026-03-13    │    │
│  │ #yield_prediction  #C-C_coupling                  │    │
│  │ ▲234  ↓1820      [编辑] [新版本] [归档] [删除]      │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Knoevenagel_condensation      待修订  V1  2026-01-05   │    │
│  │ 描述未填写  ⚠️  待处理建议 1 条                    │    │
│  │      [编辑] [提交审核] [删除]                      │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

**状态操作矩阵（必须）**：

| 状态 | 作者可见按钮 |
|------|--------------|
| `draft` | `[编辑] [提交审核] [删除]` |
| `pending_review` | `[查看] [审核中]`（编辑锁定） |
| `published` | `[编辑] [新版本] [归档] [删除]` |
| `revision_required` | `[编辑] [新版本] [提交审核] [删除]` |
| `archived` | `[查看] [取消归档] [删除]` |
| `takedown` | `[查看下架原因] [联系管理员]` |

---

### P14 消息中心（独立页面）

说明：P07 只展示消息摘要；消息的完整列表、筛选、已读/未读、处理动作都在独立页面完成。  
用户查看管理员反馈的唯一入口为 `P14 /messages`（NAVBAR 消息按钮直达）。

```
┌──────────────────────────────────────────────────────────┐
│  NAVBAR                                       [🔔 消息 2] │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  消息中心                                                  │
│  [全部] [未读] [管理员建议] [系统通知]    搜索:[_______]   │
├──────────────────────────────────────────────────────────┤
│  [未读] 管理员建议 · Suzuki_coupling_HTE · V2            │
│  admin01 · 2026-03-13                                    │
│  “ligand 列命名建议统一为 ...”                            │
│  [标记已读] [查看数据集] [去处理（打开编辑页）]            │
│                                                           │
│  [已读] 管理员建议 · Buchwald_dataset · V1               │
│  admin02 · 2026-03-10                                    │
│  “建议补充来源链接与筛选规则说明”                          │
│  [查看数据集] [去处理]                                    │
└──────────────────────────────────────────────────────────┘
```

**动作约定**：
- `查看数据集`：跳转 P03（对应数据集与版本）
- `去处理`：统一跳转 P10（元信息编辑）
- `标记已读`：仅更新阅读状态，不改变建议处理状态（`pending/resolved/dismissed`）

---

### P08 上传步骤一（文件上传）

**进入时弹出确认弹窗**：

```
┌─────────────────────────────────────────────────┐
│  上传前请确认                                     │
│                                                   │
│  □ 我已对 SMILES 相关列进行了基本检查             │
│  □ 我了解平台不会修改我上传的任何原始数据         │
│  □ 我的列名命名清晰，便于他人理解                  │
│                                                   │
│  建议列名参考（中英文均可）：                      │
│  reactants · products · solvent · catalyst        │
│  ligand · base · yield_pct · temperature_c        │
│  reaction_smiles · reagent · amount_equiv         │
│                                                   │
│  ⚠️ 使用其他列名也完全可以，                      │
│     只需在下一步填写列说明即可                    │
│                                                   │
│                 [取消]  [我已了解，继续上传]       │
└─────────────────────────────────────────────────┘
```

**主页面**：

```
┌──────────────────────────────────────────────────────────┐
│  上传数据集  步骤 1/2：上传文件                            │
│  ●──────○                                                │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐ │
│                                                           │
│  │           拖拽文件到此处上传                         │ │
│              或                                           │
│  │        [  选择文件  ]                               │ │
│                                                           │
│  │  支持 CSV · Excel · SDF · TXT · ZIP                 │ │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  │
│                                                           │
│  已选文件：                                               │
│  📊 train_set.csv          4.2 MB   ████████░░  上传中    │
│  📊 test_set.csv           1.1 MB   ██████████  完成 ✅   │
│  ❌ bad_data.csv           0.5 MB   解析失败：文件过大 [×删除] │
│                                                           │
│  + 添加更多文件                                           │
│                                                           │
│  存储配额：1.54 MB / 5 GB                                │
│                                                           │
│  [取消]                              [下一步，填写信息 →] │
│                                 （文件全部上传后可点击）   │
└──────────────────────────────────────────────────────────┘
```

---

### P09 上传步骤二（信息填写）

**布局**：

```
┌──────────────────────────────────────────────────────────┐
│  上传数据集  步骤 2/2：填写信息                            │
│  ●──────●                                                │
│  文件已保存。请完善以下信息后提交上线审核。                  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  数据集基本信息                                            │
│                                                           │
│  数据集标题 *                                             │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Suzuki coupling HTE                               │    │
│  └──────────────────────────────────────────────────┘    │
│  URL 预览：rxncommons.org/datasets/yi_zhang/             │
│           Suzuki_coupling_HTE                            │
│  （空格自动替换为下划线）                                  │
│  链接在首次保存后即固定；仅在审核通过后可对外公开访问        │
│                                                           │
│  数据集描述 *（至少50字）                                  │
│  ┌──────────────────────────────────────────────────┐    │
│  │                                                    │    │
│  │                                                    │    │
│  │                                                    │    │
│  └──────────────────────────────────────────────────┘    │
│  已输入 0/50 字                                           │
│                                                           │
│  初始版本说明（V1）*                                       │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 2024.03-2025.12 从文献与实验记录整理；剔除缺失产率样本 │    │
│  └──────────────────────────────────────────────────┘    │
│  建议写明：采集来源、时间范围、纳入/剔除规则、清洗方法      │
│                                                           │
│  适用任务 Tag *（至少选1个）                               │
│  [产率预测 ×]  [C-C偶联 ×]  [+ 添加Tag]                  │
│  预设任务Tag：yield_prediction condition_prediction        │
│              retrosynthesis forward_prediction ...        │
│  字段类Tag建议：has_yield_data has_solvent_data           │
│               has_ligand_data has_catalyst_data ...      │
│  Tag 提示：优先使用预设Tag；避免“实验A/数据集1”类无检索价值标签│
│                                                           │
│  数据来源类型（单选） *                                      │
│  ○ 实验室自测  ○ 文献提取  ● 专利提取  ○ 数据库导出          │
│                                                           │
│  来源链接/DOI（强烈建议填写）                              │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 10.1021/jacs.xxxxxxx                              │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│  License *                                                │
│  ┌──────────────────────────────────────────────────┐    │
│  │  CC BY 4.0                                    ▼  │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│  发布动作                                                    │
│  通过底部按钮选择「保存草稿」或「提交上线审核」               │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  作者信息                                                  │
│                                                           │
│  作者 1                              ☰（拖拽排序）  [×]   │
│  姓名 *              机构                                  │
│  ┌──────────────┐   ┌───────────────────────────────┐    │
│  │ Yi Zhang     │   │ Peking University              │    │
│  └──────────────┘   └───────────────────────────────┘    │
│  ORCID（可选）         角色                                │
│  ┌──────────────┐   ● 第一作者  ○ 共同作者  ○ 通讯作者   │
│  │              │                                         │
│  └──────────────┘                                         │
│                                                           │
│  [+ 添加作者]                                             │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  文件信息                                                  │
│                                                           │
│  ── train_set.csv（4.2 MB）────────────────────────────  │
│                                                           │
│  关于该文件                                               │
│  该文件还没有任何描述。                            [编辑] │
│                                                           │
│  数据预览（前5行，仅用于核对列）：                               │
│  ┌──────────────┬──────────────┬──────────┬──────────┐  │
│  │ reactants    │ products     │ ligand   │ yield_pct│  │
│  ├──────────────┼──────────────┼──────────┼──────────┤  │
│  │ CC(=O)Cl.... │ CC(=O)OCC.. │ PPh3     │ 88.2     │  │
│  │ ...          │ ...          │ ...      │ ...      │  │
│  └──────────────┴──────────────┴──────────┴──────────┘  │
│                                                           │
│  点击[编辑]后在下方展开编辑区（内联，不跳转）：                 │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ 表描述 *                                           │  │
│  │ ┌───────────────────────────────────────────────┐ │  │
│  │ │ [请填写该文件/该表的用途、来源与字段说明...]    │ │  │
│  │ └───────────────────────────────────────────────┘ │  │
│  │                                                   │  │
│  │ 列说明填写（列名纵向展示，右侧编辑框）：              │  │
│  │ ┌────────────┬─────────────────────────────────┐ │  │
│  │ │ reactants  │ [请填写描述...]                 │ │  │
│  │ │ products   │ [请填写描述...]                 │ │  │
│  │ │ ligand     │ [请填写描述...]                 │ │  │
│  │ │ yield_pct  │ [请填写描述...]                 │ │  │
│  │ │ batch_id   │ [请填写描述...]                 │ │  │
│  │ └────────────┴─────────────────────────────────┘ │  │
│  │ 完成度：0/5（示例）                 [取消] [保存]  │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  ── test_set.csv（1.1 MB）─────────────────────────────  │
│  （同上结构：逐文件独立编辑，互不干扰）                      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  [← 返回上传]     [保存草稿]     [提交上线审核]            │
│                    草稿保存         审核通过后公开          │
└──────────────────────────────────────────────────────────┘
```

调用 `POST /api/datasets` 时系统已初始化 `V1` 草稿记录；在 P09 填写「初始版本说明（V1）」后回写 `dataset_versions.version_note`。

**编辑交互建议**：
- 初始展示空状态文案 + `[编辑]` 按钮，避免用户误以为已有描述
- 点击 `[编辑]` 在当前文件卡片下方内联展开编辑区，编辑后原位保存
- 编辑区内列名纵向固定展示，右侧统一输入框填写说明，便于批量编辑
- 已填写字段允许重复修改，保存后立即回写到该文件
- 保存草稿仅执行基础格式校验，允许保留未完成必填项
- 提交上线审核前做逐列校验，仅阻止缺失列说明的文件进入审核

---

### P10 数据集元信息编辑（单页）

用途：仅编辑元信息，不触发版本号变化；适用于“改标题/描述/Tag/来源/License/作者”等场景。  
入口：P07「编辑」、P03「编辑」、P14「去处理」。

**布局**：

```
┌──────────────────────────────────────────────────────────┐
│  编辑数据集元信息                                          │
│  数据集：Suzuki_coupling_HTE  当前版本：V2                │
├──────────────────────────────────────────────────────────┤
│  标题 * / 描述 * / Tag * / 来源类型 * / License *          │
│  来源链接/DOI / 作者信息（可编辑）                          │
│                                                           │
│  [取消]  [保存元信息]   [创建修订版本（去 P15）]            │
└──────────────────────────────────────────────────────────┘
```

**规则**：
- 仅调用 `PUT /api/datasets/{owner}/{slug}` 更新元信息，不创建新版本
- `dataset_status=pending_review` 时页面只读，保存按钮禁用，并提示“审核中暂不可编辑”
- 若建议涉及文件内容调整，点击「创建修订版本」进入 P15（两步流程）

---

### P15 数据集新增版本（两步流程）

与 P08/P09 保持一致，新增版本也采用两步上传：
- 步骤 1/2：文件变更（继承上一版本文件，可替换/移除/新增）
- 步骤 2/2：信息填写（结构与 P09 对齐，包含版本说明 + 元信息 + 文件说明）
- 新增版本入口由详情页右侧底部 `+ New Version` 触发
- 若 V1 未完成文件描述/列说明必填项，`+ New Version` 按钮禁用
- 未改动文件默认继承，不需要重复上传；仅新增或替换文件需要重新补充描述
- 步骤 2 页面默认预填上一版本元信息，作者可直接修改后提交
- 新增版本创建前，系统校验“版本说明 + 本次涉及文件描述/列说明”完整性
- P15 页面不展示管理员反馈正文与处理动作，统一通过 P14 消息中心进入
- 若当前数据集有待处理管理员建议，P15 保存时弹出“是否一并标记为已处理”确认

**步骤 1/2：上传文件变更**（点击 `+ New Version` 后进入）：

```
┌──────────────────────────────────────────────────────────┐
│  新增版本  步骤 1/2：上传文件变更（V2 → V3）              │
│  ●──────○                                                 │
├──────────────────────────────────────────────────────────┤
│  继承文件（默认保留，无需重复上传）                        │
│  📊 train_set.csv  (4.2 MB)   [保留] [替换] [移除]        │
│  📊 test_set.csv   (1.1 MB)   [保留] [替换] [移除]        │
│                                                           │
│  + 添加新文件                                              │
│  配额：1.54 MB / 5 GB                                     │
│                                                           │
│  变更预览：+ 新增 0  ~ 替换 1  - 移除 0                   │
├──────────────────────────────────────────────────────────┤
│                  [取消]  [下一步：填写信息 →]             │
└──────────────────────────────────────────────────────────┘
```

**步骤 2/2：填写信息并提交**（与 P09 一致）：

```
┌──────────────────────────────────────────────────────────┐
│  新增版本  步骤 2/2：填写信息（V2 → V3）                  │
│  ●──────●                                                 │
├──────────────────────────────────────────────────────────┤
│  版本信息                                                  │
│  版本说明（V3）*                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 新增500条数据；修正ligand列命名；补充来源链接      │    │
│  └──────────────────────────────────────────────────┘    │
│  建议写明：数据来源、修改范围、兼容性影响                 │
│                                                           │
│  相对 V2 的变更摘要（自动生成，可补充备注）                │
│  + 新增文件：0   ~ 替换文件：1   - 删除文件：0            │
│  备注（写入 change_manifest）：                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 修正 ligand 命名；新增 500 条反应；补充 DOI        │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
├──────────────────────────────────────────────────────────┤
│  数据集基本信息（默认沿用 V2，可按需修改）                 │
│  数据集标题 * / 描述 * / Tag * / 来源类型 * / License *    │
│  来源链接/DOI / 作者信息（均预填，可编辑）                  │
│  （状态不可直接编辑，由底部按钮动作决定）                    │
│                                                           │
├──────────────────────────────────────────────────────────┤
│  文件信息（仅本次新增/替换文件必填）                        │
│  ── train_set.csv（替换）──────────────────────────────  │
│  关于该文件：该文件还没有任何描述。                  [编辑] │
│  点击[编辑]后展开：表描述 * + 列说明（逐列填写，与 P09 相同）│
│                                                           │
│  ── reagent_map.xlsx（新增）───────────────────────────  │
│  关于该文件：该文件还没有任何描述。                  [编辑] │
│                                                           │
│  其余继承文件（未改动）默认沿用 V2 说明，支持只读查看        │
├──────────────────────────────────────────────────────────┤
│    [← 返回文件变更]   [保存草稿]   [创建新版本 V3]          │
│     仅保存本次编辑                需全部必填项校验通过       │
└──────────────────────────────────────────────────────────┘
```

**按钮行为说明与约束**：
- **[保存草稿]**：保存草稿版本的填写进度（version_note、change_manifest、元信息），调用 `PUT /api/datasets/{id}/versions/{n}` 更新该草稿版本记录。若同时修改了数据集级别的元信息（标题/描述/Tag 等），则先调用 `PUT /api/datasets/{owner}/{slug}` 再调用版本更新接口。该版本状态维持 `draft`。
- **[创建新版本 V3]**：语义等同于“提交上线审核”。前端需调用 `POST /api/datasets/{id}/submit-review`，请求体为 `{ "version_num": 3 }`，后端将该版本 `dataset_versions.status` 更新为 `pending_review`，同时将数据集的 `dataset_status` 推进到 `pending_review`，并在 `dataset_review_requests.pre_review_status` 中记录变更前状态。此时不允许再调用版本创建接口。

编辑保存联动提示（仅存在待处理建议时出现）：

```
┌──────────────────────────────────────────────┐
│  检测到 1 条待处理管理员建议                  │
│  是否在本次保存后标记为「已处理」？            │
│                                  [否] [是]   │
└──────────────────────────────────────────────┘
```

---

### P11 管理员登录页

```
独立路由：/admin/login
不在主导航显示

┌──────────────────────────────────────────┐
│  RxnCommons 管理后台                      │
│                                          │
│  邮箱                                    │
│  ┌──────────────────────────────────┐   │
│  │                                  │   │
│  └──────────────────────────────────┘   │
│                                          │
│  密码                                    │
│  ┌──────────────────────────────────┐   │
│  │                                  │   │
│  └──────────────────────────────────┘   │
│                                          │
│  [    登录管理后台    ]                   │
└──────────────────────────────────────────┘
```

---

### P12 管理员控制台

**布局**：

```
┌──────────────────────────────────────────────────────────┐
│  [Logo] RxnCommons 管理后台    数据集  用户  [退出登录]   │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  数据集管理                                               │
│                                                           │
│  [全部] [待审核] [已发布] [待修订] [归档] [草稿] [已下架] 搜索:[_______] │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 标题/版本       用户      提交时间    状态      操作│  │
│  ├────────────────────────────────────────────────────┤  │
│  │ Suzuki_.../V2   yi_zhang  2026-03-13  待审核       │  │
│  │                                       [查看] [审核] [建议]│
│  ├────────────────────────────────────────────────────┤  │
│  │ Buchwald_.../V1 doyle_g   2026-02-21  已发布       │  │
│  │                                       [查看] [建议] [下架]│
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

**审核详情抽屉**（点击「审核」触发）：

```
┌──────────────────────────────────────────────────────────┐
│  审核请求 #R20260313-018                                   │
│  数据集：Suzuki_coupling_HTE   申请版本：V2               │
│  申请人：yi_zhang   提交时间：2026-03-13 14:22            │
├──────────────────────────────────────────────────────────┤
│  元数据信息（提交内容）                                    │
│  标题、描述、Tag、来源类型、来源链接/DOI、License、作者列表 │
│  版本说明：新增500条样本，统一ligand命名...                │
├──────────────────────────────────────────────────────────┤
│  文件信息（逐文件审查）                                    │
│  train_set.csv 4.2MB  4000行/12列                         │
│  - 文件描述：已填写                                         │
│  - 列说明完成度：12/12                                      │
│  - 预览：前5行（只读）                                      │
│  test_set.csv 1.1MB  1000行/12列                          │
│  - 文件描述：已填写                                         │
│  - 列说明完成度：12/12                                      │
├──────────────────────────────────────────────────────────┤
│  合规检查清单                                               │
│  ☑ License 合法  ☑ 来源可追溯  ☑ 文件扫描通过  ☑ 元信息完整 │
│                                                           │
│  审核意见（驳回必填）                                      │
│  ┌──────────────────────────────────────────────────┐    │
│  │                                                 │    │
│  └──────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────┤
│  历史审核记录（折叠）                                      │
│  ▸ 2026-02-28  rejected  "请补充来源链接与作者信息"       │
│  ▸ 2026-03-05  pending   "等待本次审核"                   │
├──────────────────────────────────────────────────────────┤
│      [驳回并通知用户]      [通过并上线]                   │
└──────────────────────────────────────────────────────────┘
```

说明：驳回/通过结果都会写入 `dataset_review_requests`，并通过 `P14 /messages` 通知作者。

**推送建议弹窗**（点击「建议」触发）：

```
┌─────────────────────────────────────────────────┐
│  向用户推送建议                                   │
│  数据集：Suzuki_coupling_HTE                      │
│                                                   │
│  建议内容 *                                       │
│  ┌─────────────────────────────────────────┐    │
│  │ 建议统一 ligands 命名，并补充数据来源说明      │    │
│  └─────────────────────────────────────────┘    │
│                                                   │
│  状态动作（可选）：                                │
│  □ 同时将数据集标记为 revision_required            │
│                                                   │
│              [取消]  [推送给用户]                 │
└─────────────────────────────────────────────────┘
```

推送后，消息将进入用户 `P14 /messages`，并在已登录页面 NAVBAR 显示未读提示（红点/计数）。

---

### P13 管理员用户管理

```
┌──────────────────────────────────────────────────────────┐
│  用户管理                              搜索: [_________] │
│                                                           │
│  ┌───────────────────────────────────────────────────┐   │
│  │ 用户名      邮箱           注册时间  数据集数  存储 │   │
│  ├───────────────────────────────────────────────────┤   │
│  │ yi_zhang    yi@pku.edu.cn  2025-01  5        1.5M │   │
│  │             [查看数据集] [调整配额] [封禁]           │   │
│  └───────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## 9. 页面跳转逻辑

```
访客进入 P01（首页）
  ├── 点击「浏览数据集」→ P02
  ├── 点击「上传数据集」→ P06（登录）→ P08
  ├── 点击搜索框回车 → P02（带搜索参数）
  ├── 点击「注册」→ P05
  └── 点击「登录」→ P06

P02（数据集市场）
  ├── 点击任意数据集卡片 → P03
  └── 点击「下载」（未登录）→ P06 → 返回 P03

P03（数据集详情）
  ├── 点击版本历史中的「查看」→ P04（历史版本）
  ├── 点击头部「下载当前版本（全量）」（未登录）→ P06
  ├── 点击右侧文件「下载」（未登录）→ P06
  ├── 点击「Upvote」（未登录）→ P06
  ├── 点击「复制数据集链接/复制当前版本链接」→ 留在当前页（复制成功提示）
  ├── 点击「归档/取消归档」（所有者）→ 留在 P03（状态切换）
  ├── 点击「编辑」（所有者）→ P10
  └── 点击右侧底部「+ New Version」（所有者，且 V1 已完成）→ P15 步骤1（文件变更）

P04（历史版本）
  └── 点击横幅「查看最新版本」→ P03

P05（注册）
  ├── 注册成功 → 留在当前页（提示“请查收验证邮件”）
  └── 点击邮件链接 → P18 → P06

P06（登录）
  └── 登录成功
      ├── 如来自需要登录的操作 → 返回原页面
      └── 否则 → P07（个人主页）
  └── 若邮箱未验证 → 允许登录但限制上传/评论/点赞，并提示可重发验证邮件
  └── 点击「忘记密码」→ P16

P16（忘记密码）
  ├── 点击「发送重置邮件」→ 留在 P16（提示邮件已发送）
  └── 点击邮件链接 → P17

P17（重置密码）
  └── 点击「确认重置」→ P06（重新登录）

全局消息入口（任意已登录页面）
  ├── 点击 NAVBAR「消息」→ P14（消息中心）
  ├── 点击消息「查看详情」→ 对应数据集 P03
  └── 点击消息「查看并处理」→ P10（元信息编辑）

P07（个人主页）
  ├── 点击「+ 上传新数据集」→ P08
  ├── 点击「进入消息中心」→ P14
  ├── 点击「查看并处理」（消息摘要）→ P10（元信息编辑）
  ├── 点击「归档/取消归档」→ 留在 P07（状态切换）
  ├── 点击数据集「编辑」→ P10
  └── 点击数据集标题 → P03

P14（消息中心）
  ├── 点击「查看数据集」→ P03
  ├── 点击「去处理」→ P10（元信息编辑）
  └── 点击「标记已读」→ 留在 P14（状态更新）

P08（上传步骤一）
  ├── 文件上传完成，点击「下一步」→ P09
  └── 点击「取消」→ P07

P09（上传步骤二）
  ├── 点击「保存草稿」→ P03（状态为草稿）
  ├── 点击「提交上线审核」→ P03（状态为待审核）
  └── 点击「← 返回」→ P08

P10（元信息编辑）
  ├── 点击「保存元信息」→ 留在 P03（不升版本）
  ├── 点击「创建修订版本」→ P15 步骤1
  └── 点击「取消」→ 返回 P03

P15（新增版本两步）
  ├── 步骤1：文件变更完成，点击「下一步」→ 步骤2（信息填写）
  ├── 步骤2：点击「创建新版本」→ P03（切到最新版本）
  └── 任一步骤点击「取消」→ 返回 P03

P11（管理员登录）
  └── 登录成功 → P12

P12（管理员控制台）
  ├── 点击「查看」→ P03
  ├── 点击「审核」→ 打开审核详情抽屉（元数据+文件信息）
  ├── 审核通过 → P03（状态变为已发布）
  ├── 审核驳回 → P14（用户收到驳回原因消息）
  ├── 点击「下架」→ P03（状态变为已下架）
  ├── 点击「建议」→ 弹出推送弹窗
  └── 点击顶部「用户」→ P13

P13（用户管理）
  └── 点击「查看数据集」→ P02（筛选该用户）
```

---

## 10. 安全策略（上线必做）

### 10.1 鉴权与会话安全

- 密码必须使用强哈希算法（Argon2id 或 bcrypt），禁止使用可逆加密
- Access Token 短时有效（15 分钟），Refresh Token 长时有效（7 天）并强制轮换
- Refresh Token 仅以 hash 存储；登出、改密、封禁时立即批量撤销
- 密码重置采用一次性短时 token，重置成功后撤销该用户全部 Refresh Token
- 管理员后台登录与普通登录分离
- MFA（TOTP）列为 v2 安全增强项：v1 预留扩展位，但本期不强制开发独立的 MFA 数据表、绑定流程和验证页面，避免超出当前交付范围

### 10.2 权限模型与越权防护

- 后端执行 RBAC + 对象级鉴权，前端权限判断仅用于 UI 展示
- 所有 `dataset/file/version` 接口在查询后再次校验 owner/状态可公开/admin
- `file_id`、`dataset_id` 等外部可见 ID 不能作为直接授权依据
- 管理员高危操作（下架、调配额、封禁）要求二次确认并写审计日志

### 10.3 上传与文件安全

- 文件上传采用“隔离区 -> 扫描 -> 正式区”三段式流程
- 启用恶意文件扫描（如 ClamAV）；扫描失败或超时时默认拒绝发布
- 限制压缩包解压深度、解压后总大小与文件数，防 zip bomb
- 文件名净化后再入库，对象键由系统生成，禁止路径拼接

### 10.4 应用层防护

- API 限流：登录、上传、下载、搜索、评论分别配置阈值
- 登录防爆破：连续失败达到阈值触发短时冻结与人机校验
- 输入严格校验：长度、类型、枚举、URL/DOI 格式；拒绝未声明字段
- 输出安全：用户内容渲染前做 XSS 过滤；错误响应隐藏内部实现细节

### 10.5 数据与基础设施安全

- 对象存储默认私有，下载采用短时签名 URL（例如 60 秒过期）
- 传输全链路 HTTPS；强制 HSTS，关闭弱 TLS 套件
- 数据库与对象存储最小权限访问，生产密钥使用密钥管理系统托管
- 每日备份数据库与元数据，至少每季度执行一次恢复演练

### 10.6 审计与告警

- 建立审计事件最小集合：登录失败、token 撤销、越权拒绝、管理员操作
- 安全日志集中存储，保留不少于 180 天，并按用户/IP 可检索
- 异常告警：爆破登录、下载突增、批量失败上传、异常管理员行为
- 安全响应 SLO：高危告警 30 分钟内确认，24 小时内给出处置结论

---

## 11. 部署方案

### 11.1 开发环境

```bash
# 前端
cd frontend && npm run dev          # Next.js 开发服务器 :3000

# 后端
cd backend && uvicorn main:app --reload   # FastAPI :8000

# 异步 Worker
cd backend && celery -A worker.app worker -l info

# 定时任务
cd backend && celery -A worker.app beat -l info

# 依赖服务
docker-compose up postgres redis minio clamav   # 本地依赖
```

### 11.2 生产环境架构

```
用户 → CDN/WAF/Nginx（反向代理 + HTTPS + 缓存）
   ├── / → Next.js（前端）
   └── /api → FastAPI（后端 API）

FastAPI → PostgreSQL（主数据库 + 搜索读模型）
  → Redis（会话 + 缓存 + 限流 + Broker）
  → MinIO（文件存储）
  → ClamAV（上传扫描）

Celery Worker → Redis（取任务）
        → PostgreSQL（更新元数据/检索投影）
        → MinIO（生成预览/清理文件）
        → ClamAV（补偿扫描）

Celery Beat / Scheduler → Redis（定时投递任务）
           → Worker（定时巡检、投影重建、失败重试）
```

### 11.3 docker-compose 服务清单

```yaml
services:
  frontend:    # Next.js，端口 3000
  backend:     # FastAPI，端口 8000
  worker:      # Celery Worker，处理解析/清理/投影
  scheduler:   # Celery Beat / 定时任务
  postgres:    # PostgreSQL 15
  redis:       # Redis 7
  minio:       # MinIO 对象存储
  clamav:      # 文件恶意内容扫描
  nginx:       # 反向代理
```

### 11.4 关键环境变量

```
DATABASE_URL          PostgreSQL 连接串
REDIS_URL             Redis 连接串
CELERY_BROKER_URL     异步任务 Broker 连接串
CELERY_RESULT_BACKEND 异步任务结果存储连接串
MINIO_ENDPOINT        MinIO 地址
MINIO_ACCESS_KEY      MinIO 密钥
MINIO_SECRET_KEY      MinIO 密钥
JWT_SECRET            JWT 签名密钥
ACCESS_TOKEN_EXPIRE_MIN   Access Token 过期分钟数（建议 15）
REFRESH_TOKEN_EXPIRE_DAYS Refresh Token 过期天数（建议 7）
REFRESH_TOKEN_COOKIE_SECURE 是否仅 HTTPS 发送 Refresh Cookie
RATE_LIMIT_REDIS_URL       限流存储连接串
CORS_ALLOW_ORIGINS         允许跨域来源白名单
SECURITY_ALERT_WEBHOOK      安全告警推送地址
PASSWORD_RESET_TOKEN_EXPIRE_MIN  重置 token 过期分钟数（建议 30）
PASSWORD_RESET_SECRET      密码重置 token 签名密钥
EMAIL_VERIFY_TOKEN_EXPIRE_MIN    邮箱验证 token 过期分钟数（建议 1440）
EMAIL_VERIFY_SECRET              邮箱验证 token 签名密钥
SMTP_HOST                 邮件服务器地址
SMTP_PORT                 邮件服务器端口
SMTP_USER                 邮件账号
SMTP_PASSWORD             邮件密码或授权码
MAIL_FROM                 发件人地址
ADMIN_EMAIL           管理员邮箱（初始化）
ADMIN_PASSWORD        管理员密码（初始化）
```

---

## 12. 研发团队落地与交付规范

为保证该文档顺利转化为代码落地，第三方开发团队需遵守以下配套要求：

### 12.1 业务边界与化学领域说明
- **纯托管定位**：本平台 v1 版本定位为通用文件托管系统，**不进行**深度的化学结构语义解析（不强制后端依赖 RDKit 校验 SMILES 合法性）。仅将其视为普通文本字符串处理。
- **未来扩展预留**：前端若需要预览 SMILES 结构，推荐轻量级引入 `SMILES Drawer` 或 `Ketcher` 以 Canvas 方式渲染，不依赖后端计算。

### 12.2 开发前置物料要求
- **高保真 UI/UX 设计图**：开发前必须基于本文档提供完整的 Figma 交互与 UI 高保真设计图，定义精确的色彩规范、字体排版以及各类控件的异常状态（Hover/Active/Disabled）。文档中终端字符画仅为逻辑示意，不能替代 UI 稿。
- **API Swagger/OpenAPI 文档**：开发首周需产出标准化 API 契约（OpenAPI 3.0 规范），明确复杂接口的入参出参结构及精确错误码定义定义（400/403/422 具体格式等）。

### 12.3 第三方服务依赖约定
- **邮件服务**：后端需集成第三方邮件服务（如 SendGrid、阿里云邮件推送）用于注册验证与密保找回，团队需要开发相应的邮件 HTML 模板。
- **国际化 (i18n)**：平台面向国际学术社区，前端需引入 `react-i18next` 或 `next-intl`。UI文案需支持中英双语，代码硬编码阶段应预留占位符，上线首期默认语言须为英语（English），占位设计稿及数据库均应以此为准。

**邮件模板最小集合（英文首发，必须）**：

1. Verify Email
- Subject: `Verify your RxnCommons email address`
- Header: `Welcome to RxnCommons`
- Body: `Please confirm your email address to activate upload, comment, and upvote permissions.`
- CTA: `Verify Email`
- Footer: `If you did not create this account, you can ignore this email.`

2. Reset Password
- Subject: `Reset your RxnCommons password`
- Header: `Password reset requested`
- Body: `We received a request to reset your password. This link will expire in 30 minutes.`
- CTA: `Reset Password`
- Footer: `If you did not request a password reset, no further action is required.`

3. Review Approved
- Subject: `Your dataset has been published on RxnCommons`
- Header: `Dataset published`
- Body: `Your dataset review has been approved and the latest version is now publicly available.`
- CTA: `View Dataset`

4. Review Rejected / Revision Required
- Subject: `Action required for your RxnCommons dataset`
- Header: `Review update`
- Body: `Your dataset requires changes before publication or further revision. Please review the feedback in your message center.`
- CTA: `Open Message Center`

说明：以上文案为默认英文模板；中文模板采用同结构翻译，不允许由开发团队自行发挥改写核心含义。

### 12.4 系统初始化策略
- **Root 管理员限制**：系统不设管理员公开注册。需在部署脚本中实现后端命令行工具（如 `python manage.py createsuperuser`）创建「一号管理员」，再由该管理员通过后台系统完成后续管理员的分发。

---

*文档结束 | RxnCommons v1.0 系统设计方案*
