import { Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Projects from './pages/Projects';
import ProjectDetails from './pages/ProjectDetails';

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h2>MPLADS Dashboard</h2>
        <nav>
          <ul>
            <li><Link to="/">Dashboard</Link></li>
            <li><Link to="/projects">Projects</Link></li>
          </ul>
        </nav>
      </aside>
      <div className="main">
        <header className="topbar">MPLADS Risk Monitoring</header>
        <main className="content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/projects" element={<Projects />} />
            <Route path="/projects/:id" element={<ProjectDetails />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
