import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Upload } from './pages/Upload';
import { DocumentsList } from './pages/DocumentsList';
import { DocumentReview } from './pages/DocumentReview';
import { OwnershipChain } from './pages/OwnershipChain';
import { MapCrossCheck } from './pages/MapCrossCheck';
import { AuditLog } from './pages/AuditLog';
import { AdminRules } from './pages/AdminRules';
import { EcosystemIntegration } from './pages/EcosystemIntegration';
import { Login } from './pages/Login';

export const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <div className="min-h-screen flex flex-col bg-slate-50">
              <Navbar />
              <div className="flex-1 flex">
                <Sidebar />
                <main className="flex-1 overflow-y-auto">
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/upload" element={<Upload />} />
                    <Route path="/documents" element={<DocumentsList />} />
                    <Route path="/documents/:id" element={<DocumentReview />} />
                    <Route path="/review" element={<DocumentsList />} />
                    <Route path="/ownership" element={<OwnershipChain />} />
                    <Route path="/map" element={<MapCrossCheck />} />
                    <Route path="/audit" element={<AuditLog />} />
                    <Route path="/admin" element={<AdminRules />} />
                    <Route path="/ecosystem" element={<EcosystemIntegration />} />
                  </Routes>
                </main>
              </div>
            </div>
          }
        />
      </Routes>
    </Router>
  );
};

export default App;
