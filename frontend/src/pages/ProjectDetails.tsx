import { useEffect, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
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

export default function ProjectDetails() {
  const { id } = useParams();
  const location = useLocation();
  const [project, setProject] = useState<any | null>(null);

  const source = (location.state as { from?: string } | null)?.from ?? 'projects';
  const backPath = source === 'dashboard' ? '/' : '/projects';
  const backLabel = source === 'dashboard' ? '← Back to dashboard' : '← Back to projects';

  useEffect(() => {
    if (!id) return;

    dataService.getProjects().then((all) => {
      const found = all.find(
        (item: any) => item.project_id === id || encodeURIComponent(item.project_id) === id,
      );
      setProject(found || null);
    });
  }, [id]);

  if (!project) {
    return (
      <div className="card">
        <p>Project not found.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="details-header">
        <div>
          <p className="eyebrow">Project overview</p>
          <h1>{project.project_id}</h1>
        </div>
        <Link to={backPath} className="back-link">{backLabel}</Link>
      </div>

      <div className="detail-grid">
        <div className="card">
          <h3>Project details</h3>
          <dl className="meta-list">
            <div><dt>Work</dt><dd>{project.Work || '—'}</dd></div>
            <div><dt>Work category</dt><dd>{project['Work category'] || '—'}</dd></div>
            <div><dt>State</dt><dd>{project.State || '—'}</dd></div>
            <div><dt>Constituency</dt><dd>{project.Constituency || '—'}</dd></div>
            <div><dt>IDA</dt><dd>{project.IDA || '—'}</dd></div>
            <div><dt>MP</dt><dd>{project["Hon'ble Members of Parliament"] || '—'}</dd></div>
          </dl>
        </div>

        <div className="card">
          <h3>Financial summary</h3>
          <dl className="meta-list">
            <div><dt>Recommended amount</dt><dd>{money.format(toNumber(project['Recommended Amount ( ₹ )']))}</dd></div>
            <div><dt>Sanction amount</dt><dd>{money.format(toNumber(project['Sanction Amount ( ₹ )']))}</dd></div>
            <div><dt>Disbursed amount</dt><dd>{money.format(toNumber(project['Amount Disbursed ( ₹ )']) + toNumber(project['Fund Disbursed Amount ( ₹ )']))}</dd></div>
            <div><dt>Recommended date</dt><dd>{project['Recommended date'] || '—'}</dd></div>
            <div><dt>Sanction date</dt><dd>{project['Sanction Date'] || '—'}</dd></div>
            <div><dt>Completion date</dt><dd>{project['Completion Date'] || '—'}</dd></div>
          </dl>
        </div>

        <div className="card">
          <h3>Monitoring flags</h3>
          <dl className="meta-list">
            <div><dt>Work status</dt><dd>{project['Work Status'] || '—'}</dd></div>
            <div><dt>Cost anomaly</dt><dd>{toBooleanFlag(project.cost_anomaly_flag) ? 'Yes' : 'No'}</dd></div>
            <div><dt>Cost anomaly score</dt><dd>{project.cost_anomaly_score || '—'}</dd></div>
            <div><dt>Duplicate match</dt><dd>{toBooleanFlag(project.exact_duplicate_flag) || toBooleanFlag(project.potential_duplicate_flag) ? 'Yes' : 'No'}</dd></div>
            <div><dt>Duplicate reason</dt><dd>{project.duplicate_reason || '—'}</dd></div>
            <div><dt>Similar project ID</dt><dd>{project.similar_project_id || '—'}</dd></div>
          </dl>
        </div>

        <div className="card full-span">
          <h3>Work description</h3>
          <p>{project['Work description'] || 'No description available.'}</p>
          {project.cost_anomaly_reason && (
            <div className="note-box">
              <strong>Cost anomaly reason:</strong> {project.cost_anomaly_reason}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
