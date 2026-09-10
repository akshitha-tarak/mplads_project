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

export default function Projects() {
  const [projects, setProjects] = useState<any[]>([]);
  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [anomalyFilter, setAnomalyFilter] = useState('all');

  useEffect(() => {
    dataService.getProjects().then(setProjects);
  }, []);

  const states = useMemo(
    () => Array.from(new Set(projects.map((project) => String(project.State ?? '').trim()).filter(Boolean))).sort(),
    [projects],
  );

  const statuses = useMemo(
    () => Array.from(new Set(projects.map((project) => String(project['Work Status'] ?? '').trim()).filter(Boolean))).sort(),
    [projects],
  );

  const filteredProjects = useMemo(() => {
    const query = search.trim().toLowerCase();

    return [...projects].filter((project) => {
      const matchesQuery =
        !query ||
        project.project_id.toLowerCase().includes(query) ||
        String(project.State ?? '').toLowerCase().includes(query) ||
        String(project['Work description'] ?? '').toLowerCase().includes(query) ||
        String(project.Work ?? '').toLowerCase().includes(query);

      const matchesState = stateFilter === 'all' || project.State === stateFilter;
      const matchesStatus = statusFilter === 'all' || project['Work Status'] === statusFilter;
      const matchesAnomaly =
        anomalyFilter === 'all' ||
        (anomalyFilter === 'anomaly' && toBooleanFlag(project.cost_anomaly_flag)) ||
        (anomalyFilter === 'duplicate' && (toBooleanFlag(project.exact_duplicate_flag) || toBooleanFlag(project.potential_duplicate_flag))) ||
        (anomalyFilter === 'normal' && !toBooleanFlag(project.cost_anomaly_flag) && !toBooleanFlag(project.exact_duplicate_flag) && !toBooleanFlag(project.potential_duplicate_flag));

      return matchesQuery && matchesState && matchesStatus && matchesAnomaly;
    });
  }, [projects, search, stateFilter, statusFilter, anomalyFilter]);

  return (
    <div>
      <h1>Projects</h1>

      <div className="filters">
        <input
          className="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search project, state, or work description"
        />

        <select className="search" value={stateFilter} onChange={(event) => setStateFilter(event.target.value)}>
          <option value="all">All states</option>
          {states.map((state) => (
            <option key={state} value={state}>{state}</option>
          ))}
        </select>

        <select className="search" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
          <option value="all">All statuses</option>
          {statuses.map((status) => (
            <option key={status} value={status}>{status}</option>
          ))}
        </select>

        <select className="search" value={anomalyFilter} onChange={(event) => setAnomalyFilter(event.target.value)}>
          <option value="all">All project flags</option>
          <option value="anomaly">Cost anomaly</option>
          <option value="duplicate">Duplicate check</option>
          <option value="normal">Normal</option>
        </select>
      </div>

      <div className="card table-card">
        <table className="table">
          <thead>
            <tr>
              <th>Project ID</th>
              <th>State</th>
              <th>Constituency</th>
              <th>Work category</th>
              <th>Status</th>
              <th>Sanction</th>
              <th>Disbursed</th>
              <th>Flags</th>
            </tr>
          </thead>
          <tbody>
            {filteredProjects.slice(0, 200).map((project) => (
              <tr key={project.project_id}>
                <td>
                  <Link to={`/projects/${encodeURIComponent(project.project_id)}`} state={{ from: 'projects' }}>{project.project_id}</Link>
                </td>
                <td>{project.State}</td>
                <td>{project.Constituency}</td>
                <td>{project['Work category']}</td>
                <td>{project['Work Status'] || '—'}</td>
                <td>{money.format(toNumber(project['Sanction Amount ( ₹ )']))}</td>
                <td>{money.format(toNumber(project['Amount Disbursed ( ₹ )']) + toNumber(project['Fund Disbursed Amount ( ₹ )']))}</td>
                <td>
                  <div className="tag-stack">
                    {toBooleanFlag(project.cost_anomaly_flag) && <span className="tag tag-danger">Anomaly</span>}
                    {(toBooleanFlag(project.exact_duplicate_flag) || toBooleanFlag(project.potential_duplicate_flag)) && <span className="tag tag-warn">Duplicate</span>}
                    {!toBooleanFlag(project.cost_anomaly_flag) && !toBooleanFlag(project.exact_duplicate_flag) && !toBooleanFlag(project.potential_duplicate_flag) && <span className="tag tag-ok">Normal</span>}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="muted">Showing {filteredProjects.length} project(s)</p>
    </div>
  );
}
