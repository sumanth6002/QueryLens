-- QueryLens application database bootstrap
-- Run manually if you prefer SQL over: python -m database.init_db

CREATE DATABASE IF NOT EXISTS querylens
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE querylens;

-- Tables are created by SQLAlchemy via: python -m database.init_db
-- Expected tables after initialization:
--   users
--   workspaces
--   schema_snapshots
--   queries
--   query_runs
--   functional_dependencies
--   normalization_reports
--   index_recommendations
