-- Governance Analytics Schema for Tamil Nadu State CM Dashboard

CREATE TYPE kpi_domain AS ENUM ('health', 'education', 'agriculture', 'infrastructure', 'economy', 'finance');
CREATE TYPE kpi_direction AS ENUM ('up_good', 'down_good');
CREATE TYPE frequency_unit AS ENUM ('daily', 'weekly', 'monthly', 'quarterly', 'yearly');

CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    code VARCHAR(16) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE districts (
    id SERIAL PRIMARY KEY,
    code VARCHAR(16) NOT NULL UNIQUE,
    name VARCHAR(128) NOT NULL,
    region VARCHAR(64),
    population INTEGER,
    state VARCHAR(64) NOT NULL DEFAULT 'Tamil Nadu',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    district_id INTEGER REFERENCES districts(id) ON DELETE SET NULL,
    start_date DATE,
    target_end_date DATE,
    status VARCHAR(64) NOT NULL DEFAULT 'planned',
    citizen_impact SMALLINT NOT NULL CHECK (citizen_impact BETWEEN 1 AND 10),
    urgency SMALLINT NOT NULL CHECK (urgency BETWEEN 1 AND 10),
    economic_benefit SMALLINT NOT NULL CHECK (economic_benefit BETWEEN 1 AND 10),
    feasibility SMALLINT NOT NULL CHECK (feasibility BETWEEN 1 AND 10),
    impact_score NUMERIC(5,2) GENERATED ALWAYS AS (
        (citizen_impact * 0.35 + urgency * 0.25 + economic_benefit * 0.25 + feasibility * 0.15)
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE kpis (
    id SERIAL PRIMARY KEY,
    code VARCHAR(32) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    unit VARCHAR(64) NOT NULL,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    domain kpi_domain NOT NULL,
    direction kpi_direction NOT NULL,
    frequency frequency_unit NOT NULL,
    formula_note TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE kpi_values (
    id SERIAL PRIMARY KEY,
    kpi_id INTEGER NOT NULL REFERENCES kpis(id) ON DELETE CASCADE,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    district_id INTEGER REFERENCES districts(id) ON DELETE SET NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    value NUMERIC(18,4) NOT NULL,
    target_value NUMERIC(18,4),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE budget_allocations (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    fiscal_year VARCHAR(16) NOT NULL,
    allocation_amount NUMERIC(18,2) NOT NULL CHECK (allocation_amount >= 0),
    released_amount NUMERIC(18,2) NOT NULL DEFAULT 0 CHECK (released_amount >= 0),
    status VARCHAR(64) NOT NULL DEFAULT 'approved',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE manpower (
    id SERIAL PRIMARY KEY,
    department_id INTEGER NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    district_id INTEGER REFERENCES districts(id) ON DELETE SET NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    role VARCHAR(128) NOT NULL,
    headcount INTEGER NOT NULL CHECK (headcount >= 0),
    category VARCHAR(64) NOT NULL,
    effective_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    alert_code VARCHAR(32) NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    department_id INTEGER REFERENCES departments(id) ON DELETE SET NULL,
    district_id INTEGER REFERENCES districts(id) ON DELETE SET NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    kpi_id INTEGER REFERENCES kpis(id) ON DELETE SET NULL,
    severity VARCHAR(32) NOT NULL DEFAULT 'medium',
    status VARCHAR(32) NOT NULL DEFAULT 'open',
    triggered_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Sample Seed Data
INSERT INTO departments (code, name, description) VALUES
('HEALTH', 'Health Department', 'State health and family welfare initiatives'),
('EDU', 'Education Department', 'Primary, secondary, and higher education management');

INSERT INTO districts (code, name, region, population) VALUES
('CHN', 'Chennai', 'Coastal', 4646732),
('MAS', 'Madurai', 'Central', 3152373);

INSERT INTO projects (code, name, description, department_id, district_id, start_date, target_end_date, status, citizen_impact, urgency, economic_benefit, feasibility) VALUES
('PROJECT_HEALTH_01', 'Primary Health Centre Upgrade', 'Upgrade PHC infrastructure across selected districts.', 1, 1, '2025-07-01', '2026-12-31', 'active', 9, 8, 7, 8),
('PROJECT_EDU_01', 'Digital Classrooms Initiative', 'Deploy digital classrooms in rural schools.', 2, 2, '2025-04-01', '2026-09-30', 'active', 8, 7, 6, 8);

INSERT INTO kpis (code, name, description, unit, department_id, domain, direction, frequency, formula_note) VALUES
('KPI_H1', 'Immunization Coverage Rate', 'percent', 1, 'Coverage of routine immunization for children', 'health', 'up_good', 'monthly', 'Children immunized / eligible population * 100'),
('KPI_E1', 'Student Attendance Rate', 'percent', 2, 'Average student attendance in government schools', 'education', 'up_good', 'monthly', 'Present students / enrolled students * 100'),
('KPI_A1', 'Irrigated Area Expansion', 'hectares', 1, 'Annual increase in irrigated farmland', 'agriculture', 'up_good', 'quarterly', 'Total irrigated hectares - baseline hectares'),
('KPI_I1', 'Road Network Completion', 'kilometers', 1, 'Length of completed rural roads in the financial year', 'infrastructure', 'up_good', 'yearly', 'Sum of completed road kilometers across districts'),
('KPI_F1', 'GST Revenue Growth', 'percent', 1, 'Year-over-year GST revenue increase', 'finance', 'up_good', 'quarterly', 'Current GST collection / prior GST collection - 1'),
('KPI_ECO1', 'Manufacturing Employment Growth', 'percent', 2, 'Growth in manufacturing sector employment', 'economy', 'up_good', 'monthly', 'Current employment / prior employment - 1');

INSERT INTO kpi_values (kpi_id, project_id, district_id, recorded_at, value, target_value, notes) VALUES
(1, 1, 1, '2025-08-01 09:00:00+00', 82.5, 85.0, 'Chennai PHCs showing strong progress'),
(2, 2, 2, '2025-08-01 09:00:00+00', 91.2, 92.0, 'Madurai attendance normalizing after reopening'),
(3, NULL, 2, '2025-09-01 09:00:00+00', 1430, 1500, 'Irrigated acreage expansion in Madurai district'),
(4, 1, 1, '2026-03-31 09:00:00+00', 120.5, 150.0, 'Rural road completion progress'),
(5, NULL, NULL, '2026-03-31 09:00:00+00', 12.4, 10.0, 'Quarterly GST revenue growth'),
(6, NULL, NULL, '2025-12-31 09:00:00+00', 4.8, 5.5, 'Manufacturing employment growth by end of year');

INSERT INTO budget_allocations (project_id, department_id, fiscal_year, allocation_amount, released_amount, status) VALUES
(1, 1, '2025-26', 125000000.00, 45000000.00, 'approved'),
(2, 2, '2025-26', 86000000.00, 32000000.00, 'approved');

INSERT INTO manpower (department_id, district_id, project_id, role, headcount, category, effective_date) VALUES
(1, 1, 1, 'Medical Officer', 12, 'technical', '2025-07-01'),
(2, 2, 2, 'ICT Coordinator', 5, 'support', '2025-04-01');

INSERT INTO alerts (alert_code, title, description, department_id, district_id, project_id, kpi_id, severity, status, triggered_at) VALUES
('ALRT_HEALTH_01', 'Immunization Coverage Alert', 'Coverage below target in Chennai PHCs.', 1, 1, 1, 1, 'high', 'open', '2025-08-02 10:00:00+00'),
('ALRT_EDU_01', 'Attendance Drop Alert', 'Attendance rate dropped below threshold in Madurai.', 2, 2, 2, 2, 'medium', 'open', '2025-08-03 11:00:00+00');
