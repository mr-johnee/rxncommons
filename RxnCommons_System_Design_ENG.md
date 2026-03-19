# RxnCommons System Overall Design Plan

> Version: v1.0 | Date: 2026-03-13

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [User Classification and Permissions](#2-user-classification-and-permissions)
3. [Technical Architecture](#3-technical-architecture)
4. [Database Design](#4-database-design)
5. [File Storage Solution](#5-file-storage-solution)
6. [Backend API Design](#6-backend-api-design)
7. [Frontend Framework and Pages Overview](#7-frontend-framework-and-pages-overview)
8. [Detailed Design of Each Page](#8-detailed-design-of-each-page)
9. [Page Redirection Logic](#9-page-redirection-logic)
10. [Security Strategy (Mandatory Before Launch)](#10-security-strategy-mandatory-before-launch)
11. [Deployment Plan](#11-deployment-plan)

---

## 1. Project Overview

### 1.1 Platform Positioning

RxnCommons is a **chemical reaction dataset sharing platform** geared towards the chemical research community, similar to Kaggle but specifically focused on chemical reaction data.

### 1.2 Core Principles

| Principle | Description |
|-----------|-------------|
| Data Originality | The platform does not modify any data content uploaded by users. |
| Information Transparency | Meta-information, Tags, and column descriptions are publicly displayed to help users evaluate the data. |
| Security First | Default deny, principle of least privilege, strict backend validation. |
| Delegation of Choice | Decision-making power over data is handed over to users through community voting and discussions. |
| Academic Rigor | Version control, citation formats, and DOI support to meet academic citation requirements. |

### 1.3 Scope of Platform Features

- Uploading, storing, retrieving, and downloading chemical reaction datasets.
- Tag-based dataset categorization and retrieval.
- Community voting (Upvote) mechanism.
- Dataset version control.
- Administrator review and suggestion push.

---

## 2. User Classification and Permissions

### 2.1 User Types

```
Unregistered Guest
Inactive User (Registered but email not verified, to prevent abuse)
Regular Registered User (Email verified)
Administrator (Configured in the backend, no public registration entry)
```

### 2.2 Permissions Matrix

| Function | Unregistered Guest | Inactive User | Regular User | Administrator |
|----------|-------------------|---------------|--------------|---------------|
| Browse Homepage | ✅ | ✅ | ✅ | ✅ |
| Browse Dataset List | ✅ | ✅ | ✅ | ✅ |
| View Dataset Details | ✅ | ✅ | ✅ | ✅ |
| Download Dataset | ❌ | ✅ | ✅ | ✅ |
| Upload Dataset | ❌ | ❌ | ✅ | ✅ |
| Upvote | ❌ | ❌ | ✅ | ✅ |
| Participate in Discussions | ❌ | ❌ | ✅ | ✅ |
| Manage Own Datasets | ❌ | ❌ | ✅ | ✅ |
| View All User Datasets (including private) | ❌ | ❌ | ❌ | ✅ |
| Push Modification Suggestions to Users | ❌ | ❌ | ❌ | ✅ |
| Takedown Dataset | ❌ | ❌ | ❌ | ✅ |
| User Management | ❌ | ❌ | ❌ | ✅ |

---

## 3. Technical Architecture

### 3.1 Overall Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                      User Browser                       │
└──────────────────────────┬──────────────────────────────┘
            │ HTTPS
┌──────────────────────────▼──────────────────────────────┐
│                  Nginx / CDN / WAF Layer                │
│       HTTPS Termination + Static Cache + Basic WAF      │
└───────────────┬───────────────────────┬─────────────────┘
      │                       │
┌───────────────▼──────────────┐   ┌────▼─────────────────┐
│       Frontend (Next.js)     │   │   Backend API (FastAPI)│
│ React Components+Tailwind+SWR│   │ Routing→Business→Data│
└──────────────────────────────┘   └────┬─────────────────┘
                │
          ┌───────────────┼────────────────┬──────────────────┐
          │               │                │                  │
      ┌────────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐  ┌────────▼────────┐
      │ PostgreSQL    │ │   Redis     │ │   MinIO     │  │ File Security   │
      │ Primary+Read  │ │Session/Queue│ │Object Store │  │ Scanner (Isol.) │
      └────────┬──────┘ └──────┬──────┘ └─────────────┘  └─────────────────┘
          │               │
      ┌────────▼────────┐ ┌────▼──────────────┐
      │ Celery Worker   │ │ Scheduler / Beat  │
      │ Parse/Preview/  │ │ Cron/Retry/Comp.  │
      └─────────────────┘ └───────────────────┘
```

### 3.2 Frontend Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14+ | React framework, SSR/SSG |
| TailwindCSS | 3+ | Styling system |
| SWR | 2+ | Data fetching and caching |
| Zustand | 4+ | Client-side state management |
| React Table | 8+ | Data table rendering |
| React Dropzone | — | Drag-and-drop file upload |

### 3.3 Backend Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.110+ | API framework |
| SQLAlchemy | 2+ | ORM |
| PostgreSQL | 15+ | Primary database |
| pg_trgm / PostgreSQL FTS | — | Support for title/Tag search and sorting (no separate ES required) |
| Redis | 7+ | Cache + Sessions + Rate Limiting + Message Queue Broker |
| Celery / RQ | — | Asynchronous task queue (large file parsing, physical file cleanup) |
| MinIO | — | Object storage (S3 compatible) |
| ClamAV | — | Malicious content scanning for uploaded files |
| Pandas / openpyxl | 2+ | CSV streaming and Excel row-by-row parsing to prevent OOM |
| python-magic | — | File type detection |
## 4. Database Design

### 4.1 Core Data Tables

#### `users` (User Table)

```sql
CREATE TABLE users (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username      VARCHAR(50) UNIQUE NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    institution   VARCHAR(255),
    research_area VARCHAR(255),
    role          VARCHAR(20) DEFAULT 'user',  -- 'user' | 'admin'
    storage_used  BIGINT DEFAULT 0,            -- Unit: bytes
    storage_quota BIGINT DEFAULT 5368709120,   -- Default 5GB (regular users)
    is_active     BOOLEAN DEFAULT TRUE,
    is_email_verified BOOLEAN DEFAULT FALSE,   -- Email verified status (abuse prevention)
    created_at    TIMESTAMP DEFAULT NOW(),
    last_login    TIMESTAMP
);
```

#### `physical_storage_objects` (Physical Storage Object Table)

```sql
CREATE TABLE physical_storage_objects (
    file_key        VARCHAR(500) PRIMARY KEY, -- MinIO persistent object key
    owner_id        UUID NOT NULL REFERENCES users(id),
    file_size       BIGINT NOT NULL,
    ref_count       INTEGER DEFAULT 0,        -- Reference count (cross-version reuse count)
    upload_status   VARCHAR(20) DEFAULT 'pending', 
    created_at      TIMESTAMP DEFAULT NOW()
);
```
**Design Purpose**: To address the issues of "physical deduplication" and "quota deduction black holes" when inheriting files with the same name across multiple versions. The user's `storage_used` is strictly tied to this table. To implement user-level deduplication and prevent cross-user quota billing confusion, `file_key` is strictly engineered using the format `{owner_id}_{sha256}`. Inheriting files in a new version triggers `ref_count + 1`; only when deleting a historical version drops the `ref_count` to `0` will the MinIO file be asynchronously deleted across transactions, and the storage quota refunded.

#### `datasets` (Dataset Table)

```sql
CREATE TABLE datasets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id        UUID REFERENCES users(id),
    slug            VARCHAR(255) NOT NULL,     -- URL-friendly name (spaces to underscores)
    title           VARCHAR(255) NOT NULL,
    description     TEXT NOT NULL,
    source_type     VARCHAR(50),               -- 'lab' | 'literature' | 'patent' | 'database' | 'other'
    source_ref      VARCHAR(500),              -- DOI / Patent number / URL
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

-- Use a partial unique index instead of a UNIQUE constraint to allow the same user to reuse the original name (slug) after a soft deletion
CREATE UNIQUE INDEX uniq_dataset_slug_active ON datasets(owner_id, slug) WHERE deleted_at IS NULL;

CREATE INDEX idx_datasets_dataset_status ON datasets(dataset_status);
```

**Note**: The `datasets` table no longer retains the `visibility` field. Visibility is entirely determined by `dataset_status` (`published`/`revision_required`/`archived` are public, others are private).

#### `dataset_tags` (Dataset Tag Table)

```sql
CREATE TABLE dataset_tags (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    tag        VARCHAR(100) NOT NULL,         -- Must be converted to lowercase and regex-filtered before writing
    tag_type   VARCHAR(20) DEFAULT 'custom',  -- 'task' | 'field' | 'custom'
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(dataset_id, tag)                   -- Prevent duplicate redundant tags
);

CREATE INDEX idx_dataset_tags_tag ON dataset_tags(tag);
```

**Tag Usage Conventions (Field coverage is expressed via Tags)**

- `task`: Task-related tags, e.g., `yield_prediction`, `condition_prediction`, `retrosynthesis`.
- `field`: Field-related tags, e.g., `has_yield_data`, `has_solvent_data`, `has_ligand_data`.
- `custom`: User-defined tags, e.g., specific reaction types, substrate families, data source characteristics.

#### `dataset_authors` (Dataset Author Table)

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

#### `dataset_versions` (Dataset Version Table)

```sql
CREATE TABLE dataset_versions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id   UUID REFERENCES datasets(id) ON DELETE CASCADE,
    version_num  INTEGER NOT NULL,
    status       VARCHAR(20) DEFAULT 'draft',    -- 'draft' | 'pending_review' | 'published' | 'rejected'
    version_note TEXT,                           -- Can be null during draft phase; must be non-null before submitting for publication review
    base_version_num INTEGER,                    -- The previous version number this version's changes are based on; null for V1
    download_count INTEGER DEFAULT 0,            -- Download count for this version
    metadata_complete BOOLEAN DEFAULT FALSE,     -- Server-side validation result: whether all file/column descriptions are complete for this version
    change_manifest JSONB,                       -- Change manifest relative to the previous version (fixed JSON schema, see below)
    created_at   TIMESTAMP DEFAULT NOW(),
    created_by   UUID REFERENCES users(id),
    UNIQUE(dataset_id, version_num)
);
```

`change_manifest` JSON Schema Convention (Unified across frontend and backend):

```json
{
  "files_added": ["reagent_map.xlsx"],
  "files_replaced": ["train_set.csv"],
  "files_removed": [],
  "metadata_changed": ["description", "source_ref"],
  "note": "Fixed ligand naming; added 500 new reactions"
}
```

#### `dataset_files` (Logical File Table)

```sql
CREATE TABLE dataset_files (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id      UUID NOT NULL REFERENCES dataset_versions(id) ON DELETE CASCADE,
    filename        VARCHAR(500) NOT NULL,
    file_key        VARCHAR(500) NOT NULL REFERENCES physical_storage_objects(file_key),
    description     TEXT,                   -- File description, required when published
    row_count       INTEGER,                -- Parsed row count
    col_count       INTEGER,                -- Parsed column count
    error_message   TEXT,                   -- Error reason if parsing or scanning fails
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(version_id, filename)
);
```

#### `file_columns` (File Column Table)

```sql
CREATE TABLE file_columns (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id         UUID REFERENCES dataset_files(id) ON DELETE CASCADE,
    column_name     VARCHAR(255) NOT NULL,
    column_index    INTEGER NOT NULL,
    description     TEXT,                   -- Column description, required when published
    null_rate       NUMERIC(5,2),           -- Missing rate %
    unique_count    INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);
```

**Version Inheritance Persistence Rules (Mandatory):**

1. When a new version inherits an old file, create a new `dataset_files` record (associated with the new `version_id`); do not reuse the old `id`.
2. If the file content remains unchanged, the old `file_key` can be reused (pointing to the same object storage file) to avoid duplicate storage.
3. Synchronously clone `file_columns` records when inheriting a file, associating them with the new `file_id`.
4. Any modifications to file descriptions/column descriptions for a given version only affect the current version's records and are not written back to historical versions.
5. `version_id` is the single source of truth for version attribution; all file upload, inheritance, and deletion actions must resolve to the target `version_id` before persistence.
6. `base_version_num` must be written when creating V2+ to immutably record the comparison baseline for that version; even if the frontend displays a change manifest in the future, it must not rely on "dynamically computing the previous version".

#### `upvotes` (Upvote Table)

```sql
CREATE TABLE upvotes (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    user_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(dataset_id, user_id)
);
```

#### `discussions` (Discussion Table)

```sql
CREATE TABLE discussions (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    user_id    UUID REFERENCES users(id),
    content    TEXT NOT NULL,
    root_id    UUID REFERENCES discussions(id) ON DELETE CASCADE, -- Top-level comment ID; null if it is the root comment
    parent_id  UUID REFERENCES discussions(id) ON DELETE CASCADE, -- Target ID being replied to (can be a sibling or child)
    deleted_at TIMESTAMP,                        -- Soft deletion timestamp
    deleted_by UUID REFERENCES users(id),        -- User who deleted it
    created_at TIMESTAMP DEFAULT NOW(),
    edited_at  TIMESTAMP,                        
    updated_at TIMESTAMP DEFAULT NOW()           
);
CREATE INDEX idx_discussions_root_id ON discussions(root_id);
```

**Optimization**: Introduced `root_id` to avoid time-consuming Recursive CTEs (recursive queries) in infinitely nested scenarios. All child replies are forcibly flattened and associated with their top-level primary comment, simplifying list queries to `O(1)` for superior performance (similar to a two-level comment tree design).

#### `admin_suggestions` (Admin Suggestion Table)

```sql
CREATE TABLE admin_suggestions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id  UUID REFERENCES datasets(id) ON DELETE CASCADE,
    recipient_user_id UUID REFERENCES users(id),        -- Dataset author (message recipient)
    admin_id    UUID REFERENCES users(id),
    version_num INTEGER,                                -- The dataset version the suggestion targets
    content     TEXT NOT NULL,
    status      VARCHAR(20) DEFAULT 'pending',          -- 'pending' | 'resolved' | 'dismissed'
    is_read     BOOLEAN DEFAULT FALSE,                  -- Read status
    created_at  TIMESTAMP DEFAULT NOW(),
    read_at     TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX idx_admin_suggestions_recipient_status
    ON admin_suggestions(recipient_user_id, status, is_read);
```

#### `dataset_review_requests` (Dataset Publication Review Request Table)

```sql
CREATE TABLE dataset_review_requests (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id    UUID REFERENCES datasets(id) ON DELETE CASCADE,
    version_id    UUID NOT NULL REFERENCES dataset_versions(id) ON DELETE CASCADE,
    version_num   INTEGER NOT NULL,                 -- Version number submitted for review
    requester_id  UUID REFERENCES users(id),        -- Submitter (usually the owner)
    pre_review_status VARCHAR(30),                  -- Dataset status prior to review submission (used for precise rollback upon rejection)
    status        VARCHAR(20) DEFAULT 'pending',    -- 'pending' | 'approved' | 'rejected' | 'canceled_by_user'
    submit_note   TEXT,                             -- Author's supplementary notes (optional)
    decision_note TEXT,                             -- Admin review feedback
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

#### `notifications` (Global Notification Table)

```sql
CREATE TABLE notifications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    actor_id    UUID REFERENCES users(id),                -- User/Admin who triggered the action (nullable)
    target_type VARCHAR(50) NOT NULL,                     -- Source type: 'review_request', 'admin_suggestion', 'discussion', 'system'
    target_id   UUID,                                     -- Associated business record ID
    title       VARCHAR(255) NOT NULL,                    -- Short message title
    content     TEXT,                                     -- Detailed message content / rejection reason
    is_read     BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_notifications_recipient ON notifications(recipient_id, is_read, created_at DESC);
```

**Design Purpose**: The system currently has multiple scenarios that require user notifications, such as replies (`discussions`), reviews (`review_requests`), and suggestions (`admin_suggestions`). If the frontend had to perform a joined query across all child tables to determine the unread count or aggregate the message list, it would incur unnecessary complexity and performance overhead. This table serves as a unified message archive using a publish-subscribe strategy (triggering writes to this table after the primary logic executes successfully).#### dataset_search_documents (Search Read Model Table)

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
    total_rows      INTEGER DEFAULT 0,          -- Total row count of the currently published version (sum of row_count across all files), used for P02 data scale filtering
    total_file_size BIGINT DEFAULT 0,           -- Total file size (bytes) of the currently published version, used for card display
    description     TEXT DEFAULT '',            -- Original dataset description (redundant storage), used for direct return in list APIs
    created_at      TIMESTAMP NOT NULL,         -- Dataset creation time, used for P02 "Recently Uploaded" sorting
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

Usage Description:

- P01 Curated Cards, P02 List Filtering, and Site Search uniformly read from `dataset_search_documents` to avoid multi-table hotspot queries involving JOINs on `datasets + dataset_tags + versions + counters` for online list pages.
- This table is maintained by asynchronous projection tasks: incrementally updated when dataset meta-information, tags, status, or counters change.
- In the v1 phase, introducing Elasticsearch is not mandatory; using a PostgreSQL read model + trigram/FTS is sufficient to support a medium-scale site.

**Projection Triggering Strategy (Mandatory)**:

| Event | Projection Method | Acceptable Latency |
|------|----------|------------|
| Dataset creation / Meta-info update | Dispatch async task after transaction commit | Within 5 seconds |
| Tag change | Dispatch async task after transaction commit | Within 5 seconds |
| Review status change / Archive / Takedown / Restore | Dispatch async task after transaction commit | Within 5 seconds |
| Upvote / Cancel Upvote | Dispatch async task after transaction commit | Within 10 seconds |
| download-all count change | Dispatch async task after transaction commit | Within 30 seconds |
| view_count change | Scheduled batch refresh of read model | Within 5 minutes |

Note: P02 List Page and Search Page allow brief eventual consistency latency in the read model; the latest status and counters on the details page rely on queries to the primary tables.

#### auth_refresh_tokens (Refresh Token Table)

```sql
CREATE TABLE auth_refresh_tokens (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash    VARCHAR(255) NOT NULL,        -- Store hash only, plaintext token is not stored
    issued_at     TIMESTAMP DEFAULT NOW(),
    expires_at    TIMESTAMP NOT NULL,
    revoked_at    TIMESTAMP,
    issued_ip     VARCHAR(64),
    user_agent    VARCHAR(500)
);

CREATE INDEX idx_auth_refresh_tokens_user_id ON auth_refresh_tokens(user_id);
```

#### security_audit_logs (Security Audit Log Table)

```sql
CREATE TABLE security_audit_logs (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type    VARCHAR(100) NOT NULL,      -- E.g., login_failed / token_revoked / admin_action / download_denied
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

### 4.2 Dataset Status Maintenance (Mandatory)

To avoid conflating "visibility" and "governance actions", dataset status is maintained separately in `datasets.dataset_status`:

Platform Constraint: It is strictly prohibited to reintroduce an independent `visibility` field; all public visibility evaluations must uniformly use `dataset_status`.

- `draft`: Draft (default); visible only to the author.
- `pending_review`: Pending review; the author has submitted a publishing request, awaiting administrator review.
- `published`: Published; allowed for public display and download.
- `revision_required`: Revision required; remains publicly visible and downloadable, but the author needs to address administrator suggestions.
- `archived`: Archived; the author actively stops maintenance. Still browsable and downloadable, but Upvotes and discussions are disabled.
- `takedown`: Taken down; actively hidden by the administrator. Visible only to the author and administrators, and download access is closed (**physical space is not reclaimed; supports restoration**).
- `deleted`: Deleted; a soft-delete record initiated by the user (**storage quota is reclaimed, non-restorable, entirely hidden from the frontend**).

**Status Transition Rules**:

1. Create a new dataset and save as a draft: `draft`
2. The author clicks "Submit for Review": `draft/revision_required -> pending_review` (Simultaneously, record the pre-submission status, such as `draft` or `revision_required`, in `dataset_review_requests.pre_review_status`)
3. Administrator approves: `pending_review -> published`
4. Administrator rejects: `pending_review -> pre_review_status` (Revert to the pre-submission status to prevent accidental hiding of previously published foundational records, and record the rejection reason)
5. Administrator pushes critical suggestions (for published data): `published -> revision_required`
6. The author creates a revised version and resubmits: `revision_required -> pending_review`
7. The author actively archives: `published/revision_required -> archived`, and records the `pre_archive_status`
8. The author unarchives: `archived -> pre_archive_status` (Reverts to `published` if empty)
9. Administrator takes down: `* -> takedown`
10. Administrator restores: `takedown -> draft` or `takedown -> published` (depending on the review result)
11. User deletes: `* (current non-takedown status) -> deleted`

Note: The dataset-level `dataset_status` reflects the exposure status of the currently published or submitted version. A new draft version with `dataset_versions.status=draft` exists independently and does not affect the dataset-level status. Only when submitted for review does it trigger a `pending_review` change at the dataset level, and an update to `published` upon release, ensuring online foundational datasets remain undisturbed during this process.

**Frontend Display Conventions**:

- The P03 header displays status badges (`pending_review` / `published` / `revision_required` / `archived` / `takedown`).
- The P07 "My Datasets" list displays status, prioritizing `dataset_status`.
- `revision_required`: Visible and downloadable by visitors; only the author/administrator sees the "Pending Suggestions" prompt.
- `archived`: Visible and downloadable by visitors; Upvote button is hidden, and the discussion input box is closed.
- `archived`: Retrievable by P02 Search and lists by default. Cards and details pages must display the "Archived" status badge. P02 provides status filtering options for users to exclusively view or exclude archived datasets.

### 4.3 Dataset Linking and Sharing Rules (Mandatory)

Every dataset generates a stable slug upon its first save, corresponding to a fixed primary link:

- Primary Link (Latest Version): `/datasets/{owner}/{slug}`
- Version Link (Fixed Version): `/datasets/{owner}/{slug}/v{n}`

**Access and Sharing Rules**:

1. `draft/pending_review/takedown`: Links are accessible only to the author and administrators; other users receive a 403/404 upon access.
2. `published/revision_required/archived`: Primary links can be shared publicly, defaulting to the latest published version.
3. Historical replication experiments / paper citations should use the version link `v{n}` to avoid "latest version drift".
4. The page provides one-click copy functions:
- `Copy Dataset Link` (Primary Link)
- `Copy Current Version Link` (v{n})

### 4.4 Slug Generation Rules (Mandatory)

To ensure stable and readable URLs, the slug rules are uniformly standardized as follows:

1. The slug is generated from the title upon the first save; subsequent title modifications do not affect the slug (links remain permanently stable).
2. Uniformly lowercase; retains only `a-z`, `0-9`, and `_`.
3. Spaces and delimiters (space, `-`, `.`) are uniformly replaced by `_`.
4. Other characters (e.g., `/`, `#`, `%`, Chinese symbols) are removed or replaced by `_`, and consecutive `_` characters are merged.
5. Leading and trailing `_` characters are removed; maximum length is 100 characters (truncated if overly long).
6. If empty after sanitization, fall back to `dataset_{short_id}`.
7. In case of conflicts under the same `owner`, append a suffix (e.g., `_2`, `_3`).

### 4.5 Dataset Deletion and Takedown Semantics (Mandatory Separation)

To avoid data and storage quota conflicts during restoration after an administrator takedown, the hiding of records is divided into two distinct behaviors:

1. **User Active Deletion (Delete `DELETE /api/datasets/{owner}/{slug}`)**
   - Populate `datasets.deleted_at` and `datasets.deleted_by`, and set `dataset_status` to `deleted`.
   - Entirely hidden from the frontend lists and details (not displayed in any status list).
   - **Quota Operation**: Immediately trigger a database-level atomic operation to reclaim the occupied quota (`UPDATE users SET storage_used = storage_used - :size`).
   - **File Cleanup**: Upon soft deletion, simultaneously push a cleanup task encompassing all MinIO physical files into the backend offline asynchronous queue (Celery/RQ) for execution.
   - **Review Cleanup**: If currently in the `pending_review` status, automatically backfill the corresponding `dataset_review_requests` to `canceled_by_user` to prevent dangling waits.

2. **Administrator Takedown (Takedown `PUT /api/admin/datasets/{id}/takedown`)**
   - Set `dataset_status` to `takedown` (do not populate `deleted_at`).
   - Hidden from the public only; still visible to the author/administrators, but cannot be downloaded normally.
   - **Quota Operation**: Do **not** clean up physical files, and do **not** refund the quota.
   - **Review Cleanup**: If currently in the `pending_review` status, similarly backfill the corresponding `dataset_review_requests` to `canceled_by_admin` to avoid dangling waits.
   - Ensure it can subsequently be safely restored to its original normal state (`draft` or `published`) via `restore`.
## 5. File Storage Solution

### 5.1 Storage Structure

Use **MinIO** (AWS S3 API compatible) for object storage. File paths are organized according to the following rules:

```
rxncommons-bucket/
├── objects/
│   └── {owner_id}_{sha256}              ← Physical file: corresponds to physical_storage_objects.file_key
│                                         ← Same content from the same user is stored only once, reused across versions
├── previews/
│   └── {dataset_id}/
│       └── v{n}/
│           └── {file_id}_preview.json   ← First 50 rows preview cache, can be rebuilt on demand
├── archives/
│   └── {dataset_id}/
│       └── v{n}/
│           └── dataset_v{n}.zip         ← Full offline packaged download ZIP
└── avatars/
    └── {user_id}/
        └── avatar.jpg
```

**Path Rule Description**:
- Original files are uniformly stored under `objects/`, using `{owner_id}_{sha256}` as the object key (i.e., `physical_storage_objects.file_key`) to achieve deduplication per user.
- Preview caches and ZIP archives are organized by `dataset_id + version_num`, decoupled from physical files.
- `dataset_files.filename` is purely a logical filename (the original name when uploaded by the user) and is not involved in MinIO object key generation.

### 5.2 Storage Strategy

| File Type | Strategy | Description |
|---------|------|------|
| Original Uploaded Files | Kept permanently, read-only | Ensures data reproducibility |
| Preview Caches (JSON) | Rebuildable, deletable | Saves bandwidth |
| Historical Version Files | Kept permanently (for versions with download history) | Ensures citation persistence |
| Historical Version Deletion | Only allowed for versions with no download history | Protects data that has been used/cited |
| Unpublished Draft Files | Kept permanently (continuously saved as user workspace, not automatically cleaned up) | Ensures drafts can be edited at any time |
| Object Access Control | Private by default, downloaded using short-lived signed URLs | Prevents direct traversal of object storage |

### 5.3 Quota Management

```
Standard Registered Users: 5 GB
Verified Users (providing institutional email/ORCID): 10 GB
Exceeding Quota: Backend rejects writes (HTTP 403), frontend only shows a friendly prompt
```

### 5.4 Single Upload Limits

```
Single File: 200 MB
Single Dataset (sum of all files): 1 GB
Max Files per Dataset: 10 files
```

### 5.5 Upload Security and Large File Anti-OOM Strategy (Mandatory)

- **Malicious Attacks Defense**:
  - Backend dual-validation for file types: Extension whitelist + `python-magic` MIME validation; any mismatch triggers rejection.
  - Filename sanitization and random object keys: Prohibit directory traversal characters (e.g., `../`); uniformly changed to system-generated keys upon storage.
  - Archive security: Limit decompression depth, total decompressed size, and file count to prevent zip bombs.
  - Malicious content scanning: Files enter a quarantine zone before database entry, moving to formal storage only after passing the scan.
  - Immediate blocking on failure: Scan failures, invalid types, or exceeding limits all mark the associated `physical_storage_objects.upload_status=error` and write to `dataset_files.error_message`; publishing is disabled.
- **Anti-Service OOM (Out of Memory) Limits**:
  - **Strictly prohibited**: Directly using `pd.read_csv()` or `pd.read_excel()` to load large files entirely into memory within the FastAPI receiving thread.
  - **CSV Processing**: Mandatory use of `chunksize` for streaming chunked parsing and `row_count` counting for preview extraction.
  - **Excel Processing**: Limited to row-by-row scanning via `openpyxl(read_only=True)` iterative generators; if difficult to process, the frontend can restrict tables larger than 50MB to be forcibly converted to `.csv` before upload.
  - Parsing and calculation processes must be dispatched via Celery/RQ to independent Worker nodes for asynchronous execution; they must not block the Web service and cause downtime.
  - **upload_status State Transition Rules**:
    1) Initial Pending: `pending` (before the client starts uploading or before return)
    2) Scan Passed + Quarantine Transfer to MinIO Successful: `pending -> ready`
    3) Invalid Format, Virus Scan Failed, Anti-OOM Truncation Detection Failed: `pending -> error` (interrupted after marking, and the file cannot be used for publishing)

### 5.6 Download Counting Metric (Unified)

- The statistical metric targets "full download of the current version" (download-all); single file downloads are not counted.
- Adopts a "count upon issuing the download-all URL" strategy (simple to implement, stable performance).
- `datasets.download_count` and `dataset_versions.download_count` increment synchronously during a download-all.
- Metric explanation displayed on the frontend: Download volume represents "times a full download was initiated," not guaranteeing complete file transmission.

### 5.7 Full Packaged Download (Download-all) Technical Implementation

To prevent server memory overflow (OOM) or network disconnections caused by dynamic packaging of large files, the following strategies are adopted:
1. **Offline Packaging**: When a version status changes to `published`, a background Celery task is immediately triggered to package all relevant files for that version into an independent `.zip` archive.
2. **Independent Storage**: The generated ZIP file is uploaded back to MinIO (e.g., `v{n}/archive/dataset_v{n}.zip`).
3. **Short-Lived Issuance**: When a user clicks to download all files for the current version, a temporary access URL for this ZIP object is directly issued, accelerating the download directly through the underlying storage without passing through the backend application layer for data relay.

### 5.8 Preview File Generation and Inheritance Strategy

To prevent missing previews after version inheritance, a "per-version independent preview cache" approach is uniformly adopted:

1. Newly uploaded/replaced files: Generate a preview JSON in the corresponding `v{n}/preview/`.
2. Inherited unmodified files: Copy the previous version's preview JSON to the new version's `v{n}/preview/`.
3. The preview API preferentially reads the preview cache; if it does not exist, the backend rebuilds it on demand and writes it back to the cache.
4. Preview caches correspond one-to-one with `dataset_versions.version_num`; cross-version path reuse is prohibited.

### 5.9 physical_storage_objects Reference Counting Compensation Mechanism

To avoid inconsistencies between `ref_count` and actual version file references, the following rules are uniformly adopted:

1. `ref_count +/- 1` caused by new file entry, version inheritance, and version deletion must be committed within the same database transaction as the corresponding `dataset_files` additions or deletions.
2. If the transaction rolls back, the `ref_count` change rolls back along with it; dirty states where "version creation failed but reference count increased" are prohibited.
3. Asynchronous cleanup of physical files is triggered only after the transaction is committed; verify `ref_count = 0` again before task execution.
4. The Scheduler executes a reconciliation task daily: Aggregates actual reference counts by `dataset_files.file_key` and compares them with `physical_storage_objects.ref_count`; if inconsistent, rewrites corrections based on the actual reference count and records an audit log.
5. The reconciliation task is a compensation mechanism and does not replace maintenance within transactions; daily write logic still prioritizes transaction consistency.
## 6. Backend API Design

### 6.1 API Routing Overview

```text
Authentication
  POST   /api/auth/register
  POST   /api/auth/verify-email/request
  POST   /api/auth/verify-email/confirm
  POST   /api/auth/login
  POST   /api/auth/logout
  POST   /api/auth/refresh
  POST   /api/auth/forgot-password
  POST   /api/auth/reset-password

Users
  GET    /api/users/me
  PUT    /api/users/me
  GET    /api/notifications                 # Get notification list (corresponds to P14)
  PUT    /api/notifications/{id}/read       # Mark notification as read
  PUT    /api/notifications/read-all        # Mark all as read

Public
  GET    /api/stats/overview                # Homepage statistics (number of datasets/reactions/registered users), results cached for 5 minutes

Datasets
  GET    /api/datasets                      # List + Search (read from dataset_search_documents read model)
  POST   /api/datasets                      # Create a dataset and initialize V1 draft version (version_note can be null)
  POST   /api/datasets/{id}/submit-review   # Submit for publication review (creates a review request, request body must explicitly pass { "version_num": X })
  POST   /api/datasets/{owner}/{slug}/archive    # Archive by author (writes to pre_archive_status then sets to archived)
  POST   /api/datasets/{owner}/{slug}/unarchive  # Unarchive (restores to pre_archive_status)
  GET    /api/datasets/{owner}/{slug}        # Details (latest version)
  GET    /api/datasets/{owner}/{slug}/v{n}   # Specific version
  PUT    /api/datasets/{owner}/{slug}        # Update meta information (editing is rejected when pending_review)
  DELETE /api/datasets/{owner}/{slug}        # Soft delete (reclaim quota + asynchronously clean up files)

Files
  POST   /api/datasets/{id}/files            # Upload a file (Body must explicitly pass version_num; P08 passes 1 by default, P15 passes current draft version number)
  GET    /api/datasets/{id}/files/{file_id}/preview   # Preview data
  GET    /api/datasets/{id}/files/{file_id}/download  # Download
  GET    /api/datasets/{id}/versions/{n}/download-all # Download all files for the current version (zip or signed-url manifest)

Versions
  POST   /api/datasets/{id}/versions         # Create a new draft version record, returns version_num (Entry point for P15 Step 1)
  PUT    /api/datasets/{id}/versions/{n}     # Update draft version information (version_note / change_manifest / temporarily save meta information)
  GET    /api/datasets/{id}/versions         # Version list (contains status field, frontend can use this to determine if an unfinished draft exists)
  DELETE /api/datasets/{id}/versions/{n}     # Delete historical version (only allowed if there are no download records)

File Inheritance
  POST   /api/datasets/{id}/versions/{n}/inherit-files  # Batch inherit unmodified files from the previous version (pass { "file_ids": [...] }, must be completed in the same transaction as ref_count increment, see 5.3 for details)

Admin Suggestions
  PUT    /api/suggestions/{id}/status         # Author updates suggestion status (resolved/dismissed)

Interactions
  POST   /api/datasets/{id}/upvote           # Upvote
  DELETE /api/datasets/{id}/upvote           # Remove upvote
  GET    /api/datasets/{id}/discussions      # Discussion list
  POST   /api/datasets/{id}/discussions      # Post a comment
  PUT    /api/datasets/{id}/discussions/{discussion_id}     # Edit own comment
  DELETE /api/datasets/{id}/discussions/{discussion_id}  # Soft delete comment

Admin
  GET    /api/admin/review-requests         # Pending / Historical review list
  GET    /api/admin/review-requests/{id}    # Review details (metadata + file info + column descriptions)
  POST   /api/admin/review-requests/{id}/approve  # Approve review and publish
  POST   /api/admin/review-requests/{id}/reject   # Reject with reason
  GET    /api/admin/datasets                 # All datasets
  POST   /api/admin/datasets/{id}/suggest    # Push a suggestion (only available for published/revision_required)
  PUT    /api/admin/datasets/{id}/takedown   # Takedown (set dataset_status=takedown)
  PUT    /api/admin/datasets/{id}/restore    # Restore (revert to draft or published)
  GET    /api/admin/users                    # User list
  PUT    /api/admin/users/{id}/quota         # Adjust quota
```

### 6.2 Key API Response Examples

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

Note: The frontend must use `user.is_email_verified` from the response body as the basis for UI permission checks (whether to display upload, comment, and upvote entry points); the JWT payload only carries the minimum fields required for authentication, and the frontend is not required to parse the email verification status from the token itself.

#### GET /api/datasets (List)

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

### 6.3 API Security Constraints (Global)

1. Authentication & Sessions
- Access Token is valid for 15 minutes, Refresh Token is valid for 7 days.
- Refresh Tokens use a rotation mechanism: every refresh issues a new token, and the old token is immediately invalidated.
- Refresh Tokens are only stored in the database as hashes (`auth_refresh_tokens`), and are revoked by the server upon logout.
- Regular users must complete email verification (`is_email_verified=true`) before they can upload, comment, or upvote.

2. Permissions & Object-Level Authorization
- All `dataset/file/version` read/write endpoints enforce object-level authorization (owner / publicly available status / admin).
- Downloading and previewing a `file_id` strictly requires secondary verification of its associated `dataset_status` to prevent IDOR vulnerabilities.
- Admin endpoints require `role=admin` and explicitly record audit logs.

3. Brute Force & Abuse Prevention
- Rate limiting for login endpoints: 10 times per minute for the same IP; 5 consecutive failures triggers a 15-minute freeze.
- Upload, download, comment, and search endpoints are all rate-limited, returning HTTP 429 when limits are exceeded.
- Critical operations (login failures, bans, takedowns, permission changes) are written to `security_audit_logs`.

4. Input & Output Security
- All inputs are validated via Pydantic (length, format, enums); undeclared fields are strictly forbidden.
- **Strong Consistency Validation for Custom Tags**: Tags are forcefully converted to lowercase before writing, and rigorously restricted by RegEx to only allow letters, numbers, and underscores, preventing variants and garbage data injection.
- User-visible text (titles, descriptions, discussion content) undergoes XSS filtering prior to rendering.
- Error responses do not expose stack traces or internal paths; they only return traceable error codes.

### 6.4 Draft and Publication Validation Rules (Mandatory)

This logic is strictly validated by the backend; the frontend only provides guidance prompts and cannot replace server-side validation.

**0. Dataset Creation and V1 Initialization Sequence (Mandatory)**

1. When calling `POST /api/datasets`, the backend atomically creates:
- A `datasets` record (`dataset_status='draft'`)
- A `dataset_versions(dataset_id, version_num=1, status='draft', version_note=NULL)` draft record
2. P08 file uploads call `POST /api/datasets/{id}/files`, natively writing to `version_num=1` by default.
3. When filling in the "Initial Version Notes (V1)" in P09, this is written back to the existing V1 `version_note`.
4. When submitting for publication review (Group B validation), `version_note` is strictly required to be non-empty.

**0.1 Sequence for Creating a New Version Draft (P15, Mandatory)**

1. After the author clicks `+ New Version`, the frontend first calls `POST /api/datasets/{id}/versions`.
2. The backend completes the following in a single transaction:
- Validates that the current dataset has no version with `status='draft'` (only 1 new version draft is permitted at any given time).
- Calculates `next_version_num = max(version_num) + 1`.
- Creates `dataset_versions(dataset_id, version_num=next_version_num, base_version_num=current_version, status='draft', version_note=NULL, change_manifest={})`.
- Returns `version_num`.
3. All file uploads and file inheritance operations in P15 Step 1 must explicitly carry this `version_num`.
4. Until P15 Step 2 is completed, this version remains `status='draft'`, which means it is a "draft version" and is not displayed externally on the public details page, visible only to the author. After taking the submission for review, it shifts to `pending_review`, and after approval, it transitions to `published`.5. If the user aborts midway:
- The draft version will consistently be saved in the system, serving as the user's private workspace. It will not be automatically cleaned up or discarded by the system, ensuring the user can return to continue editing at any time.
6. Only 1 version with `status='draft'` is allowed for a dataset at any given time to avoid target version ambiguity when uploading via P15.

**0.2 File Upload API Contract (Mandatory)**

The `POST /api/datasets/{id}/files` request body must contain:

```json
{
  "version_num": 3,
  "file_role": "data",
  "filename": "train_set.csv"
}
```

Constraints:

1. `version_num` is a required field; the backend is not allowed to automatically guess based on the "current version".
2. P08 always passes `version_num = 1`.
3. P15 can only pass the draft version number returned by `POST /api/datasets/{id}/versions`.
4. Upon receiving the upload request, the backend must first validate:
- The `version_num` belongs to the current `dataset_id`.
- The current user is an owner or admin.
- The version has not yet been submitted for review and has not been deleted.
5. If validation fails, return `409 invalid_target_version`.

**A. Save Draft (Lenient Validation)**

- Allows incomplete metadata to be written to the database (used for resuming edits after interruption).
- Minimum requirements:
1. At least 1 uploaded file record exists.
2. The dataset has a V1 version record (`version_num=1`).
3. Dataset ownership is valid (owner matches).
4. Field types/lengths/enums are valid (Pydantic).

**B. Submit for Online Review (Strict Validation)**

When calling `POST /api/datasets/{id}/submit-review`, all the following must pass:

1. Dataset basic information is complete: `title/description/source_type/license` are non-empty.
2. `description` length meets the minimum limit (Current design: >=50 characters).
3. At least 1 task-type Tag exists.
4. `version_note` of the currently submitted version is non-empty.
5. All physical storage objects associated with files in this version have `physical_storage_objects.upload_status=ready`.
6. The `description` for all files in this version is non-empty.
7. The `description` for all columns in this version is non-empty.
8. File and column reference relationships are intact (no orphan columns, no cross-version mismatches).

Validation failure returns `422` with field-level errors (e.g., `missing_file_description`, `missing_column_description`).

**C. Pre-approval Re-verification by Administrator (Bypass Prevention)**

- Re-execute Group B validations before `POST /api/admin/review-requests/{id}/approve`.
- If validation fails, reject the approval and prompt the administrator: "The submitted content has changed. Please ask the author to correct and resubmit."
- Upon passage, atomically update:
1. `dataset_status -> published`
2. Update `datasets.current_version` to the version number approved in this review (if greater than the current value).
3. `dataset_versions.status -> 'published'`, `metadata_complete=true`
4. Write to `dataset_review_requests(status=approved, reviewed_at, reviewed_by)`
5. Trigger an asynchronous task: Generate a ZIP archive for this version and project the update to `dataset_search_documents`.

**D. Lock Metadata During Review (Avoid "Review Snapshot Drift")**

- When `dataset_status=pending_review`, `PUT /api/datasets/{owner}/{slug}` returns `409 Conflict`.
- Suggested error code: `dataset_under_review_locked`.
- Suggested prompt text: "The dataset is under review and temporarily uneditable; please wait for the review results before modifying."

### 6.5 Historical Version Deletion Rules (Mandatory)

`DELETE /api/datasets/{id}/versions/{n}` only allows the owner to delete "unused" historical versions:

1. At least 1 version must be retained (cannot delete empty dataset versions).
2. Deletion is rejected when `dataset_versions.download_count > 0`, returning `409 Conflict`.
3. If any higher version `m > n` exists, deleting `Vn` is prohibited, returning `409 version_has_descendants`; the deletion operation can only act on leaf historical versions "prior to the current version with no descendant dependencies" to avoid breaking the `change_manifest` comparison baseline.
4. If `current_version` is deleted, it automatically rolls back to the maximum existing version number.
5. Deletion and `current_version` rollback must be completed within the same transaction to avoid reading intermediate states.
6. When the dataset is in the `takedown` status, the author is prohibited from deleting any versions (returns `409`).

### 6.6 Suggested Resolution Closed Loop (Editing Linkage)

- When a user receives a notification from P14 and clicks "Go process", the frontend not only fetches the notification itself but also extracts the original `admin_suggestions.id` from `notifications.target_id`.
- It then transitions to P10 (Metadata Editing Component) with this hint. Upon saving, a linkage action hook automatically pops up at the bottom of the page: "1 pending administrator suggestion detected. Mark as resolved?"
- After the user confirms and the primary frontend form saves data successfully, the status is set to `resolved` via `PUT /api/suggestions/{suggestion_id}/status`.
- Upon successful update of the business table, the initial `notifications` can optionally be digested concurrently via an asynchronous event and marked as "read".
- If the user cancels, only the data is saved without changing the suggestion status.
- If files need to be modified, the user clicks "Create Revision" in P10 to enter the two-step P15 process.
- Currently, no structured type judgment is performed on administrator suggestions (no `suggestion_type` field) to avoid incorrect automatic shunting.

### 6.7 Discussion Editing and Soft Deletion Rules

- `PUT /api/datasets/{id}/discussions/{discussion_id}` only allows the author of the comment to edit the text content.
- Upon successful edit, `edited_at` and `updated_at` are written, and the frontend displays "(edited)".
- Currently, historical edited versions are not retained (only the final version is kept).
- `DELETE /api/datasets/{id}/discussions/{discussion_id}` only performs soft deletion:
- Writes `deleted_at` and `deleted_by`, preserving the original record and reply relationships.
- The frontend renders the deleted comment with placeholder text: "This comment has been deleted."
- Sub-replies are retained normally to avoid breaking the discussion thread.

### 6.8 Dataset Deletion and Quota Atomic Reclamation

- `DELETE /api/datasets/{owner}/{slug}` performs soft deletion for user-initiated active deletions:
- The soft deletion action is completed within a transaction:
1. Write to `datasets.deleted_at/deleted_by`.
2. `dataset_status -> deleted`.
3. If the current status exists in the `pending` state of `dataset_review_requests`, atomically update it to `canceled_by_user`.
4. **Safe quota deduction**: Must use database atomic operations for deduction to prevent "dirty writes" of the quota caused by high-concurrency uploads/deletions:
   `UPDATE users SET storage_used = GREATEST(storage_used - :total_size, 0) WHERE id = :user_id`
- Physical file cleanup is queued into the Celery asynchronous queue for offline execution; on failure, it enters the dead-letter queue for alerting and retries, without affecting the return of the primary request.

### 6.9 Full Download vs. Single File Download Semantics

- The header download button corresponds to `GET /api/datasets/{id}/versions/{n}/download-all`.
- Single file downloads continue to use `GET /api/datasets/{id}/files/{file_id}/download`.
- `datasets.download_count` and `dataset_versions.download_count` only calculate `download-all`.
- Single file downloads are not included in the header download volume statistics.

### 6.10 Audit Concurrency Control (Mandatory)

- `POST /api/admin/review-requests/{id}/approve|reject` must be checked and updated within the same transaction.
- Recommended implementation:
1. `SELECT ... FOR UPDATE` locks the review request.
2. Decision writing is allowed only when `status='pending'`.
3. If the status has changed, return `409 Conflict` (e.g., `review_request_already_decided`).
- Ensure that any review request will only have one final decision.

### 6.11 Administrator Suggestion API Applicable Statuses

- `POST /api/admin/datasets/{id}/suggest` is only permitted for `published` or `revision_required`.
- Returns `409` for `draft` / `pending_review` / `takedown` / `archived`.
- During the `pending_review` phase, administrator advisory should be expressed through the review approval/rejection process instead of routing via the suggestion channel.

### 6.12 Password Reset Flow Constraints (Mandatory)

- `POST /api/auth/forgot-password` returns a uniform success response regardless of whether the email exists, to prevent account enumeration.
- The reset token utilizes a one-time short-lived token (recommended 30 minutes) and saves the hash (Redis or database) for verification.
- Upon successful `POST /api/auth/reset-password`, immediately invalidate the token and revoke all Refresh Tokens for the user.
- Password reset events are written to `security_audit_logs` (`event_type=password_reset`).

### 6.13 Domain Error Code System (Mandatory)

Uniform error response format:

```json
{
  "error": {
    "code": "dataset_under_review_locked",
    "message": "The dataset is under review and temporarily uneditable",
    "details": {
      "dataset_id": "uuid"
    }
  }
}
```

Naming conventions:

1. Uniform use of lowercase snake_case.
2. Prefixes divided by domain: `auth_*`, `dataset_*`, `version_*`, `review_*`, `file_*`, `suggestion_*`.
3. `message` serves as the default text directly displayable; the frontend is allowed to override with localized text based on `code`.

First batch of must-implement error codes:

| HTTP | code | Default Message |
|------|------|----------|
| 401 | `auth_invalid_credentials` | Incorrect email or password |
| 403 | `auth_email_not_verified` | Email not verified, current operation unavailable |
| 403 | `dataset_access_denied` | You do not have permission to access this dataset |
| 404 | `dataset_not_found` | Dataset not found or invisible |
| 409 | `dataset_under_review_locked` | The dataset is under review and temporarily uneditable |
| 409 | `review_request_already_decided` | This review request has already been processed |
| 409 | `invalid_target_version` | Target version is not writable |
| 409 | `version_has_descendants` | This version is still used as a comparison baseline by subsequent versions and cannot be deleted |
| 409 | `draft_version_already_exists` | An unfinished new version draft already exists |
| 409 | `dataset_status_conflict` | The current dataset status does not support this operation |
| 422 | `missing_file_description` | There are files with empty descriptions |
| 422 | `missing_column_description` | There are columns with empty descriptions |
| 422 | `invalid_tag_format` | Invalid Tag format |

## 7. Frontend Framework & Page Overview

### 7.1 Design Style

- **Style Positioning**: Minimalist academic style, reference Semantic Scholar, arXiv, Zenodo
- **Color Scheme**: White background + Deep Blue primary (`#1E3A5F`) + Light Gray auxiliary (`#F8F9FA`) + Green success (`#28A745`) + Orange warning (`#FD7E14`)
- **Typography**: Body text `Inter`, Code/SMILES `JetBrains Mono`
- **Layout**: Maximum width `1200px`, paddings on both sides, center-aligned content

### 7.2 Page Inventory (18 Pages Total)

| ID | Page Name | Route | Access Permission |
|------|---------|------|---------|
| P01 | Home | `/` | All |
| P02 | Dataset Marketplace | `/datasets` | All |
| P03 | Dataset Details | `/datasets/{owner}/{slug}` | All |
| P04 | Dataset Details (Specific Version) | `/datasets/{owner}/{slug}/v{n}` | All |
| P05 | Registration Page | `/register` | Guest |
| P06 | Login Page | `/login` | Guest |
| P18 | Email Verification Result Page | `/verify-email` | Guest |
| P16 | Forgot Password | `/forgot-password` | Guest |
| P17 | Reset Password | `/reset-password` | Guest |
| P07 | User Profile | `/profile` | Authenticated |
| P14 | Message Center | `/messages` | Authenticated |
| P08 | Upload Step 1 (File Upload) | `/upload/step1` | Verified Authenticated |
| P09 | Upload Step 2 (Information Filling) | `/upload/step2` | Verified Authenticated |
| P10 | Dataset Metadata Edit | `/datasets/{owner}/{slug}/edit` | Owner/Admin |
| P15 | New Dataset Version (Two Steps) | `/datasets/{owner}/{slug}/new-version` | Owner/Admin |
| P11 | Admin Login | `/admin/login` | — |
| P12 | Admin Dashboard | `/admin/datasets` | Admin |
| P13 | Admin User Management | `/admin/users` | Admin |

---

## 8. Detailed Page Design

---

### P01 Home

**Goal**: A promotional entry point for visitors, quickly conveying platform value, and guiding users to the marketplace or registration.

**Layout**:

```text
┌──────────────────────────────────────────────────────────┐
│  NAVBAR                                                   │
│  [Logo] RxnCommons    Home  Datasets  About      Login  Register│
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  HERO                                                     │
│                                                           │
│         Chemical Reaction Data Sharing Platform            │
│    Open · Trusted · Designed for Chemical Research         │
│                                                           │
│    ┌──────────────────────────────────┐  [Search]         │
│    │  Search dataset title or Tag...   │                  │
│    └──────────────────────────────────┘                   │
│                                                           │
│    [Browse Datasets →]   [Upload My Dataset]              │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  STATS (Real-time statistics)                              │
│                                                           │
│   1,284          8,920,000+        542                    │
│   Datasets       Reactions         Registered Users       │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Featured Datasets (3 cards horizontal layout)             │
│                                                           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │ Dataset Title │ │ Dataset Title │ │ Dataset Title │      │
│  │              │ │              │ │              │      │
│  │ Tag Tag      │ │ Tag Tag      │ │ Tag Tag      │      │
│  │ 2,233 rows   │ │ 4,821 rows   │ │ 52,430 rows  │      │
│  │ ▲234  ↓1820 │ │ ▲891  ↓3872 │ │ ▲102  ↓940  │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
│                                         [View All →]      │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Platform Features (3 columns)                             │
│                                                           │
│   🔬 Designed for Chemistry   🏷️ Structured Tag Search   🔒 Immutable Raw Data │
│   Supports Multiple Formats    Traceable Metadata          Archived on Upload    │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  FOOTER                                                   │
│  About  Contact  GitHub  Privacy Policy  Terms             │
└──────────────────────────────────────────────────────────┘
```

**Interaction Details**:
- Hitting Enter in the search box directly navigates to P02 with the search parameter.
- "Upload My Dataset" button: Redirects to P06 Login Page if unauthenticated, otherwise redirects to P08.
- Featured datasets selection rule: v1 limits the query to datasets in `dataset_search_documents` where `dataset_status IN ('published', 'revision_required')`, truncating the Top 3 based on `upvote_count` descending (manual pin configurations can be extended in future versions).
- Data source for STATS: `Datasets` = `COUNT(*) FROM dataset_search_documents WHERE dataset_status IN ('published','revision_required','archived')`; `Reactions` = `SUM(total_rows) FROM dataset_search_documents WHERE ...`; `Registered Users` = `COUNT(*) FROM users`. It is recommended for the backend to provide a `GET /api/stats/overview` endpoint, caching the result for 5 minutes.

---

### P02 Dataset Marketplace

**Goal**: Discovery and retrieval of datasets, supporting filtering by Tag and conditions.

**Layout**:

```text
┌──────────────────────────────────────────────────────────┐
│  NAVBAR (Same as above)                                   │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Search Bar                                               │
│  ┌──────────────────────────────────────────┐  [Search]   │
│  │  Search dataset title or Tag...           │           │
│  └──────────────────────────────────────────┘           │
│  Found 128 datasets         Sort by: [Newly Uploaded ▼]    │
└──────────────────────────────────────────────────────────┘

┌──────────────┬───────────────────────────────────────────┐
│  Filter Panel │  Dataset Card List                          │
│  (Fixed Left) │                                           │
│              │  ┌────────────────────────────────────┐   │
│  Task Type   │  │ Suzuki coupling HTE                │   │
│  □ Yield Predict│ │ by yi_zhang  ·  2,233 rows · 604KB │   │
│  □ Cond. Predict│ │                                    │   │
│  □ Retrosynth│  │ #yield_prediction  #C-C_coupling   │   │
│  □ Forward   │  │ #HTE                               │   │
│  □ Reaction Class│ │                                    │   │
│              │  │(Card only shows Task Tags)           │   │
│  ──────────  │  │ ▲ 234    ↓ 1,820                   │   │
│  Data Scale  │  └────────────────────────────────────┘   │
│  □ <1000 rows│                                           │
│  □ 1k~10k rows│ ┌────────────────────────────────────┐   │
│  □ >10k rows │  │ Buchwald-Hartwig Amination          │   │
│              │  │ by doyle_group  ·  3,956 rows · 2MB│   │
│  ──────────  │  │                                    │   │
│  Source      │  │ #yield_prediction  #C-N_coupling   │   │
│  □ Lab       │  │                                    │   │
│  □ Lit Extract│ │(Field coverage info shown in detail)│   │
│  □ Patent Ext│  │                                    │   │
│  □ DB Export │  │                                    │   │
│  ──────────  │  │                                    │   │
│  Status      │  │                                    │   │
│  □ Published │  │                                    │   │
│  □ Rev. Req  │  │                                    │   │
│  □ Archived  │  │ ▲ 891    ↓ 3,872                   │   │
│              │  └────────────────────────────────────┘   │
│              │  [← Prev Page] Page 1/7 [Next Page →]     │
└──────────────┴───────────────────────────────────────────┘
```

**Card Field Explanations**:
- `▲ 234`: Community Upvote count.
- `↓ 1,820`: Download count.
- The card only displays Task-related Tags; field coverage information is shown in the right "Included Fields" section on the dataset detail page.

**Search Logic**:
- P02 does not directly scan the primary business table, but queries the `dataset_search_documents` read model.
- v1 adopts a combination strategy of "Fuzzy Title Matching + Exact Tag Filtering + Status Filtering + Sorting Fields".
- Left "Data Scale" filter: Corresponds to range filtering on the backend against the `total_rows` field in the read model (e.g., `<1000`, `BETWEEN 1000 AND 10000`, `>10000`).
- Default search scope includes `published`, `revision_required`, and `archived`.
- Users can filter by "Status" on the left to solely view published, revision requested, or archived datasets.
- Currently, a dedicated search engine is not introduced, but the database must enable `pg_trgm` or FTS indexes; otherwise, the list page will degrade into a slow-query hotspot as the scale grows.

---

### P03 Dataset Details (Latest Version)

**Goal**: Complete presentation of dataset information, supporting data preview, discussion, and download.

**Layout**:

```text
┌──────────────────────────────────────────────────────────┐
│  NAVBAR (Messages entry shown top right after login)       │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Dataset Header                                            │
│                                                           │
│  Suzuki coupling HTE      [▲ Upvote 234]  [↓ Download 1,820]│
│  by yi_zhang  ·  Updated 2026-03-13  ·  V2 (Latest)        │
│  [Download Current Ver (All)] [Copy DB Link] [Copy Ver Link]│
│  Status: Published                                         │
│                                                           │
│  #yield_prediction  #C-C_coupling  #HTE  #Pd-catalysis   │
│                                                           │
│  This is a high-throughput screening dataset regarding     │
│  Suzuki coupling, containing yield data under...           │
│                                                           │
│  Current Version Stats (V2): 2,233 rows · 3 files · 604 KB │
│                  Current Vers. Downloads: 1,820 times      │
└──────────────────────────────────────────────────────────┘

┌────────────────────────────────────┬─────────────────────┐
│  Tab Navigation                     │  Right Info Panel    │
│  [Data Preview] [Discussion(12)]    │                     │
│                                    │  Files (click to switch)│
│  ─────────────────────────────     │  train_set.csv 4.2MB ●[DL]│
│                                    │  test_set.csv  1.1MB  [DL]│
│  [Data Preview Tab]                 │  metadata.xlsx 0.6MB  [DL]│
│  Headers (In same table, 2 rows fixed)│                     │
│  ┌────────────┬────────────┬──────┐│  ─────────────────   │
│  │Reactant SMILES│Product SMILES│Yield(%)││  Included Fields   │
│  │reactants   │products    │yield ││  #has_reactants_data │
│  ├────────────┼────────────┼──────┤│  #has_products_data  │
│  │CC(=O)...   │CC(=O)...   │88.2  ││  #has_yield_data     │
│  │c1ccc...    │c1ccc...    │91.5  ││  #has_solvent_data   │
│  │...         │...         │...   ││  #has_ligand_data    │
│  └────────────┴────────────┴──────┘│  ─────────────────   │
│  Scroll horizontally for data;     │  Metadata            │
│  Top 2 header rows fixed.          │  Status: Published   │
│  Showing 50 / 2,233 rows           │  Source: Lit Extract │
│                                    │  DOI: 10.1021/...    │
│                                    │  License: CC BY 4.0  │
│                                    │                     │
│                                    │  ─────────────────   │
│                                    │  Version History     │
│                                    │  V2  2026-03-13 Curr │
│                                    │  V1  2025-11-02      │
│                                    │       [View] [DL] [Delete]|
│                                    │  *Note: [Delete] only shown if no successor & no downloads*│
│                                    │                     │
│                                    │  ─────────────────   │
│                                    │  Actions (Owner Only)│
│                                    │  [+ New Version]     │
│                                    │  [Archive/Unarchive] │
│                                    │  (Disabled if V1 missing │
│                                    │   field descriptions)│
└────────────────────────────────────┴─────────────────────┘
```

**Information Hierarchy Recommendations**:
- Field-type Tags are displayed in the right info panel and are not used as criteria for the left-side filter constraint.
- File selection is placed in the right "File List". Highlighting indicates the current file; no need to repeat the filename again on the left side.
- Column descriptions are placed directly above column names, aligned together, reducing comparative overhead.
- Dataset statistical information is moved up to the header region, prioritized globally.
- The data table supports horizontal scrolling. Column description + column name form a two-row fixed header to prevent context loss while browsing long tables.
- The "New Version" entry is pinned to the bottom of the right info panel to prevent confusion with browsing details.
- Prerequisite for "New Version": All mandatory fields for V1 file descriptions and column mappings must be completed.
- Admin recommendations centralize in the "Message Center". Detail/edit pages only show a redirect prompt rather than duplicating full text.
- `published/revision_required/archived` states support public sharing; links copied for other states restrict access only to the owner/admins.
- Under the `revision_required` state, it remains public and downloadable. Only the author sees the "Pending Recommendations" banner.
- The download button in the header is strictly for "Download Current Version All Files". The `[Download]` buttons in the right panel are for single files.
- Header download statistics count only full-package downloads, excluding single-file downloads.
- View count triggering logic: Whenever `GET /api/datasets/{owner}/{slug}` details page loads, the backend increments `datasets.view_count` asynchronously (deduplication of same User/IP over a short interval recommended via Redis sliding window, although v1 may skip deduping for simplicity).

**Discussion Tab Interaction Details (Mandatory)**:

- Presentation: Top-level comments laid out flat. Replies use a secondary indented list, explicitly abandoning infinite nesting beneath.
- Loads 20 top-level comments per page, sorted by "Newest Post" descending by default; v1 does not provide a "Hottest Sort".
- Each top-level comment displays its 3 most recent replies by default. Excess replies are lazy-loaded asynchronously upon clicking "Expand more replies".
- When replying, the frontend supports displaying `@username`, but the database strictly saves plain text content without a dedicated mention schema.
- Under `archived` states, the discussion zone operates in read-only mode: users can browse history but text boxes and reply buttons are hidden.
- Deleted comments display a placeholder copy to preserve structure depth and reply counts.
- Top-level comment card fields: Author, Time, Text Content, Edited Flag, Reply Button, Delete Button (Visible to Owner/Admin).

---

### P04 Dataset Details (Historical Version)

Identical to P03, but includes a prominent version warning banner injected at the top:

```text
┌──────────────────────────────────────────────────────────┐
│ ⚠️ You are viewing historical version V1 (2025-11-02)     │
│    This version has been cited and is permanently kept.    │
│    The latest version is V2. [View →]                      │
└──────────────────────────────────────────────────────────┘
```

The version area highlights the currently viewed version, and the rest of the contents reflect the files and column mappings relevant to that version.
Header statistics only encompass metrics for the "currently viewed version" (e.g., V1 downloads) rather than other versions or global aggregates.

---

### P05 Registration Page

**Layout**:

```text
┌──────────────────────────────────────────────────────────┐
│  NAVBAR                                                   │
└──────────────────────────────────────────────────────────┘

                ┌────────────────────────────┐
                │  Create your RxnCommons Account│
                │                            │
                │  Username *                │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │  3-50 chars, alphanumeric/underscore│
                │                            │
                │  Email *                   │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  Password *                │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │  Minimum 8 chars, alpha+numeric│
                │                            │
                │  Confirm Password *        │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  Institution/Affiliation (Optional)│
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  Research Focus (Optional) │
                │  ┌────────────────────┐    │
                │  │  Select...      ▼  │    │
                │  └────────────────────┘    │
                │  Organic Synth/MedChem/CompChem/Other│
                │                            │
                │  [    Register    ]         │
                │                            │
                │  A verification email will be sent.│
                │  Email verification required before │
                │  uploading/commenting/upvoting.     │
                │                            │
                │  Already have an account? Login│
                └────────────────────────────┘
```

---

### P06 Login Page
```text
                ┌────────────────────────────┐
                │  Log in to RxnCommons      │
                │                            │
                │  Email                     │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  Password                  │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │  Forgot password?          │
                │                            │
                │  [   Log in   ]            │
                │                            │
                │  If email is unverified,   │
                │  prompt after login:       │
                │  [Resend verification email]│
                │                            │
                │  No account? Sign up       │
                └────────────────────────────┘
```

---

### P18 Email Verification Result Page

```
                ┌────────────────────────────┐
                │  Email Verification Result │
                │                            │
                │  ✅ Verification Successful│
                │  Your account now has      │
                │  upload and interaction    │
                │  permissions               │
                │                            │
                │  [Log in]   [Back to Home] │
                └────────────────────────────┘
```

---

### P16 Forgot Password

```
                ┌────────────────────────────┐
                │  Recover Password          │
                │                            │
                │  Registered Email *        │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  [Send Reset Email]        │
                │                            │
                │  Prompt after sending:     │
                │  Please click the email    │
                │  link within 30 minutes    │
                └────────────────────────────┘
```

---

### P17 Reset Password

```
                ┌────────────────────────────┐
                │  Reset Password            │
                │                            │
                │  New Password *            │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  Confirm New Password *    │
                │  ┌────────────────────┐    │
                │  │                    │    │
                │  └────────────────────┘    │
                │                            │
                │  [Confirm Reset]           │
                └────────────────────────────┘
```

---

### P07 Personal Profile

**Layout**:

```
┌──────────────────────────────────────────────────────────┐
│  NAVBAR                                   [🔔 Messages 2] │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Personal Information                                     │
│                                                           │
│  [Avatar]  yi_zhang                            [Settings] │
│            Peking University  ·  Organic Synthesis        │
│                                                           │
│  5 datasets    12,450 reactions    3,820 downloads        │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Storage Quota                                            │
│  ████████░░░░░░░░░░░░░░░░░░░░░  1.54 MB / 5 GB            │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Message Summary (Recent 3)                               │
│                                                           │
│  [Unread] Suzuki_coupling_HTE · V2 · ligand column suggest│
│        2026-03-13  admin01              [View and handle] │
│                                                           │
│  [Read] Buchwald_dataset · V1 · source link addition sugg.│
│        2026-03-10  admin02                 [View details] │
│                                                           │
│  [Go to Message Center]                                   │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  My Datasets                              [+ Upload New]  │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Suzuki_coupling_HTE         Published V2 2026-03-13   │    │
│  │ #yield_prediction  #C-C_coupling                      │    │
│  │ ▲234  ↓1820       [Edit] [New Version] [Archive] [Del]│    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Knoevenagel_condensation Revision Req V1 2026-01-05   │    │
│  │ Description empty ⚠️ 1 pending suggestion             │    │
│  │      [Edit] [Submit for Review] [Delete]              │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

**Status Action Matrix (Mandatory)**:

| Status | Visible Buttons for Author |
|------|--------------|
| `draft` | `[Edit] [Submit for Review] [Delete]` |
| `pending_review` | `[View] [Under Review]` (Editing locked) |
| `published` | `[Edit] [New Version] [Archive] [Delete]` |
| `revision_required` | `[Edit] [New Version] [Submit for Review] [Delete]` |
| `archived` | `[View] [Unarchive] [Delete]` |
| `takedown` | `[View Takedown Reason] [Contact Admin]` |

---

### P14 Message Center (Independent Page)

Note: P07 only displays a message summary; the complete list of messages, filtering, read/unread status, and processing actions are all handled on an independent page.  
The only entry point for users to view admin feedback is `P14 /messages` (accessible directly via the NAVBAR messages button).

```
┌──────────────────────────────────────────────────────────┐
│  NAVBAR                                   [🔔 Messages 2] │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Message Center                                           │
│  [All] [Unread] [Admin Suggestions] [System] Search:[___] │
├──────────────────────────────────────────────────────────┤
│  [Unread] Admin Suggestion · Suzuki_coupling_HTE · V2     │
│  admin01 · 2026-03-13                                     │
│  "Suggest keeping the ligand column naming consistent..." │
│  [Mark as Read] [View Dataset] [Handle (Open Edit Page)]  │
│                                                           │
│  [Read] Admin Suggestion · Buchwald_dataset · V1          │
│  admin02 · 2026-03-10                                     │
│  "Suggest adding source links and filtering rules desc..."│
│  [View Dataset] [Handle]                                  │
└──────────────────────────────────────────────────────────┘
```

**Action Conventions**:
- `View Dataset`: Jumps to P03 (corresponding dataset and version)
- `Handle`: Uniformly jumps to P10 (metadata editing)
- `Mark as Read`: Only updates the reading status, does not change the suggestion processing status (`pending/resolved/dismissed`)

---

### P08 Upload Step 1 (File Upload)

**Confirmation dialog upon entry**:

```
┌─────────────────────────────────────────────────┐
│  Please confirm before uploading                │
│                                                 │
│  □ I have performed basic checks on SMILES      │
│    related columns                              │
│  □ I understand that the platform will not      │
│    modify any of my uploaded raw data           │
│  □ My column names are clearly named for others │
│    to understand                                │
│                                                 │
│  Suggested column names (English/Chinese OK):   │
│  reactants · products · solvent · catalyst      │
│  ligand · base · yield_pct · temperature_c      │
│  reaction_smiles · reagent · amount_equiv       │
│                                                 │
│  ⚠️ Using other column names is perfectly fine, │
│     just provide column descriptions in the     │
│     next step                                   │
│                                                 │
│           [Cancel]  [I understand, continue]    │
└─────────────────────────────────────────────────┘
```

**Main Page**:

```
┌──────────────────────────────────────────────────────────┐
│  Upload Dataset  Step 1/2: Upload Files                  │
│  ●──────○                                                │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐   │
│                                                          │
│  │           Drag and drop files here to upload      │   │
│              or                                          │
│  │        [  Select Files  ]                         │   │
│                                                          │
│  │  Supports CSV · Excel · SDF · TXT · ZIP           │   │
│   ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─      │
│                                                          │
│  Selected files:                                         │
│  📊 train_set.csv         4.2 MB   ████████░░ Uploading  │
│  📊 test_set.csv          1.1 MB   ██████████ Done ✅    │
│  ❌ bad_data.csv          0.5 MB   Parse failed: File... │
│                                    too large [× Delete]  │
│                                                          │
│  + Add more files                                        │
│                                                          │
│  Storage Quota: 1.54 MB / 5 GB                           │
│                                                          │
│  [Cancel]                         [Next, Fill Info →]    │
│                            (Clickable after all uploads) │
└──────────────────────────────────────────────────────────┘
```

---

### P09 Upload Step 2 (Information Fill)

**Layout**:

```
┌──────────────────────────────────────────────────────────┐
│  Upload Dataset  Step 2/2: Fill Information              │
│  ●──────●                                                │
│  Files saved. Please complete the following info before  │
│  submitting for review.                                  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Dataset Basic Information                               │
│                                                          │
│  Dataset Title *                                         │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Suzuki coupling HTE                              │    │
│  └──────────────────────────────────────────────────┘    │
│  URL Preview: rxncommons.org/datasets/yi_zhang/          │
│               Suzuki_coupling_HTE                        │
│  (Spaces automatically replaced with underscores)        │
│  Link is fixed after first save; only publicly accessible│
│  after review approval.                                  │
│                                                          │
│  Dataset Description * (At least 50 chars)               │
│  ┌──────────────────────────────────────────────────┐    │
│  │                                                  │    │
│  │                                                  │    │
│  │                                                  │    │
│  └──────────────────────────────────────────────────┘    │
│  Entered 0/50 chars                                      │
│                                                          │
│  Initial Version Notes (V1) *                            │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 2024.03-2025.12 compiled from lit and lab records│    │
│  │ removed samples with missing yield data.         │    │
│  └──────────────────────────────────────────────────┘    │
│  Tip: Include collection source, time frame,             │
│  inclusion/exclusion rules, and cleaning methods         │
│                                                          │
│  Applicable Task Tags * (Select at least 1)              │
│  [Yield Prediction ×]  [C-C Coupling ×]  [+ Add Tag]     │
│  Preset Task Tags: yield_prediction condition_prediction │
│          retrosynthesis forward_prediction ...           │
│  Field Tag Suggestions: has_yield_data has_solvent_data  │
│          has_ligand_data has_catalyst_data ...           │
│  Tag Hint: Prefer preset tags; avoid tags like           │
│  "Experiment A" with no search value.                    │
│                                                          │
│  Data Source Type (Single Select) *                      │
│  ○ Lab Tested  ○ Literature  ● Patent  ○ DB Export       │
│                                                          │
│  Source Link/DOI (Highly Recommended)                    │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 10.1021/jacs.xxxxxxx                             │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  License *                                               │
│  ┌──────────────────────────────────────────────────┐    │
│  │  CC BY 4.0                                    ▼  │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  Publish Actions                                         │
│  Use the bottom buttons to either "Save Draft" or        │
│  "Submit for Review".                                    │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Author Information                                      │
│                                                          │
│  Author 1                            ☰ (Drag to sort) [×]│
│  Name *              Institution                         │
│  ┌──────────────┐   ┌───────────────────────────────┐    │
│  │ Yi Zhang     │   │ Peking University             │    │
│  └──────────────┘   └───────────────────────────────┘    │
│  ORCID (Optional)      Role                              │
│  ┌──────────────┐   ● First Author  ○ Co-author          │
│  │              │   ○ Corresponding Author               │
│  └──────────────┘                                        │
│                                                          │
│  [+ Add Author]                                          │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  File Information                                        │
│                                                          │
│  ── train_set.csv (4.2 MB) ────────────────────────────  │
│                                                          │
│  About this file                                         │
│  This file does not have any description yet.     [Edit] │
│                                                          │
│  Data Preview (Top 5 rows, for column checking only):    │
│  ┌──────────────┬──────────────┬──────────┬──────────┐   │
│  │ reactants    │ products     │ ligand   │ yield_pct│   │
│  ├──────────────┼──────────────┼──────────┼──────────┤   │
│  │ CC(=O)Cl.... │ CC(=O)OCC..  │ PPh3     │ 88.2     │   │
│  │ ...          │ ...          │ ...      │ ...      │   │
│  └──────────────┴──────────────┴──────────┴──────────┘   │
│                                                          │
│  Click [Edit] to expand inline editor below:             │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Table Description *                                 │ │
│  │ ┌───────────────────────────────────────────────┐   │ │
│  │ │ [Please describe the purpose, source, and     │   │ │
│  │ │ fields of this file/table...]                 │   │ │
│  │ └───────────────────────────────────────────────┘   │ │
│  │                                                     │ │
│  │ Column Description (vertical, edit on right):       │ │
│  │ ┌────────────┬─────────────────────────────────┐    │ │
│  │ │ reactants  │ [Please enter description...]   │    │ │
│  │ │ products   │ [Please enter description...]   │    │ │
│  │ │ ligand     │ [Please enter description...]   │    │ │
│  │ │ yield_pct  │ [Please enter description...]   │    │ │
│  │ │ batch_id   │ [Please enter description...]   │    │ │
│  │ └────────────┴─────────────────────────────────┘    │ │
│  │ Completion: 0/5 (Example)         [Cancel] [Save]   │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ── test_set.csv (1.1 MB) ─────────────────────────────  │
│  (Same structure as above: independent editing per file) │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  [← Back to Upload]   [Save Draft]   [Submit for Review] │
│                       Saved as draft Published on pass   │
└──────────────────────────────────────────────────────────┘
```

When calling `POST /api/datasets`, the system has already initialized a `V1` draft record; after filling in the "Initial Version Note (V1)" on P09, it writes back to `dataset_versions.version_note`.

**Editing Interaction Guidelines**:
- Initially display empty state copy + an `[Edit]` button to prevent users from mistakenly thinking a description already exists.
- Clicking `[Edit]` expands an inline editing area below the current file card; edits are saved in place.
- Inside the editing area, column names are vertically fixed, with unified input boxes on the right for descriptions, facilitating batch editing.
- Filled fields allow repeated modifications and write back to the file immediately upon saving.
- Saving a draft only performs basic format validation and allows incomplete required fields to be retained.
- Before submitting for online review, a per-column validation is performed, blocking only files with missing column descriptions from entering the review process.

---

### P10 Dataset Metadata Editing (Single Page)

Purpose: Edit metadata only without triggering a version bump; applicable for scenarios like "updating Title/Description/Tag/Source/License/Author".
Entry points: P07 "Edit", P03 "Edit", P14 "Go to Process".

**Layout**:

```
┌──────────────────────────────────────────────────────────┐
│  Edit Dataset Metadata                                     │
│  Dataset: Suzuki_coupling_HTE  Current Version: V2         │
├──────────────────────────────────────────────────────────┤
│  Title * / Description * / Tag * / Source Type * / License *│
│  Source Link/DOI / Author Info (Editable)                  │
│                                                           │
│  [Cancel]   [Save Metadata]   [Create Revision (Goto P15)] │
└──────────────────────────────────────────────────────────┘
```

**Rules**:
- Only calls `PUT /api/datasets/{owner}/{slug}` to update metadata; does not create a new version.
- When `dataset_status=pending_review`, the page is read-only, the save button is disabled, and it prompts "Editing temporarily disabled while under review".
- If the suggestion involves file content adjustments, clicking "Create Revision" navigates to P15 (two-step process).

---

### P15 Create Dataset Version (Two-Step Process)

Consistent with P08/P09, creating a new version also adopts a two-step upload process:
- Step 1/2: File Changes (inherits files from the previous version, can be replaced/removed/added).
- Step 2/2: Information Filling (structure aligns with P09, including version notes + metadata + file descriptions).
- The new version entry point is triggered by the `+ New Version` button at the bottom right of the detail page.
- If V1 has incomplete mandatory file descriptions/column descriptions, the `+ New Version` button is disabled.
- Unchanged files are inherited by default and do not need to be re-uploaded; only new or replaced files require descriptions to be provided again.
- The Step 2 page pre-fills the previous version's metadata by default, which authors can directly modify and submit.
- Before a new version is created, the system validates the completeness of "Version Notes + File Descriptions/Column Descriptions involved in this update".
- The P15 page does not display the administrator feedback body or processing actions; they are uniformly accessed via the P14 Message Center.
- If the current dataset has pending administrator suggestions, saving on P15 will pop up a confirmation asking "Mark as processed at the same time?".

**Step 1/2: Upload File Changes** (Entered after clicking `+ New Version`):

```
┌──────────────────────────────────────────────────────────┐
│  New Version  Step 1/2: Upload File Changes (V2 → V3)      │
│  ●──────○                                                 │
├──────────────────────────────────────────────────────────┤
│  Inherited Files (kept by default, no re-upload needed)    │
│  📊 train_set.csv  (4.2 MB)   [Keep] [Replace] [Remove]    │
│  📊 test_set.csv   (1.1 MB)   [Keep] [Replace] [Remove]    │
│                                                           │
│  + Add New File                                            │
│  Quota: 1.54 MB / 5 GB                                     │
│                                                           │
│  Diff Preview: + Added 0  ~ Replaced 1  - Removed 0        │
├──────────────────────────────────────────────────────────┤
│                  [Cancel]  [Next: Fill Info →]             │
└──────────────────────────────────────────────────────────┘
```

**Step 2/2: Fill Information & Submit** (Consistent with P09):

```
┌──────────────────────────────────────────────────────────┐
│  New Version  Step 2/2: Fill Information (V2 → V3)         │
│  ●──────●                                                 │
├──────────────────────────────────────────────────────────┤
│  Version Information                                       │
│  Version Notes (V3) *                                      │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Added 500 records; fixed ligand column naming;   │    │
│  │ supplemented source links                        │    │
│  └──────────────────────────────────────────────────┘    │
│  Suggestion: specify data source, scope of changes,        │
│  compatibility impact                                      │
│                                                           │
│  Change Summary relative to V2 (auto-generated, with notes)│
│  + Added files: 0   ~ Replaced files: 1   - Deleted files: 0│
│  Remarks (written into change_manifest):                   │
│  ┌──────────────────────────────────────────────────┐    │
│  │ Fixed ligand naming; added 500 reactions; added  │    │
│  │ DOI                                              │    │
│  └──────────────────────────────────────────────────┘    │
│                                                           │
├──────────────────────────────────────────────────────────┤
│  Basic Dataset Info (inherits V2 by default, editable)     │
│  Dataset Title * / Description * / Tag * / Source Type * / │
│  License *                                                 │
│  Source Link/DOI / Author Info (all pre-filled, editable)  │
│  (Status is not directly editable, determined by bottom btn)│
│                                                           │
├──────────────────────────────────────────────────────────┤
│  File Information (required only for added/replaced files) │
│  ── train_set.csv (Replaced) ──────────────────────────  │
│  About this file: This file has no description yet. [Edit] │
│  Expands on [Edit]: Table Description * + Column Explanations│
│  (Filled per column, identical to P09)                     │
│                                                           │
│  ── reagent_map.xlsx (Added) ──────────────────────────  │
│  About this file: This file has no description yet. [Edit] │
│                                                           │
│  Other inherited files (unchanged) use V2 descriptions, RO.│
├──────────────────────────────────────────────────────────┤
│  [← Back to File Changes]  [Save Draft]  [Create Version V3]│
│  Only saves current edits             Requires all mandatory│
│                                       checks to pass        │
└──────────────────────────────────────────────────────────┘
```

**Button Behavior and Constraints**:
- **[Save Draft]**: Saves the drafting progress (version_note, change_manifest, metadata). Calls `PUT /api/datasets/{id}/versions/{n}` to update the draft version record. If dataset-level metadata (Title/Description/Tag, etc.) was also modified, it calls `PUT /api/datasets/{owner}/{slug}` before calling the version update API. The version status remains as `draft`.
- **[Create Version V3]**: Semantically equivalent to "Submit for Online Review". The frontend must call `POST /api/datasets/{id}/submit-review` with the request body `{ "version_num": 3 }`. The backend updates the version's `dataset_versions.status` to `pending_review`, concurrently advances the dataset's `dataset_status` to `pending_review`, and records the previous state in `dataset_review_requests.pre_review_status`. Calling the version creation API is prohibited at this point.

Linked Save Prompt (appears only if there are pending suggestions):

```
┌──────────────────────────────────────────────┐
│  Detected 1 pending administrator suggestion  │
│  Mark as 'Processed' after saving?            │
│                                  [No] [Yes]  │
└──────────────────────────────────────────────┘
```

---

### P11 Admin Login Page

```
Independent Route: /admin/login
Not displayed in main navigation

┌──────────────────────────────────────────┐
│  RxnCommons Admin Console                │
│                                          │
│  Email                                   │
│  ┌──────────────────────────────────┐    │
│  │                                  │    │
│  └──────────────────────────────────┘    │
│                                          │
│  Password                                │
│  ┌──────────────────────────────────┐    │
│  │                                  │    │
│  └──────────────────────────────────┘    │
│                                          │
│  [         Login to Admin Console       ]│
└──────────────────────────────────────────┘
```

---

### P12 Admin Console

**Layout**:

```
┌──────────────────────────────────────────────────────────┐
│  [Logo] RxnCommons Admin Console   Datasets  Users  [Logout]│
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Dataset Management                                        │
│                                                            │
│  [All] [Pending] [Published] [Needs Rev] [Archived]        │
│  [Draft] [Unpublished]                     Search:[_______]│
│                                                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Title/Version  User      Submit Time Status   Actions   │
│  ├────────────────────────────────────────────────────┤    │
│  │ Suzuki_.../V2  yi_zhang  2026-03-13  Pending            │
│  │                                   [View] [Approve] [Suggest]│
│  ├────────────────────────────────────────────────────┤    │
│  │ Buchwald_.../V1 doyle_g  2026-02-21  Published          │
│  │                                   [View] [Suggest] [Unpublish]│
│  └────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

**Review Detail Drawer** (Triggered by clicking "Approve"):

```
┌──────────────────────────────────────────────────────────┐
│  Review Request #R20260313-018                             │
│  Dataset: Suzuki_coupling_HTE   Requested Version: V2      │
│  Applicant: yi_zhang   Submit Time: 2026-03-13 14:22       │
├──────────────────────────────────────────────────────────┤
│  Metadata Info (Submitted Content)                         │
│  Title, Description, Tag, Source Type, Source Link/DOI,    │
│  License, Author List                                      │
│  Version Notes: Added 500 samples, unified ligand naming...│
├──────────────────────────────────────────────────────────┤
│  File Info (Per-file Review)                               │
│  train_set.csv 4.2MB  4000 rows/12 cols                    │
│  - File Description: Filled                                │
│  - Column Desc. Completion: 12/12                          │
│  - Preview: First 5 rows (Read-only)                       │
│  test_set.csv 1.1MB  1000 rows/12 cols                     │
│  - File Description: Filled                                │
│  - Column Desc. Completion: 12/12                          │
├──────────────────────────────────────────────────────────┤
│  Compliance Checklist                                      │
│  ☑ Legal License  ☑ Traceable Source  ☑ File Scan Passed   │
│  ☑ Complete Metadata                                       │
│                                                            │
│  Review Comments (Required for Rejection)                  │
│  ┌──────────────────────────────────────────────────┐    │
│  │                                                  │    │
│  └──────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────┤
│  Historical Review Records (Collapsed)                     │
│  ▸ 2026-02-28  rejected  "Add source links and authors"    │
│  ▸ 2026-03-05  pending   "Waiting for current review"      │
├──────────────────────────────────────────────────────────┤
│      [Reject and Notify User]      [Approve and Publish]   │
└──────────────────────────────────────────────────────────┘
```

Note: Both rejection/approval results will be written to `dataset_review_requests` and the author will be notified via `P14 /messages`.

**Push Suggestion Modal** (Triggered by clicking "Suggest"):

```
┌─────────────────────────────────────────────────┐
│  Push Suggestion to User                          │
│  Dataset: Suzuki_coupling_HTE                     │
│                                                   │
│  Suggestion Content *                             │
│  ┌─────────────────────────────────────────┐      │
│  │ Suggest unifying ligands naming and adding       │      │
│  │ data source descriptions                         │      │
│  └─────────────────────────────────────────┘      │
│                                                   │
│  Status Action (Optional):                        │
│  □ Simultaneously mark dataset as revision_required │
│                                                   │
│              [Cancel]  [Push to User]             │
└─────────────────────────────────────────────────┘
```

After pushing, the message will enter the user's `P14 /messages` and display an unread badge (red dot/count) on the NAVBAR on logged-in pages.

---

### P13 Admin User Management

```
┌──────────────────────────────────────────────────────────┐
│  User Management                       Search: [_________] │
│                                                            │
│  ┌───────────────────────────────────────────────────┐     │
│  │ Username   Email          Reg. Time Datasets Storage│     │
│  ├───────────────────────────────────────────────────┤     │
│  │ yi_zhang   yi@pku.edu.cn  2025-01   5        1.5M   │     │
│  │            [View Datasets] [Adjust Quota] [Ban]     │     │
│  └───────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────┘
```

## 9. Page Navigation Logic

```
Visitor enters P01 (Home Page)
  ├── Click "Browse Datasets" → P02
  ├── Click "Upload Dataset" → P06 (Login) → P08
  ├── Press Enter in search box → P02 (with search parameters)
  ├── Click "Register" → P05
  └── Click "Log In" → P06

P02 (Dataset Marketplace)
  ├── Click any dataset card → P03
  └── Click "Download" (Not logged in) → P06 → Return to P03

P03 (Dataset Details)
  ├── Click "View" in version history → P04 (Historical Version)
  ├── Click "Download Current Version (Full)" in header (Not logged in) → P06
  ├── Click "Download" on right-side file (Not logged in) → P06
  ├── Click "Upvote" (Not logged in) → P06
  ├── Click "Copy Dataset Link / Copy Current Version Link" → Stay on current page (Copy successful prompt)
  ├── Click "Archive / Unarchive" (Owner) → Stay on P03 (State toggle)
  ├── Click "Edit" (Owner) → P10
  └── Click "+ New Version" at bottom right (Owner, and V1 is complete) → P15 Step 1 (File changes)

P04 (Historical Version)
  └── Click banner "View Latest Version" → P03

P05 (Registration)
  ├── Registration successful → Stay on current page (Prompt "Please check verification email")
  └── Click email link → P18 → P06

P06 (Login)
  └── Login successful
      ├── If redirected from an action requiring login → Return to original page
      └── Otherwise → P07 (User Dashboard)
  └── If email unverified → Allow login but restrict upload/comment/upvote, and prompt to resend verification email
  └── Click "Forgot Password" → P16

P16 (Forgot Password)
  ├── Click "Send Reset Email" → Stay on P16 (Prompt email sent)
  └── Click email link → P17

P17 (Reset Password)
  └── Click "Confirm Reset" → P06 (Log in again)

Global Message Entry (Any logged-in page)
  ├── Click "Messages" in NAVBAR → P14 (Message Center)
  ├── Click message "View Details" → Corresponding dataset P03
  └── Click message "View and Process" → P10 (Metadata Edit)

P07 (User Dashboard)
  ├── Click "+ Upload New Dataset" → P08
  ├── Click "Enter Message Center" → P14
  ├── Click "View and Process" (Message excerpt) → P10 (Metadata Edit)
  ├── Click "Archive / Unarchive" → Stay on P07 (State toggle)
  ├── Click dataset "Edit" → P10
  └── Click dataset title → P03

P14 (Message Center)
  ├── Click "View Dataset" → P03
  ├── Click "Go to Process" → P10 (Metadata Edit)
  └── Click "Mark as Read" → Stay on P14 (State update)

P08 (Upload Step 1)
  ├── File upload complete, click "Next" → P09
  └── Click "Cancel" → P07

P09 (Upload Step 2)
  ├── Click "Save Draft" → P03 (State is Draft)
  ├── Click "Submit for Publishing Review" → P03 (State is Pending Review)
  └── Click "← Back" → P08

P10 (Metadata Edit)
  ├── Click "Save Metadata" → Stay on P03 (No version bump)
  ├── Click "Create New Revision" → P15 Step 1
  └── Click "Cancel" → Return to P03

P15 (New Version Two-Step)
  ├── Step 1: File changes complete, click "Next" → Step 2 (Information Entry)
  ├── Step 2: Click "Create New Version" → P03 (Switch to latest version)
  └── Click "Cancel" at any step → Return to P03

P11 (Admin Login)
  └── Login successful → P12

P12 (Admin Dashboard)
  ├── Click "View" → P03
  ├── Click "Review" → Open Review Details Drawer (Metadata + File Info)
  ├── Review Approved → P03 (State changes to Published)
  ├── Review Rejected → P14 (User receives rejection reason message)
  ├── Click "Unpublish" → P03 (State changes to Unpublished)
  ├── Click "Suggest" → Open Push Notification Modal
  └── Click "Users" at the top → P13

P13 (User Management)
  └── Click "View Datasets" → P02 (Filter by this user)
```
## 10. Security Policies (Mandatory for Production)

### 10.1 Authentication & Session Security

- Passwords must use strong hashing algorithms (Argon2id or bcrypt); reversible encryption is strictly prohibited.
- Access Tokens are short-lived (15 minutes); Refresh Tokens are long-lived (7 days) and require mandatory rotation.
- Refresh Tokens are stored only as hashes; upon logout, password change, or user ban, they are immediately revoked in bulk.
- Password resets utilize a one-time short-lived token; all Refresh Tokens for that user are revoked upon successful reset.
- Administrator backend login is isolated from regular user login.
- MFA (TOTP) is slated as a v2 security enhancement: Extension points are reserved in v1, but independent MFA data tables, binding workflows, and verification pages are not mandatory in the current delivery scope to avoid scope creep.

### 10.2 Permission Model & Privilege Escalation Protection

- Backend enforces RBAC + object-level authorization; frontend permission checks are solely for UI rendering.
- All `dataset/file/version` endpoints re-verify owner/public status/admin privileges after querying.
- Externally visible IDs like `file_id` and `dataset_id` must not be used as direct authorization proofs.
- High-risk administrator operations (takedown, quota adjustment, ban) require secondary confirmation and must be logged in the audit trail.

### 10.3 Upload & File Security

- File uploads follow a three-stage workflow: "Quarantine -> Scan -> Production".
- Malicious file scanning (e.g., ClamAV) is enabled; default action is to reject publication upon scan failure or timeout.
- Limit archive extraction depth, total extracted size, and number of files to prevent zip bombs.
- File names are sanitized before database insertion; object keys are system-generated, and path concatenation is prohibited.

### 10.4 Application Layer Protection

- API Rate Limiting: Distinct thresholds configured for login, upload, download, search, and commenting.
- Bruteforce Protection on Login: Exceeding consecutive failure thresholds triggers a short-term lockout and CAPTCHA validation.
- Strict Input Validation: Validate length, type, enums, URL/DOI formats; reject undeclared fields.
- Output Security: XSS filtering applied before rendering user content; internal implementation details are hidden in error responses.

### 10.5 Data & Infrastructure Security

- Object storage defaults to private; downloads utilize short-lived presigned URLs (e.g., expiring in 60 seconds).
- HTTPS applied across the entire transmission link; strict HSTS enabled, weak TLS suites disabled.
- Principle of least privilege applied to database and object storage access; production credentials managed via Key Management System (KMS).
- Daily backups for database and metadata; restoration drills conducted at least quarterly.

### 10.6 Audit & Alerting

- Establish a minimal set of audit events: login failures, token revocations, authorization denials, and administrator operations.
- Security logs are centralized, retained for no less than 180 days, and searchable by user/IP.
- Anomaly Alerting: Bruteforce logins, unexpected download spikes, bulk upload failures, abnormal administrator behaviors.
- Security Response SLO: High-risk alerts must be acknowledged within 30 minutes, with a resolution conclusion provided within 24 hours.

---

## 11. Deployment Strategy

### 11.1 Development Environment

```bash
# Frontend
cd frontend && npm run dev          # Next.js development server :3000

# Backend
cd backend && uvicorn main:app --reload   # FastAPI :8000

# Async Worker
cd backend && celery -A worker.app worker -l info

# Scheduled Tasks
cd backend && celery -A worker.app beat -l info

# Dependency Services
docker-compose up postgres redis minio clamav   # Local dependencies
```

### 11.2 Production Environment Architecture

```
User → CDN/WAF/Nginx (Reverse Proxy + HTTPS + Cache)
   ├── / → Next.js (Frontend)
   └── /api → FastAPI (Backend API)

FastAPI → PostgreSQL (Primary Database + Search Read Model)
  → Redis (Sessions + Cache + Rate Limiting + Broker)
  → MinIO (Object Storage)
  → ClamAV (Upload Scanning)

Celery Worker → Redis (Fetch Tasks)
        → PostgreSQL (Update Metadata/Search Projections)
        → MinIO (Generate Previews/Cleanup Files)
        → ClamAV (Compensatory Scanning)

Celery Beat / Scheduler → Redis (Scheduled Task Dispatch)
           → Worker (Periodic Inspection, Projection Rebuild, Failure Retry)
```

### 11.3 docker-compose Services List

```yaml
services:
  frontend:    # Next.js, port 3000
  backend:     # FastAPI, port 8000
  worker:      # Celery Worker, handles parsing/cleanup/projections
  scheduler:   # Celery Beat / Scheduled Tasks
  postgres:    # PostgreSQL 15
  redis:       # Redis 7
  minio:       # MinIO Object Storage
  clamav:      # File malicious content scanning
  nginx:       # Reverse Proxy
```

### 11.4 Key Environment Variables

```
DATABASE_URL          PostgreSQL connection string
REDIS_URL             Redis connection string
CELERY_BROKER_URL     Async task broker connection string
CELERY_RESULT_BACKEND Async task result storage connection string
MINIO_ENDPOINT        MinIO address
MINIO_ACCESS_KEY      MinIO access key
MINIO_SECRET_KEY      MinIO secret key
JWT_SECRET            JWT signing secret
ACCESS_TOKEN_EXPIRE_MIN   Access Token expiration in minutes (recommended: 15)
REFRESH_TOKEN_EXPIRE_DAYS Refresh Token expiration in days (recommended: 7)
REFRESH_TOKEN_COOKIE_SECURE Whether to send Refresh Cookie over HTTPS only
RATE_LIMIT_REDIS_URL       Rate limiting storage connection string
CORS_ALLOW_ORIGINS         CORS allowed origins whitelist
SECURITY_ALERT_WEBHOOK      Security alert push webhook
PASSWORD_RESET_TOKEN_EXPIRE_MIN  Reset token expiration in minutes (recommended: 30)
PASSWORD_RESET_SECRET      Password reset token signing secret
EMAIL_VERIFY_TOKEN_EXPIRE_MIN    Email verification token expiration in minutes (recommended: 1440)
EMAIL_VERIFY_SECRET              Email verification token signing secret
SMTP_HOST                 Mail server address
SMTP_PORT                 Mail server port
SMTP_USER                 Mail account
SMTP_PASSWORD             Mail password or authorization code
MAIL_FROM                 Sender address
ADMIN_EMAIL           Administrator email (initialization)
ADMIN_PASSWORD        Administrator password (initialization)
```

---

## 12. R&D Team Implementation & Delivery Specifications

To ensure this document is successfully translated into code, the third-party development team must adhere to the following supplementary requirements:

### 12.1 Business Boundaries & Chemistry Domain Clarifications
- **Pure Hosting Positioning**: The v1 version of this platform is positioned as a general file hosting system and **will not** perform deep semantic parsing of chemical structures (backend is not required to depend on RDKit for SMILES validity verification). It should be treated as plain text string processing.
- **Future Extension Reservation**: If the frontend needs to preview SMILES structures, it is recommended to introduce lightweight libraries like `SMILES Drawer` or `Ketcher` for Canvas rendering, without relying on backend computations.

### 12.2 Prerequisites for Development
- **High-Fidelity UI/UX Design Assets**: Prior to development, complete Figma interaction and high-fidelity UI design mockups must be provided based on this document, defining precise color specifications, typography, and various component states (Hover/Active/Disabled). The terminal ASCII diagrams in this document are purely for logical illustration and cannot replace UI mockups.
- **API Swagger/OpenAPI Documentation**: Standardized API contracts (OpenAPI 3.0 specification) must be produced in the first week of development, explicitly defining the input/output structures of complex endpoints and precise error code definitions (e.g., specific formats for 400/403/422).

### 12.3 Third-Party Service Dependency Conventions
- **Email Service**: The backend needs to integrate third-party email services (such as SendGrid, Aliyun DirectMail) for registration verification and password recovery. The team must develop corresponding HTML email templates.
- **Internationalization (i18n)**: The platform targets the international academic community. The frontend must introduce `react-i18next` or `next-intl`. UI texts must support bilingual Chinese and English. Placeholders should be reserved during the hard-coding phase. English must be the default language for the first release. Design mockups and database configurations should be based on English.

**Minimum Required Email Templates (English Initial Release, Mandatory)**:

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

Note: The above texts are the default English templates; Chinese templates should use structurally identical translations. The development team is not permitted to arbitrarily alter the core meaning.

### 12.4 System Initialization Strategy
- **Root Administrator Restrictions**: The system does not allow public registration for administrators. A backend command-line tool (e.g., `python manage.py createsuperuser`) must be implemented in the deployment script to create the "Primary Administrator". Subsequent administrator distributions will be managed by this primary administrator via the backend system.

---

*End of Document | RxnCommons v1.0 System Design Specification*