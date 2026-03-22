import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/workflows') {
      return location.pathname === '/workflows' || location.pathname === '/';
    }
    return location.pathname === path;
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: 'var(--primary-blue-900)' }}>
      {/* Header */}
      <header style={{
        backgroundColor: 'var(--primary-blue-800)',
        borderBottom: '1px solid var(--border-color)',
        padding: '1rem 0'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          padding: '0 1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <Link
            to="/workflows"
            style={{
              textDecoration: 'none',
              color: 'var(--text-primary)',
              fontSize: '1.5rem',
              fontWeight: '600'
            }}
          >
            Workflow Application
          </Link>

          <nav style={{ display: 'flex', gap: '2rem' }}>
            <Link
              to="/workflows"
              style={{
                textDecoration: 'none',
                color: isActive('/workflows') ? 'var(--accent-blue-400)' : 'var(--text-secondary)',
                fontWeight: isActive('/workflows') ? '600' : '500',
                padding: '0.5rem 1rem',
                borderRadius: '0.375rem',
                backgroundColor: isActive('/workflows') ? 'var(--primary-blue-700)' : 'transparent'
              }}
            >
              Workflows
            </Link>
            <Link
              to="/executions"
              style={{
                textDecoration: 'none',
                color: isActive('/executions') ? 'var(--accent-blue-400)' : 'var(--text-secondary)',
                fontWeight: isActive('/executions') ? '600' : '500',
                padding: '0.5rem 1rem',
                borderRadius: '0.375rem',
                backgroundColor: isActive('/executions') ? 'var(--primary-blue-700)' : 'transparent'
              }}
            >
              Executions
            </Link>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main style={{
        maxWidth: '1200px',
        margin: '0 auto',
        padding: '2rem 1.5rem'
      }}>
        {children}
      </main>
    </div>
  );
};

export default Layout;