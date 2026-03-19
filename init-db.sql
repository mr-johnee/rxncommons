-- 启用 pg_trgm 扩展以支持模糊查询和 FTS (Full Text Search) 全文搜索
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
-- 启用 pgcrypto 以获取 gen_random_uuid() 的支持（兼容性保障）
CREATE EXTENSION IF NOT EXISTS "pgcrypto";