"""
PostgreSQL Schema & Mock Data Seeder
====================================
Seeds an enterprise Postgres instance with multi-department mock data:
- finance.quarterly_reports & finance.invoices
- engineering.services & engineering.deployments
- hr.employees

Usage:
  python seed_postgres.py --url "postgresql://user:pass@host:5432/dbname"
  or set POSTGRES_URL environment variable and run:
  python seed_postgres.py
"""

import sys
import os
import argparse
import psycopg2

SCHEMA_SQL = """
-- 1. Create Department Schemas
CREATE SCHEMA IF NOT EXISTS finance;
CREATE SCHEMA IF NOT EXISTS engineering;
CREATE SCHEMA IF NOT EXISTS hr;

-- 2. Finance Tables
CREATE TABLE IF NOT EXISTS finance.quarterly_reports (
    id SERIAL PRIMARY KEY,
    fiscal_year INT NOT NULL,
    quarter VARCHAR(10) NOT NULL,
    revenue NUMERIC(15, 2) NOT NULL,
    net_profit NUMERIC(15, 2) NOT NULL,
    growth_rate VARCHAR(10) NOT NULL
);

CREATE TABLE IF NOT EXISTS finance.invoices (
    invoice_id VARCHAR(32) PRIMARY KEY,
    client_name VARCHAR(100) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL,
    status VARCHAR(20) NOT NULL,
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL
);

-- 3. Engineering Tables
CREATE TABLE IF NOT EXISTS engineering.services (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(64) UNIQUE NOT NULL,
    tier VARCHAR(10) NOT NULL,
    language VARCHAR(32) NOT NULL,
    health_status VARCHAR(20) NOT NULL,
    p99_latency_ms INT NOT NULL
);

CREATE TABLE IF NOT EXISTS engineering.deployments (
    deployment_id VARCHAR(32) PRIMARY KEY,
    service_name VARCHAR(64) NOT NULL,
    version VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    deployed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. HR Tables
CREATE TABLE IF NOT EXISTS hr.employees (
    emp_id VARCHAR(16) PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    department VARCHAR(50) NOT NULL,
    job_title VARCHAR(100) NOT NULL,
    salary NUMERIC(12, 2) NOT NULL,
    hire_date DATE NOT NULL
);
"""

MOCK_DATA_SQL = """
-- Clear previous data
TRUNCATE TABLE finance.quarterly_reports, finance.invoices, engineering.services, engineering.deployments, hr.employees CASCADE;

-- Insert Finance Data
INSERT INTO finance.quarterly_reports (fiscal_year, quarter, revenue, net_profit, growth_rate) VALUES
(2026, '2026-Q1', 1500000.00, 350000.00, '12%'),
(2026, '2026-Q2', 1850000.00, 420000.00, '15%'),
(2026, '2026-Q3', 2100000.00, 510000.00, '18%'),
(2025, '2025-Q4', 1340000.00, 290000.00, '10%');

INSERT INTO finance.invoices (invoice_id, client_name, amount, status, issue_date, due_date) VALUES
('INV-2026-001', 'Acme Global Corp', 45000.00, 'PAID', '2026-01-15', '2026-02-15'),
('INV-2026-002', 'Starlight Technologies', 128500.00, 'PAID', '2026-02-01', '2026-03-01'),
('INV-2026-003', 'Apex Logistics', 78900.00, 'PENDING', '2026-03-10', '2026-04-10'),
('INV-2026-004', 'CloudScale Inc', 210000.00, 'PENDING', '2026-03-15', '2026-04-15');

-- Insert Engineering Data
INSERT INTO engineering.services (service_name, tier, language, health_status, p99_latency_ms) VALUES
('api-gateway', 'Tier-1', 'Go', 'HEALTHY', 12),
('auth-service', 'Tier-1', 'Python', 'HEALTHY', 18),
('data-pipeline', 'Tier-2', 'Rust', 'HEALTHY', 45),
('billing-engine', 'Tier-1', 'Java', 'HEALTHY', 25),
('analytics-worker', 'Tier-3', 'Python', 'DEGRADED', 180);

INSERT INTO engineering.deployments (deployment_id, service_name, version, status, deployed_at) VALUES
('DEP-901', 'api-gateway', 'v2.4.1', 'SUCCESS', '2026-09-20 14:32:00'),
('DEP-902', 'auth-service', 'v1.8.0', 'SUCCESS', '2026-09-21 09:15:00'),
('DEP-903', 'data-pipeline', 'v3.1.2', 'SUCCESS', '2026-09-22 17:40:00'),
('DEP-904', 'billing-engine', 'v2.0.4', 'SUCCESS', '2026-09-24 11:20:00');

-- Insert HR Data
INSERT INTO hr.employees (emp_id, full_name, department, job_title, salary, hire_date) VALUES
('EMP-001', 'Alice Johnson', 'finance', 'Senior Financial Analyst', 125000.00, '2022-03-15'),
('EMP-002', 'Bob Smith', 'engineering', 'Principal Cloud Architect', 175000.00, '2021-06-01'),
('EMP-003', 'Carol Martinez', 'hr', 'VP of People Operations', 160000.00, '2020-01-10'),
('EMP-004', 'David Lee', 'engineering', 'Staff Security Engineer', 168000.00, '2023-08-20'),
('EMP-005', 'Emma Watson', 'finance', 'Head of FP&A', 190000.00, '2019-11-05');
"""

def seed_database(db_url: str):
    print("=" * 65)
    print("POSTGRESQL ENTERPRISE MOCK DATA SEEDER")
    print("=" * 65)
    print(f"Connecting to database...")
    
    try:
        conn = psycopg2.connect(db_url, connect_timeout=15)
        conn.autocommit = True
        cur = conn.cursor()
        print("Connected successfully!")
        
        print("\n1. Creating Schemas & Tables...")
        cur.execute(SCHEMA_SQL)
        print("   Schemas & Tables created.")
        
        print("2. Inserting Mock Enterprise Data...")
        cur.execute(MOCK_DATA_SQL)
        print("   Mock records inserted successfully.")
        
        print("\n3. Verifying Seeded Tables:")
        cur.execute("""
            SELECT table_schema || '.' || table_name AS full_name
            FROM information_schema.tables 
            WHERE table_schema IN ('finance', 'engineering', 'hr')
            ORDER BY table_schema, table_name;
        """)
        tables = [r[0] for r in cur.fetchall()]
        for t in tables:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cur.fetchone()[0]
            print(f"   • {t:30} ({cnt} records)")
            
        cur.close()
        conn.close()
        print("\n" + "=" * 65)
        print("SEEDING COMPLETE! Database is ready for queries.")
        print("=" * 65)
    except Exception as e:
        print(f"\n[ERROR] Failed to seed database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed PostgreSQL database with mock data")
    parser.add_argument("--url", default=os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL"), help="PostgreSQL connection string")
    args = parser.parse_args()
    
    if not args.url:
        print("Error: No database URL provided.")
        print("Provide via --url or set the POSTGRES_URL environment variable.")
        print('Example: python seed_postgres.py --url "postgresql://user:password@host:5432/dbname"')
        sys.exit(1)
        
    seed_database(args.url)
