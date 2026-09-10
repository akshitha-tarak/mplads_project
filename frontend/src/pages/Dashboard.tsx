import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import dataService, { toBooleanFlag } from '../services/dataService';

const money = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
});

const toNumber = (value: unknown) => {
  const raw = String(value ?? '').replace(/[^0-9.-]/g, '');
  if (!raw) return 0;
  const num = Number(raw);
  return Number.isFinite(num) ? num : 0;
};

const getRiskLabel = (project: any) => {
  const hasCostAnomaly = toBooleanFlag(project.cost_anomaly_flag);
  const hasExactDuplicate = toBooleanFlag(project.exact_duplicate_flag);
  const hasPotentialDuplicate = toBooleanFlag(project.potential_duplicate_flag);

  if (hasCostAnomaly && (hasExactDuplicate || hasPotentialDuplicate)) return 'High risk';
  if (hasCostAnomaly) return 'Cost anomaly';
  if (hasExactDuplicate) return 'Exact duplicate';
  if (hasPotentialDuplicate) return 'Potential duplicate';
  return 'Normal';
};

const BarChart = ({ title, data }: { title: string; data: { label: string; value: number }[] }) => {
  const max = Math.max(...data.map((item) => item.value), 1);

  return (
    <div className="panel">
      <h3>{title}</h3>
      <div className="chart-list">
        {data.map((item) => (
          <div key={item.label} className="chart-row">
            <div className="chart-labels">
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${(item.value / max) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default function Dashboard() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dataService
      .getProjects()
      .then(setProjects)
      .finally(() => setLoading(false));
  }, []);

  const summary = useMemo(() => {
    const totalProjects = projects.length;
    const completedProjects = projects.filter((project) => String(project['Completion Date'] ?? '').trim() !== '').length;
    const totalSanctioned = projects.reduce((sum, project) => sum + toNumber(project['Sanction Amount ( ₹ )']), 0);
    const totalDisbursed = projects.reduce((sum, project) => sum + toNumber(project['Amount Disbursed ( ₹ )']) + toNumber(project['Fund Disbursed Amount ( ₹ )']), 0);
    const anomalies = projects.filter((project) => toBooleanFlag(project.cost_anomaly_flag)).length;
    const exactDuplicates = projects.filter((project) => toBooleanFlag(project.exact_duplicate_flag)).length;
    const potentialDuplicates = projects.filter((project) => toBooleanFlag(project.potential_duplicate_flag)).length;
    const duplicates = exactDuplicates + potentialDuplicates;
    const highRiskProjects = projects.filter((project) => {
      const hasCostAnomaly = toBooleanFlag(project.cost_anomaly_flag);
      const hasExactDuplicate = toBooleanFlag(project.exact_duplicate_flag);
      const hasPotentialDuplicate = toBooleanFlag(project.potential_duplicate_flag);
      return hasCostAnomaly || hasExactDuplicate || hasPotentialDuplicate;
    }).length;

    const stateCounts = projects.reduce((acc: Record<string, number>, project) => {
      const state = String(project.State ?? '').trim();
      if (!state) return acc;
      acc[state] = (acc[state] ?? 0) + 1;
      return acc;
    }, {});

    const statusCounts = projects.reduce((acc: Record<string, number>, project) => {
      const status = String(project['Work Status'] ?? '').trim() || 'Unspecified';
      acc[status] = (acc[status] ?? 0) + 1;
      return acc;
    }, {});

    const riskOverview = [
      { label: 'Cost anomaly', value: anomalies },
      { label: 'Potential duplicate', value: potentialDuplicates },
      { label: 'Exact duplicate', value: exactDuplicates },
    ];

    const topProjects = [...projects]
      .sort((a, b) => toNumber(b['Sanction Amount ( ₹ )']) - toNumber(a['Sanction Amount ( ₹ )']))
      .slice(0, 6)
      .map((project) => ({
        ...project,
        riskLabel: getRiskLabel(project),
      }));

    return {
      totalProjects,
      completedProjects,
      totalSanctioned,
      totalDisbursed,
      anomalies,
      duplicates,
      exactDuplicates,
      potentialDuplicates,
      highRiskProjects,
      stateCounts,
      statusCounts,
      riskOverview,
      topProjects,
    };
  }, [projects]);

  const stateChart = Object.entries(summary.stateCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([label, value]) => ({ label, value }));

  const statusChart = Object.entries(summary.statusCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([label, value]) => ({ label, value }));

  if (loading) {
    return <div className="card"><p>Loading dashboard...</p></div>;
  }

  return (
    <div>
      <h1>MPLADS dashboard</h1>
      <div className="kpi-grid">
        <div className="card kpi-card">
          <span className="kpi-label">Total projects</span>
          <strong>{summary.totalProjects}</strong>
        </div>
        <div className="card kpi-card">
          <span className="kpi-label">Completed works</span>
          <strong>{summary.completedProjects}</strong>
        </div>
        <div className="card kpi-card">
          <span className="kpi-label">Sanctioned value</span>
          <strong>{money.format(summary.totalSanctioned)}</strong>
        </div>
        <div className="card kpi-card">
          <span className="kpi-label">Disbursed value</span>
          <strong>{money.format(summary.totalDisbursed)}</strong>
        </div>
        <div className="card kpi-card">
          <span className="kpi-label">Cost anomalies</span>
          <strong>{summary.anomalies}</strong>
        </div>
        <div className="card kpi-card">
          <span className="kpi-label">Duplicate cases</span>
          <strong>{summary.duplicates}</strong>
        </div>
        <div className="card kpi-card">
          <span className="kpi-label">High-risk projects</span>
          <strong>{summary.highRiskProjects}</strong>
        </div>
      </div>

      <div className="dashboard-grid">
        <BarChart title="Top states by project count" data={stateChart} />
        <BarChart title="Work status distribution" data={statusChart} />
        <BarChart title="Risk & anomaly overview" data={summary.riskOverview} />
      </div>

      <section className="card table-card">
        <div className="section-header">
          <h3>Largest sanctioned projects</h3>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Project ID</th>
              <th>State</th>
              <th>Work</th>
              <th>Sanction</th>
              <th>Work Status</th>
              <th>Risk / anomaly</th>
            </tr>
          </thead>
          <tbody>
            {summary.topProjects.map((project) => (
              <tr key={project.project_id}>
                <td>
                  <Link to={`/projects/${encodeURIComponent(project.project_id)}`} state={{ from: 'dashboard' }}>{project.project_id}</Link>
                </td>
                <td>{project.State}</td>
                <td>{project.Work}</td>
                <td>{money.format(toNumber(project['Sanction Amount ( ₹ )']))}</td>
                <td>{project['Work Status'] || '—'}</td>
                <td>
                  <span className={`tag ${project.riskLabel === 'High risk' ? 'tag-danger' : project.riskLabel === 'Cost anomaly' || project.riskLabel === 'Exact duplicate' || project.riskLabel === 'Potential duplicate' ? 'tag-warn' : 'tag-ok'}`}>
                    {project.riskLabel}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}
