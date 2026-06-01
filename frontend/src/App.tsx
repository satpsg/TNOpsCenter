import { useEffect, useState, type ReactNode } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

type KpiCard = {
  name: string
  latest: number
  unit: string
  trend_7d?: number
  trend_30d?: number
}

type HeatmapRow = {
  name: string
  performance_score: number
}

type ProjectRow = {
  name: string
  impact_score: number
}

type AlertRow = {
  title: string
  severity: string
  status: string
}

type BudgetRow = {
  department_id?: number
  department_name?: string
  fiscal_year: string
  project_id?: number
  project_code?: string
  project_name?: string
  allocated: number
  spent: number
  remaining: number
}

type GapRow = {
  department_id?: number
  department_name?: string
  district_id?: number
  district_name?: string
  required: number
  available: number
  deficit: number
  deficit_score: number
}

type PriorityRow = {
  project_id: number
  project_code?: string
  project_name?: string
  impact?: number
  urgency?: number
  economic_benefit?: number
  feasibility?: number
  required?: number
  available?: number
  resource_gap: number
  priority_score: number
}

type LiveAlertRow = {
  alert_id: number
  alert_code: string
  title: string
  description?: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  district_id?: number
  status: string
  triggered_at: string
  acknowledged_at?: string
}

type BudgetData = {
  departments: BudgetRow[]
  projects: BudgetRow[]
}

type GapData = {
  by_department: GapRow[]
  by_district: GapRow[]
}

type SummaryData = {
  kpi_cards: KpiCard[]
  project_count: number
  open_alerts: number
}

const TABS: Array<{ key: 'dashboard' | 'budget' | 'gap'; label: string }> = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'budget', label: 'Budget Overview' },
  { key: 'gap', label: 'Resource Gap Analysis' },
]

const MOCK_KPI: KpiCard[] = [
  { name: 'Immunization Rate', latest: 82.5, unit: '%', trend_7d: 1.4, trend_30d: 3.1 },
  { name: 'Student Attendance', latest: 91.2, unit: '%', trend_7d: -0.1, trend_30d: 0.8 },
  { name: 'Road Completion', latest: 120.5, unit: 'km', trend_7d: 5.2, trend_30d: 18.4 },
]
const MOCK_DISTRICTS = [
  { name: 'Chennai', performance_score: 82.4 },
  { name: 'Madurai', performance_score: 76.2 },
  { name: 'Coimbatore', performance_score: 68.1 },
  { name: 'Tirunelveli', performance_score: 71.9 },
  { name: 'Salem', performance_score: 65.7 },
]
const MOCK_PROJECTS = [
  { name: 'PHC Upgrade', impact_score: 86.2 },
  { name: 'Digital Classrooms', impact_score: 83.4 },
  { name: 'Irrigation Expansion', impact_score: 79.8 },
]
const MOCK_ALERTS = [
  { title: 'Immunization below target', severity: 'high', status: 'open' },
  { title: 'Attendance dip in Madurai', severity: 'medium', status: 'open' },
]
const MOCK_BUDGET = {
  departments: [
    { department_id: 1, department_name: 'Health', fiscal_year: '2025-26', allocated: 42000000, spent: 23500000, remaining: 18500000 },
    { department_id: 2, department_name: 'Education', fiscal_year: '2025-26', allocated: 19000000, spent: 11200000, remaining: 7800000 },
  ],
  projects: [
    { project_id: 1, project_code: 'HEALTH-001', project_name: 'Rural Clinic Buildout', fiscal_year: '2025-26', allocated: 12000000, spent: 7200000, remaining: 4800000 },
    { project_id: 2, project_code: 'EDU-019', project_name: 'School Digital Access', fiscal_year: '2025-26', allocated: 8500000, spent: 5400000, remaining: 3100000 },
  ],
}
const MOCK_GAP = {
  by_department: [
    { department_id: 1, department_name: 'Health', required: 350, available: 280, deficit: 70, deficit_score: 20.0 },
    { department_id: 2, department_name: 'Education', required: 180, available: 145, deficit: 35, deficit_score: 19.44 },
  ],
  by_district: [
    { district_id: 1, district_name: 'Chennai', required: 210, available: 175, deficit: 35, deficit_score: 16.67 },
    { district_id: 2, district_name: 'Madurai', required: 160, available: 125, deficit: 35, deficit_score: 21.88 },
  ],
}
const MOCK_PRIORITIES = [
  { project_id: 1, project_code: 'HEALTH-001', project_name: 'Rural Clinic Buildout', priority_score: 8.7, resource_gap: 4.0 },
  { project_id: 2, project_code: 'EDU-019', project_name: 'School Digital Access', priority_score: 8.2, resource_gap: 3.0 },
]

const COLORS = {
  bg: '#0a0e1a',
  panel: '#0f1629',
  border: '#1e2d4a',
  accent: '#d4a017',
  accentSoft: '#f0c040',
  teal: '#00c9a7',
  red: '#ff4d6d',
  orange: '#ff8c42',
  blue: '#3a86ff',
  muted: '#4a6080',
  text: '#c8d8f0',
  textSoft: '#7a9abf',
}

const fmt = (n: number, dec = 1) => n?.toLocaleString('en-IN', { maximumFractionDigits: dec })
const fmtCr = (n: number) => `₹${fmt(n)} Cr`

const mockData = {
  economy: {
    gdp: 27.53,
    gdpGrowth: 8.2,
    gsdp: 3148000,
    revenue: 284500,
    expenditure: 261200,
    fiscalDeficit: 3.2,
    exports: 184300,
    fdi: 42600,
    trend: [22.1, 23.4, 24.8, 25.9, 26.7, 27.53],
  },
  governance: {
    schemesActive: 148,
    schemesCompleted: 312,
    pendingGrievances: 14283,
    grievancesResolved: 98421,
    budgetUtilization: 79.4,
    corruptionComplaints: 312,
    vigilanceActions: 289,
  },
  infrastructure: {
    roadsKm: 199040,
    roadsGoodCondition: 78.4,
    powerGenMW: 21480,
    powerSurplus: 12.3,
    waterCoverage: 84.6,
    metroRoutes: 6,
    airportsOperational: 8,
    portsActive: 15,
    projectsOngoing: 2847,
    projectsDelayed: 341,
  },
  welfare: {
    pdsCardholders: 2.15,
    aadhaarLinked: 98.7,
    healthcareVisits: 184200,
    hospitalBeds: 91440,
    schoolEnrollment: 98.2,
    dropoutRate: 0.8,
    womenSHG: 612000,
    farmerBeneficiaries: 4200000,
  },
  environment: {
    forestCover: 17.6,
    airQualityAQI: 87,
    waterBodiesRestored: 2341,
    solarMW: 8420,
    evRegistrations: 184200,
    swachhtaScore: 74.2,
  },
  districts: [
    { name: 'Chennai', pop: 87.5, gdp: 14.2, dev: 92, alert: false },
    { name: 'Coimbatore', pop: 34.6, gdp: 9.8, dev: 88, alert: false },
    { name: 'Madurai', pop: 30.4, gdp: 6.1, dev: 81, alert: false },
    { name: 'Tiruchirappalli', pop: 27.2, gdp: 5.4, dev: 79, alert: false },
    { name: 'Salem', pop: 23.1, gdp: 4.2, dev: 74, alert: true },
    { name: 'Tirunelveli', pop: 18.7, gdp: 3.1, dev: 71, alert: false },
    { name: 'Vellore', pop: 16.2, gdp: 2.8, dev: 68, alert: true },
    { name: 'Erode', pop: 15.8, gdp: 2.6, dev: 72, alert: false },
    { name: 'Dindigul', pop: 12.1, gdp: 1.9, dev: 63, alert: true },
    { name: 'Thanjavur', pop: 24.0, gdp: 3.8, dev: 76, alert: false },
    { name: 'Kancheepuram', pop: 19.4, gdp: 3.4, dev: 77, alert: false },
    { name: 'Dharmapuri', pop: 10.6, gdp: 1.4, dev: 58, alert: true },
  ],
  alerts: [
    { id: 1, type: 'critical', sector: 'Health', msg: 'Dengue surge in Vellore · 312 cases this week', time: '2m ago' },
    { id: 2, type: 'warning', sector: 'Water', msg: 'Poondi reservoir at 34% · Chennai water advisory needed', time: '18m ago' },
    { id: 3, type: 'info', sector: 'Economy', msg: 'IT exports up 14.3% QoQ · Q1 FY27 milestone', time: '1h ago' },
    { id: 4, type: 'warning', sector: 'Power', msg: 'Grid demand peak at 19,840 MW · 6 PM forecast', time: '2h ago' },
    { id: 5, type: 'info', sector: 'Welfare', msg: 'Kalaignar Magalir Urimai scheme: 42L disbursed today', time: '3h ago' },
    { id: 6, type: 'critical', sector: 'Infrastructure', msg: 'NH-44 landslide near Theni · traffic diverted', time: '5h ago' },
  ] as LiveAlertItem[],
  shortTermGoals: [
    { goal: 'Resolve 50K pending grievances', progress: 72, deadline: 'Jun 2026' },
    { goal: 'Complete 500 km new road network', progress: 58, deadline: 'Jul 2026' },
    { goal: 'Enroll 1M in health insurance', progress: 81, deadline: 'Jun 2026' },
    { goal: 'Achieve 90% budget utilization', progress: 88, deadline: 'Mar 2027' },
    { goal: 'Plant 1 Crore trees (Green TN)', progress: 64, deadline: 'Aug 2026' },
  ],
  longTermGoals: [
    { goal: 'Tamil Nadu as $1T economy by 2047', progress: 28, milestone: '2047' },
    { goal: '100% renewable energy by 2035', progress: 42, milestone: '2035' },
    { goal: 'Zero poverty districts', progress: 31, milestone: '2030' },
    { goal: 'Universal healthcare coverage', progress: 67, milestone: '2030' },
    { goal: 'Smart cities in all 38 districts', progress: 19, milestone: '2035' },
  ],
}

function LiveClock() {
  const [time, setTime] = useState(new Date())

  useEffect(() => {
    const interval = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="live-clock">
      <div className="live-clock-time">
        {time.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
      </div>
      <div className="live-clock-date">
        {time.toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}
      </div>
    </div>
  )
}

function KPICard({ icon, label, value, sub, color = COLORS.teal, pulse }: { icon: string; label: string; value: string; sub?: string; color?: string; pulse?: boolean }) {
  return (
    <div className="kpi-summary-card" style={{ borderLeft: `3px solid ${color}` }}>
      {pulse && <div className="pulse-dot" style={{ boxShadow: `0 0 8px ${COLORS.red}` }} />}
      <div className="kpi-summary-icon">{icon}</div>
      <div className="kpi-summary-value" style={{ color }}>{value}</div>
      <div className="kpi-summary-label">{label}</div>
      {sub && <div className="kpi-summary-note">{sub}</div>}
    </div>
  )
}

function SectionTitle({ children, icon }: { children: ReactNode; icon: string }) {
  return (
    <div className="section-title">
      <span className="section-title-icon">{icon}</span>
      <span>{children}</span>
      <div className="section-title-divider" />
    </div>
  )
}

function GoalBar({ goal, progress, deadline, milestone }: { goal: string; progress: number; deadline?: string; milestone?: string }) {
  const color = progress > 75 ? COLORS.teal : progress > 50 ? COLORS.blue : progress > 30 ? COLORS.orange : COLORS.red
  return (
    <div className="goal-bar-row">
      <div className="goal-bar-meta">
        <span>{goal}</span>
        <div>
          <span>{deadline || milestone}</span>
          <span style={{ color, fontWeight: 700 }}>{progress}%</span>
        </div>
      </div>
      <div className="goal-progress-track">
        <div className="goal-progress-fill" style={{ width: `${progress}%`, background: `linear-gradient(90deg, ${color}88, ${color})` }} />
      </div>
    </div>
  )
}

type AlertType = 'critical' | 'warning' | 'info'

type LiveAlertItem = {
  id: number
  type: AlertType
  sector: string
  msg: string
  time: string
}

function AlertItem({ alert }: { alert: { id: number; type: AlertType; sector: string; msg: string; time: string } }) {
  const colors: Record<AlertType, string> = { critical: COLORS.red, warning: COLORS.orange, info: COLORS.teal }
  const icons: Record<AlertType, string> = { critical: '🚨', warning: '⚠️', info: 'ℹ️' }
  return (
    <div className="alert-item-dark" style={{ borderColor: `${colors[alert.type]}30`, background: `${colors[alert.type]}10` }}>
      <span className="alert-item-icon">{icons[alert.type]}</span>
      <div className="alert-item-body">
        <div className="alert-item-header">
          <span className="alert-item-sector" style={{ color: colors[alert.type] }}>{alert.sector}</span>
          <span className="alert-item-time">{alert.time}</span>
        </div>
        <div className="alert-item-message">{alert.msg}</div>
      </div>
    </div>
  )
}

function MiniSparkline({ data, color }: { data: number[]; color: string }) {
  const max = Math.max(...data)
  const min = Math.min(...data)
  const range = max - min || 1
  const w = 80
  const h = 28
  const points = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w
    const y = h - ((v - min) / range) * h
    return `${x},${y}`
  }).join(' ')
  return (
    <svg width={w} height={h} className="sparkline-svg">
      <polyline points={points} fill="none" stroke={color} strokeWidth={1.5} strokeLinejoin="round" />
      <circle cx={w} cy={h - ((data[data.length - 1] - min) / range) * h} r={2.5} fill={color} />
    </svg>
  )
}

function DistrictGrid({ districts }: { districts: Array<{ name: string; dev: number; alert: boolean }> }) {
  return (
    <div className="district-grid">
      {districts.map((d) => (
        <div
          key={d.name}
          className="district-card"
          style={{ borderColor: d.alert ? `${COLORS.red}60` : COLORS.border, background: d.alert ? `${COLORS.red}12` : COLORS.panel }}
        >
          <div className="district-card-header">
            <span>{d.name}</span>
            {d.alert && <span className="district-alert-dot">⚠️</span>}
          </div>
          <div className="district-card-detail">Dev Index: {d.dev}</div>
          <div className="district-progress-bar">
            <div className="district-progress-fill" style={{ width: `${d.dev}%`, background: d.dev > 80 ? COLORS.teal : d.dev > 70 ? COLORS.blue : COLORS.orange }} />
          </div>
        </div>
      ))}
    </div>
  )
}

function DonutRing({ value, max = 100, color, size = 60, label }: { value: number; max?: number; color: string; size?: number; label: string }) {
  const r = (size - 10) / 2
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - value / max)
  return (
    <div className="donut-ring">
      <svg width={size} height={size}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#1a2540" strokeWidth={6} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={6}
          strokeDasharray={circ}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
        />
        <text x={size / 2} y={size / 2 + 4} textAnchor="middle" fill={color} fontSize={12} fontWeight={700} fontFamily="Rajdhani, sans-serif">
          {value}%
        </text>
      </svg>
      <div className="donut-label">{label}</div>
    </div>
  )
}

function DashboardView({
  kpiCards,
  data,
  districtData,
  projectData,
  liveAlerts,
  onAcknowledgeAlert,
  openAlerts,
  budgetDepartments,
  budgetProjects,
  resourceGapItems,
  priorityItems,
}: {
  kpiCards: KpiCard[]
  data: typeof mockData
  districtData: HeatmapRow[]
  projectData: ProjectRow[]
  liveAlerts: LiveAlertRow[]
  onAcknowledgeAlert: (alertId: number) => void
  openAlerts: number
  budgetDepartments: BudgetRow[]
  budgetProjects: BudgetRow[]
  resourceGapItems: GapRow[]
  priorityItems: PriorityRow[]
}) {
  const [activeTab, setActiveTab] = useState<'overview' | 'economy' | 'welfare' | 'infra' | 'environment' | 'goals'>('overview')

  return (
    <>
      <div className="dashboard-status-row">
        <div className="dashboard-summary-pill">Open Alerts: {openAlerts}</div>
        <div className="dashboard-subnav">
          {[
            { id: 'overview', label: 'Overview', icon: '🧭' },
            { id: 'economy', label: 'Economy', icon: '📈' },
            { id: 'welfare', label: 'Welfare', icon: '❤️' },
            { id: 'infra', label: 'Infrastructure', icon: '🛣️' },
            { id: 'environment', label: 'Environment', icon: '🌿' },
            { id: 'goals', label: 'Goals', icon: '🎯' },
          ].map((tab) => (
            <button
              key={tab.id}
              className={`subtab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id as any)}
            >
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="dashboard-tab-panel">
        {activeTab === 'overview' && (
          <div className="overview-grid">
            <div className="overview-kpi-grid">
              {[
                { icon: '💰', label: 'GSDP (₹ Cr)', value: '₹31.48L Cr', sub: '8.2% growth', color: COLORS.teal, pulse: false },
                { icon: '⚡', label: 'Power Gen. (MW)', value: '21,480 MW', sub: '+12.3% surplus', color: COLORS.accentSoft },
                { icon: '🏥', label: 'Health Visits Today', value: '1.84L', sub: '184 govt hospitals', color: COLORS.blue },
                { icon: '🎓', label: 'School Enrollment', value: '98.2%', sub: 'Dropout: 0.8%', color: COLORS.teal },
                { icon: '📣', label: 'Active Grievances', value: '14,283', sub: '98,421 resolved', color: COLORS.orange, pulse: true },
                { icon: '🌤️', label: 'Air Quality (AQI)', value: '87', sub: 'Moderate · Chennai', color: COLORS.teal },
              ].map((card) => (
                <KPICard key={card.label} {...card} />
              ))}
            </div>

            <div className="panel-dark">
              <SectionTitle icon="📈">Economy Snapshot</SectionTitle>
              <div className="panel-row">
                <div>
                  <div className="panel-title-large">₹27.53T</div>
                  <div className="panel-note">State GDP · 8.2% Growth</div>
                </div>
                <MiniSparkline data={data.economy.trend} color={COLORS.teal} />
              </div>
              {[
                ['Revenue', fmtCr(data.economy.revenue), COLORS.teal],
                ['Expenditure', fmtCr(data.economy.expenditure), COLORS.orange],
                ['Exports', fmtCr(data.economy.exports), COLORS.blue],
                ['FDI Inflows', fmtCr(data.economy.fdi), COLORS.accentSoft],
              ].map(([label, value, color]) => (
                <div key={label} className="panel-stat-row">
                  <span>{label}</span>
                  <span style={{ color }}>{value}</span>
                </div>
              ))}
            </div>

            <div className="panel-dark">
              <SectionTitle icon="❤️">Welfare Vitals</SectionTitle>
              <div className="donut-row">
                {[
                  { value: data.welfare.aadhaarLinked, color: COLORS.teal, label: 'Aadhaar Linked' },
                  { value: data.welfare.schoolEnrollment, color: COLORS.blue, label: 'School Enrolment' },
                  { value: data.governance.budgetUtilization, color: COLORS.accentSoft, label: 'Budget Utilized' },
                  { value: Math.round(data.welfare.healthcareVisits / 2000), color: COLORS.orange, label: 'Health Coverage' },
                ].map((item) => (
                  <DonutRing key={item.label} value={Math.min(100, item.value)} color={item.color} label={item.label} size={68} />
                ))}
              </div>
              {[
                ['PDS Cardholders', `${fmt(data.welfare.pdsCardholders / 100, 2)} Cr`, COLORS.teal],
                ['Women SHG Groups', `${Math.round(data.welfare.womenSHG / 1000)}K`, COLORS.blue],
                ['Farmer Beneficiaries', `${Math.round(data.welfare.farmerBeneficiaries / 100000)}L`, COLORS.orange],
              ].map(([label, value, color]) => (
                <div key={label} className="panel-stat-row">
                  <span>{label}</span>
                  <span style={{ color }}>{value}</span>
                </div>
              ))}
            </div>

            <div className="panel-dark">
              <SectionTitle icon="🏗️">Infrastructure</SectionTitle>
              {[
                { label: 'Roads (Good Condition)', value: data.infrastructure.roadsGoodCondition, max: 100, color: COLORS.teal },
                { label: 'Water Coverage', value: data.infrastructure.waterCoverage, max: 100, color: COLORS.blue },
                { label: 'Power Surplus', value: data.infrastructure.powerSurplus, max: 30, color: COLORS.accentSoft },
                { label: 'Projects On-Time', value: Math.round((1 - data.infrastructure.projectsDelayed / data.infrastructure.projectsOngoing) * 100), max: 100, color: COLORS.orange },
              ].map((item) => (
                <div key={item.label} className="panel-progress-row">
                  <span>{item.label}</span>
                  <span style={{ color: item.color }}>{item.value}%</span>
                  <div className="progress-track"><div className="progress-fill" style={{ width: `${Math.min(100, (item.value / item.max) * 100)}%`, background: item.color }} /></div>
                </div>
              ))}
              <div className="infrastructure-stats-grid">
                {[
                  ['Airports', data.infrastructure.airportsOperational],
                  ['Ports', data.infrastructure.portsActive],
                  ['Metro Lines', data.infrastructure.metroRoutes],
                ].map(([label, value]) => (
                  <div key={label} className="mini-stat-card">
                    <div className="mini-stat-value">{value}</div>
                    <div className="mini-stat-label">{label}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="panel-dark alert-panel">
              <SectionTitle icon="🚨">Live Alerts</SectionTitle>
              {(mockData.alerts as LiveAlertItem[]).map((item) => <AlertItem key={item.id} alert={item} />)}
              <div className="alert-summary-card">
                <div className="alert-summary-label">District Attention Required</div>
                <div className="alert-summary-value">4 Districts</div>
              </div>
            </div>

            <div className="panel-dark district-panel">
              <SectionTitle icon="🗺️">District Development Index</SectionTitle>
              <DistrictGrid districts={mockData.districts} />
            </div>
          </div>
        )}

        {activeTab === 'economy' && (
          <div className="secondary-grid">
            {[
              { title: 'Revenue & Expenditure', icon: '💰', items: [['Total Revenue', fmtCr(data.economy.revenue), COLORS.teal, 'Tax + Non-Tax'], ['Total Expenditure', fmtCr(data.economy.expenditure), COLORS.orange, 'Plan + Non-Plan'], ['Fiscal Deficit', `${data.economy.fiscalDeficit}% GSDP`, COLORS.red, 'FY 2026-27'], ['Capital Expenditure', '₹62,400 Cr', COLORS.blue, '23.9% of total'], ['GST Collection (MTD)', '₹18,420 Cr', COLORS.accentSoft, '11.2% YoY']] },
              { title: 'Industry & Trade', icon: '🏭', items: [['Total Exports', fmtCr(data.economy.exports), COLORS.teal, 'Goods & Services'], ['FDI Inflows (FY)', fmtCr(data.economy.fdi), COLORS.blue, '2nd largest in India'], ['IT/ITES Revenue', '₹1,12,000 Cr', COLORS.accentSoft, '14.3% QoQ'], ['Manufacturing Output', '₹84,200 Cr', COLORS.orange, 'Auto + Textiles'], ['MSMEs Active', '47.2 Lakh', COLORS.teal, '12.4L women-led']] },
              { title: 'Agriculture & Rural', icon: '🌾', items: [['Farmer Beneficiaries', '42 Lakh', COLORS.teal, 'Direct DBT'], ['Kharif Sowing', '82%', COLORS.accentSoft, '2.1L hectares'], ['Agri Credit Disbursed', '₹1,24,000 Cr', COLORS.blue, 'FY 2026-27 target'], ['Crop Insurance Enrolled', '18.4 Lakh', COLORS.orange, 'PM Fasal Bima'], ['Warehousing Capacity', '84.2 LMT', COLORS.teal, '+12% from last yr']] },
            ].map((section) => (
              <div key={section.title} className="panel-dark">
                <SectionTitle icon={section.icon}>{section.title}</SectionTitle>
                {section.items.map(([label, value, color, note]) => (
                  <div key={label} className="panel-stat-row">
                    <div>
                      <div className="panel-stat-label">{label}</div>
                      <div className="panel-note">{note}</div>
                    </div>
                    <div style={{ color, fontWeight: 700 }}>{value}</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'welfare' && (
          <div className="secondary-grid">
            {[
              { title: 'Healthcare', icon: '🏥', items: [['Govt Hospitals', '2,184', COLORS.teal, 'All districts covered'], ['Hospital Beds', '91,440', COLORS.blue, '3.1 per 1000'], ['Doctor Vacancies Filled', '78.4%', COLORS.orange, '642 posts pending'], ['Health Visits Today', '1.84 Lakh', COLORS.teal, 'OPD + IPD'], ['Ayushman Coverage', '2.14 Cr', COLORS.accentSoft, 'Cards issued']] },
              { title: 'Education', icon: '🎓', items: [['Govt School Enrollment', '98.2%', COLORS.teal, 'Primary & Secondary'], ['Dropout Rate', '0.8%', COLORS.accentSoft, 'Lowest in 10 yrs'], ['Mid-Day Meal Beneficiaries', '44.2 Lakh', COLORS.blue, 'Daily'], ['Teachers Recruited FY27', '8,200', COLORS.teal, 'Govt schools'], ['Higher Ed Institutions', '1,842', COLORS.orange, 'Arts, Engg, Med']] },
              { title: 'Women & Child', icon: '👩‍👧', items: [['Women SHG Groups', '6.12 Lakh', COLORS.teal, 'Active groups'], ['Kalaignar Magalir Urimai', '₹1,000/mo', COLORS.accentSoft, '42L disbursed today'], ['Anganwadis Active', '54,392', COLORS.blue, 'Nutrition coverage'], ['Child Beneficiaries', '38.4 Lakh', COLORS.teal, 'ICDS scheme'], ['Women Safety Helpline (181)', '4,218 calls', COLORS.orange, 'Resolved: 94%']] },
              { title: 'Housing & PDS', icon: '🏠', items: [['PDS Cardholders', '2.15 Crore', COLORS.teal, 'Active ration cards'], ['Aadhaar Linked', '98.7%', COLORS.accentSoft, '99.1% target'], ['PMAY Houses Sanctioned', '3.84 Lakh', COLORS.blue, 'Urban + Rural'], ['Houses Completed', '2.41 Lakh', COLORS.teal, '62.7% completion'], ['Piped Water HH Coverage', '84.6%', COLORS.orange, 'Jal Jeevan Mission']] },
            ].map((section) => (
              <div key={section.title} className="panel-dark">
                <SectionTitle icon={section.icon}>{section.title}</SectionTitle>
                {section.items.map(([label, value, color, note]) => (
                  <div key={label} className="panel-stat-row">
                    <div>
                      <div className="panel-stat-label">{label}</div>
                      <div className="panel-note">{note}</div>
                    </div>
                    <div style={{ color, fontWeight: 700 }}>{value}</div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'infra' && (
          <div className="secondary-grid">
            {[
              { title: 'Roads & Transport', icon: '🛣️', items: [['Total Road Network', '1,99,040 km', COLORS.teal], ['Roads in Good Condition', '78.4%', COLORS.accentSoft], ['National Highways', '4,840 km', COLORS.blue], ['Projects Ongoing', '2,847', COLORS.orange], ['Delayed Projects', '341 (12%)', COLORS.red], ['Express Highways', '18 corridors', COLORS.teal]] },
              { title: 'Power & Energy', icon: '⚡', items: [['Total Generation', '21,480 MW', COLORS.teal], ['Solar Capacity', '8,420 MW', COLORS.accentSoft], ['Wind Capacity', '10,152 MW', COLORS.blue], ['Power Surplus', '+12.3%', COLORS.teal], ['Electrification', '100%', COLORS.accentSoft], ['Smart Meters Installed', '42.1 Lakh', COLORS.orange]] },
              { title: 'Urban & Connectivity', icon: '🌐', items: [['Metro Routes Operational', '6', COLORS.teal], ['Metro Stations', '84', COLORS.blue], ['Airports Operational', '8', COLORS.accentSoft], ['Active Ports', '15', COLORS.orange], ['Broadband Villages', '12,842', COLORS.teal], ['5G Towers', '18,400', COLORS.blue]] },
            ].map((section) => (
              <div key={section.title} className="panel-dark">
                <SectionTitle icon={section.icon}>{section.title}</SectionTitle>
                {section.items.map(([label, value, color]) => (
                  <div key={label} className="panel-stat-row">
                    <span>{label}</span>
                    <span style={{ color, fontWeight: 700 }}>{value}</span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}

        {activeTab === 'environment' && (
          <div className="secondary-grid two-column-grid">
            <div className="panel-dark">
              <SectionTitle icon="🌎">Climate & Environment</SectionTitle>
              {[
                ['Forest Cover', `${data.environment.forestCover}%`, COLORS.teal, 'Target: 25% by 2030'],
                ['Air Quality (AQI)', `${data.environment.airQualityAQI}`, COLORS.orange, 'Chennai · Moderate'],
                ['Water Bodies Restored', `${data.environment.waterBodiesRestored}`, COLORS.blue, 'Lakes & tanks'],
                ['Swachh Bharat Score', `${data.environment.swachhtaScore}/100`, COLORS.accentSoft, 'State average'],
                ['Plastic-Free Panchayats', '8,421', COLORS.teal, 'Out of 12,524'],
                ['EV Registrations', `${Math.round(data.environment.evRegistrations / 1000)}K`, COLORS.blue, 'FY 2026-27'],
              ].map(([label, value, color, note]) => (
                <div key={label} className="panel-stat-row">
                  <div>
                    <div className="panel-stat-label">{label}</div>
                    <div className="panel-note">{note}</div>
                  </div>
                  <div style={{ color, fontWeight: 700 }}>{value}</div>
                </div>
              ))}
            </div>
            <div className="panel-dark">
              <SectionTitle icon="♻️">Renewable Energy Progress</SectionTitle>
              <div className="donut-row">
                <DonutRing value={42} color={COLORS.teal} label="Renewable Target" size={84} />
                <DonutRing value={74} color={COLORS.accentSoft} label="Solar Target" size={84} />
                <DonutRing value={88} color={COLORS.blue} label="Wind Target" size={84} />
              </div>
              {[
                ['Solar Installed', '8,420 MW', COLORS.accentSoft, 'Target: 20,000 MW'],
                ['Wind Installed', '10,152 MW', COLORS.blue, '#1 in India'],
                ['Green Hydrogen Projects', '4 active', COLORS.teal, '₹8,400 Cr investment'],
                ['Carbon Credits Earned', '12.4L MT', COLORS.teal, 'FY 2026-27'],
              ].map(([label, value, color, note]) => (
                <div key={label} className="panel-stat-row">
                  <div>
                    <div className="panel-stat-label">{label}</div>
                    <div className="panel-note">{note}</div>
                  </div>
                  <div style={{ color, fontWeight: 700 }}>{value}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'goals' && (
          <div className="secondary-grid two-column-grid">
            <div className="panel-dark">
              <SectionTitle icon="⏳">Short-Term Goals (2026)</SectionTitle>
              <div className="panel-note">Goals to be achieved within this fiscal year and the next 6 months</div>
              {data.shortTermGoals.map((goal) => <GoalBar key={goal.goal} {...goal} />)}
            </div>
            <div className="panel-dark">
              <SectionTitle icon="🚀">Long-Term Vision Goals</SectionTitle>
              <div className="panel-note">Strategic milestones for Tamil Nadu's transformation by 2030–2047</div>
              {data.longTermGoals.map((goal) => <GoalBar key={goal.goal} {...goal} />)}
            </div>
            <div className="panel-dark action-items-panel">
              <SectionTitle icon="📌">Priority Action Items · This Week</SectionTitle>
              <div className="action-grid">
                {[
                  { icon: '🚑', action: 'Emergency health response · Vellore dengue surge', priority: 'CRITICAL', color: COLORS.red },
                  { icon: '💧', action: 'Issue water conservation advisory · Chennai (Poondi 34%)', priority: 'HIGH', color: COLORS.orange },
                  { icon: '🚧', action: 'Deploy NHAI coordination · NH-44 Theni landslide clearance', priority: 'HIGH', color: COLORS.orange },
                  { icon: '⚡', action: 'Peak power demand management plan · 6 PM forecast 19,840 MW', priority: 'MEDIUM', color: COLORS.blue },
                ].map((item) => (
                  <div key={item.action} className="action-card" style={{ borderColor: `${item.color}30`, background: `${item.color}10` }}>
                    <div className="action-card-icon">{item.icon}</div>
                    <div className="action-card-priority" style={{ color: item.color }}>{item.priority}</div>
                    <div className="action-card-text">{item.action}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

function BudgetOverview({ budgetDepartments, budgetProjects }: { budgetDepartments: BudgetRow[]; budgetProjects: BudgetRow[] }) {
  return (
    <>
      <section className="panel">
        <div className="panel-header">
          <h2>Budget Allocation Summary</h2>
          <p>Allocated, spent and remaining amounts by department</p>
        </div>
        <div className="chart-row">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={budgetDepartments} margin={{ top: 16, right: 24, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="department_name" tick={{ fontSize: 12 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="allocated" fill="#2563eb" />
              <Bar dataKey="spent" fill="#0ea5e9" />
              <Bar dataKey="remaining" fill="#14b8a6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Scheme-level Budget Details</h2>
          <p>Project-level allocations and remaining balances</p>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Project</th>
                <th>Fiscal Year</th>
                <th>Allocated</th>
                <th>Spent</th>
                <th>Remaining</th>
              </tr>
            </thead>
            <tbody>
              {budgetProjects.map((item, index) => (
                <tr key={index}>
                  <td>{item.project_code ?? 'Unknown'} - {item.project_name ?? 'Unnamed'}</td>
                  <td>{item.fiscal_year}</td>
                  <td>{item.allocated.toLocaleString()}</td>
                  <td>{item.spent.toLocaleString()}</td>
                  <td>{item.remaining.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}

function GapOverview({ resourceGapItems, priorityItems }: { resourceGapItems: GapRow[]; priorityItems: PriorityRow[] }) {
  return (
    <>
      <section className="panel">
        <div className="panel-header">
          <h2>Department Resource Gap</h2>
          <p>Required vs available manpower and normalized gap score</p>
        </div>
        <div className="chart-row">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={resourceGapItems} margin={{ top: 16, right: 24, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="department_name" tick={{ fontSize: 12 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="required" fill="#f59e0b" />
              <Bar dataKey="available" fill="#10b981" />
              <Bar dataKey="deficit_score" fill="#ef4444" name="Gap %" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Priority Scoring</h2>
          <p>Risk-weighted downstream priorities for active projects</p>
        </div>
        <div className="chart-row">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={priorityItems.slice(0, 8)} layout="vertical" margin={{ top: 8, right: 16, left: 16, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis type="category" dataKey="project_name" width={180} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="priority_score" fill="#2563eb" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </>
  )
}

function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'budget' | 'gap'>('dashboard')
  const [summary, setSummary] = useState<SummaryData>({ kpi_cards: [], project_count: 0, open_alerts: 0 })
  const [heatmap, setHeatmap] = useState<HeatmapRow[]>([])
  const [projects, setProjects] = useState<ProjectRow[]>([])
  const [budgetData, setBudgetData] = useState<BudgetData>({ departments: [], projects: [] })
  const [gapData, setGapData] = useState<GapData>({ by_department: [], by_district: [] })
  const [priorityData, setPriorityData] = useState<PriorityRow[]>([])
  const [liveAlerts, setLiveAlerts] = useState<LiveAlertRow[]>([])

  const handleAcknowledgeAlert = async (alertId: number) => {
    try {
      await fetch(`${API_BASE}/alerts/acknowledge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_id: alertId }),
      })
      setLiveAlerts((prev) =>
        prev.map((alert) =>
          alert.alert_id === alertId
            ? { ...alert, status: 'acknowledged', acknowledged_at: new Date().toISOString() }
            : alert
        )
      )
    } catch (error) {
      console.error('Failed to acknowledge alert:', error)
    }
  }

  useEffect(() => {
    async function loadData() {
      try {
        const [summaryRes, heatmapRes, projectsRes, alertsRes, budgetRes, gapRes, priorityRes, liveAlertsRes] = await Promise.all([
          fetch(`${API_BASE}/summary`),
          fetch(`${API_BASE}/district/heatmap`),
          fetch(`${API_BASE}/projects/top`),
          fetch(`${API_BASE}/alerts/latest`),
          fetch(`${API_BASE}/analytics/budget`),
          fetch(`${API_BASE}/analytics/gap`),
          fetch(`${API_BASE}/analytics/priorities`),
          fetch(`${API_BASE}/alerts/live`),
        ])

        setSummary(summaryRes.ok ? await summaryRes.json() : { kpi_cards: MOCK_KPI, project_count: 0, open_alerts: 0 })
        setHeatmap(heatmapRes.ok ? await heatmapRes.json() : MOCK_DISTRICTS)
        setProjects(projectsRes.ok ? await projectsRes.json() : MOCK_PROJECTS)
        setBudgetData(budgetRes.ok ? await budgetRes.json() : MOCK_BUDGET)
        setGapData(gapRes.ok ? await gapRes.json() : MOCK_GAP)
        setPriorityData(priorityRes.ok ? (await priorityRes.json()).priorities : MOCK_PRIORITIES)
        setLiveAlerts(liveAlertsRes.ok ? await liveAlertsRes.json() : [])
      } catch (error) {
        setSummary({ kpi_cards: MOCK_KPI, project_count: 0, open_alerts: 0 })
        setHeatmap(MOCK_DISTRICTS)
        setProjects(MOCK_PROJECTS)
        setBudgetData(MOCK_BUDGET)
        setGapData(MOCK_GAP)
        setPriorityData(MOCK_PRIORITIES)
      }
    }
    loadData()

    const interval = setInterval(loadData, 12000)
    return () => clearInterval(interval)
  }, [])

  const kpiCards = summary.kpi_cards.length ? summary.kpi_cards : MOCK_KPI
  const districtData = heatmap.length ? heatmap : MOCK_DISTRICTS
  const projectData = projects.length ? projects : MOCK_PROJECTS
  const budgetDepartments = budgetData.departments.length ? budgetData.departments : MOCK_BUDGET.departments
  const budgetProjects = budgetData.projects.length ? budgetData.projects : MOCK_BUDGET.projects
  const resourceGapItems = gapData.by_department.length ? gapData.by_department : MOCK_GAP.by_department
  const priorityItems = priorityData.length ? priorityData : MOCK_PRIORITIES

  return (
    <div className="dashboard-page">
      <header className="hero-header">
        <div className="hero-identity">
          <div className="hero-logo">TN</div>
          <div className="hero-main">
            <p className="eyebrow">Tamil Nadu CM Dashboard</p>
            <h1>Chief Minister's Command Centre</h1>
            <p className="hero-subtitle">Real-time state operations · Fiscal Year 2026–27</p>
            <div className="hero-metrics">
              {[
                { label: 'GSDP', value: '₹31.48L Cr', color: COLORS.teal },
                { label: 'Fiscal Deficit', value: '3.2%', color: COLORS.orange },
                { label: 'Budget Util.', value: '79.4%', color: COLORS.blue },
              ].map((metric) => (
                <div key={metric.label} className="hero-metric">
                  <div className="hero-metric-value" style={{ color: metric.color }}>{metric.value}</div>
                  <div className="hero-metric-label">{metric.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
        <LiveClock />
      </header>

      <div className="ticker-bar">
        <span className="ticker-label">LIVE FEED</span>
        <div className="ticker-marquee">
          🔴 Dengue surge Vellore · ⚡ Power demand 19,840 MW · 📈 IT exports +14.3% QoQ · 🌧️ Poondi reservoir 34% · 🚜 Kharif sowing 82% complete · 🏥 42 govt hospitals upgraded · 🛣️ NH-44 landslide Theni · 📊 GST collection ₹18,420 Cr this month
        </div>
      </div>

      <div className="tab-bar">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={`tab-button ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="tab-panel">
        {activeTab === 'dashboard' ? (
          <DashboardView
            kpiCards={kpiCards}
            data={mockData}
            districtData={districtData}
            projectData={projectData}
            liveAlerts={liveAlerts}
            onAcknowledgeAlert={handleAcknowledgeAlert}
            openAlerts={summary.open_alerts}
            budgetDepartments={budgetDepartments}
            budgetProjects={budgetProjects}
            resourceGapItems={resourceGapItems}
            priorityItems={priorityItems}
          />
        ) : activeTab === 'budget' ? (
          <BudgetOverview budgetDepartments={budgetDepartments} budgetProjects={budgetProjects} />
        ) : (
          <GapOverview resourceGapItems={resourceGapItems} priorityItems={priorityItems} />
        )}
      </div>
    </div>
  )
}

export default App
