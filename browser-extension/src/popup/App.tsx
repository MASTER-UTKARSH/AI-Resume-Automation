import React, { useState, useEffect } from 'react';
import { ApplicationStatus } from '../shared/types/events';
import { ApplicationPreview } from '../shared/types/adapter';

export const App: React.FC = () => {
  const [connectionStatus, setConnectionStatus] = useState<'CONNECTED' | 'DISCONNECTED' | 'RECONNECTING'>('DISCONNECTED');
  const [detectedPlatform, setDetectedPlatform] = useState<string>('Detecting...');
  const [isSupported, setIsSupported] = useState<boolean>(false);
  const [currentUrl, setCurrentUrl] = useState<string>('');
  const [agentStatus, setAgentStatus] = useState<ApplicationStatus>('PREPARING');
  const [activeTask, setActiveTask] = useState<{ title: string; company: string; operation: string; progress: number } | null>(null);
  const [recentLogs, setRecentLogs] = useState<Array<{ timestamp: string; message: string; type: 'info' | 'success' | 'warn' | 'error' }>>([
    { timestamp: new Date().toLocaleTimeString(), message: 'Extension initialized in Manifest V3 runtime.', type: 'info' }
  ]);
  const [pendingApproval, setPendingApproval] = useState<ApplicationPreview | null>(null);
  const [isPaused, setIsPaused] = useState<boolean>(false);

  useEffect(() => {
    // 1. Query active tab information
    if (typeof chrome !== 'undefined' && chrome.tabs && chrome.tabs.query) {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs && tabs[0] && tabs[0].url) {
          const url = tabs[0].url;
          setCurrentUrl(url);

          // Request platform detection from content script or background
          chrome.tabs.sendMessage(tabs[0].id!, { type: 'GET_PAGE_STATUS' }, (response) => {
            if (chrome.runtime.lastError) {
              setDetectedPlatform('No Job Form Detected');
              setIsSupported(false);
            } else if (response) {
              setDetectedPlatform(response.platform_name || 'Standard Webpage');
              setIsSupported(Boolean(response.is_supported));
              if (response.pending_approval) {
                setPendingApproval(response.pending_approval);
              }
            }
          });
        }
      });

      // 2. Query Background Service Worker status
      chrome.runtime.sendMessage({ type: 'GET_STATUS' }, (response) => {
        if (response) {
          setConnectionStatus(response.isConnected ? 'CONNECTED' : 'DISCONNECTED');
          if (response.activeTask) setActiveTask(response.activeTask);
          if (response.agentStatus) setAgentStatus(response.agentStatus);
        }
      });

      // 3. Listen for live updates from background service worker
      const messageListener = (msg: any) => {
        if (msg.type === 'WS_STATUS_UPDATE') {
          setConnectionStatus(msg.status);
        } else if (msg.type === 'LOG_EVENT') {
          setRecentLogs(prev => [
            { timestamp: new Date().toLocaleTimeString(), message: msg.message, type: msg.level || 'info' },
            ...prev.slice(0, 9)
          ]);
        } else if (msg.type === 'APPLICATION_PREVIEW_READY') {
          setPendingApproval(msg.preview);
          setAgentStatus('AWAITING_APPROVAL');
        }
      };

      chrome.runtime.onMessage.addListener(messageListener);
      return () => chrome.runtime.onMessage.removeListener(messageListener);
    }
  }, []);

  const handleToggleConnect = () => {
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      if (connectionStatus === 'CONNECTED') {
        chrome.runtime.sendMessage({ type: 'DISCONNECT_WS' });
        setConnectionStatus('DISCONNECTED');
      } else {
        setConnectionStatus('RECONNECTING');
        chrome.runtime.sendMessage({ type: 'CONNECT_WS' });
      }
    }
  };

  const handleTogglePause = () => {
    const next = !isPaused;
    setIsPaused(next);
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      chrome.runtime.sendMessage({ type: next ? 'PAUSE_AUTOMATION' : 'RESUME_AUTOMATION' });
    }
  };

  const handleCancelTask = () => {
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      chrome.runtime.sendMessage({ type: 'CANCEL_CURRENT_TASK' });
      setActiveTask(null);
      setPendingApproval(null);
      setAgentStatus('PREPARING');
    }
  };

  const handleApproveSubmission = () => {
    if (!pendingApproval) return;
    if (typeof chrome !== 'undefined' && chrome.runtime) {
      chrome.runtime.sendMessage({
        type: 'APPROVE_SUBMISSION',
        payload: {
          application_id: pendingApproval.application_id,
          approval_token: `appr_${Date.now()}_confirmed`
        }
      });
      setPendingApproval(null);
      setAgentStatus('SUBMITTING');
    }
  };

  return (
    <div style={{ padding: '16px', boxSizing: 'border-box', fontSize: '13px', lineHeight: '1.4' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #222226', paddingBottom: '12px', marginBottom: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: '#ff8400' }}></div>
          <span style={{ fontWeight: 700, letterSpacing: '-0.3px', color: '#f1f0ea' }}>Clyde AI Browser Agent</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{
            fontSize: '10px',
            fontFamily: 'monospace',
            padding: '2px 6px',
            borderRadius: '4px',
            backgroundColor: 'rgba(255, 132, 0, 0.12)',
            color: '#ff8400',
            border: '1px solid rgba(255, 132, 0, 0.25)'
          }}>
            {agentStatus}
          </span>
          <span style={{
            fontSize: '10px',
            fontFamily: 'monospace',
            padding: '2px 6px',
            borderRadius: '4px',
            backgroundColor: connectionStatus === 'CONNECTED' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            color: connectionStatus === 'CONNECTED' ? '#10b981' : '#ef4444',
            border: `1px solid ${connectionStatus === 'CONNECTED' ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)'}`
          }}>
            {connectionStatus}
          </span>
        </div>
      </div>

      {/* Target Site Card */}
      <div style={{ backgroundColor: '#141418', border: '1px solid #26262b', borderRadius: '8px', padding: '10px 12px', marginBottom: '12px' }}>
        <div style={{ fontSize: '11px', color: '#909099', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Current Website</div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ fontWeight: 600, color: '#f1f0ea' }}>{detectedPlatform}</div>
          <span style={{
            fontSize: '10px',
            padding: '2px 6px',
            borderRadius: '4px',
            backgroundColor: isSupported ? 'rgba(16, 185, 129, 0.12)' : 'rgba(144, 144, 153, 0.12)',
            color: isSupported ? '#10b981' : '#909099'
          }}>
            {isSupported ? 'Supported ATS' : 'Standard Webpage'}
          </span>
        </div>
        <div style={{ fontSize: '11px', color: '#71717a', marginTop: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {currentUrl || 'No tab active'}
        </div>
      </div>

      {/* Pending Approval Drawer / Alert */}
      {pendingApproval && (
        <div style={{ backgroundColor: 'rgba(255, 132, 0, 0.08)', border: '1px solid rgba(255, 132, 0, 0.3)', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ff8400', fontWeight: 600, fontSize: '12px', marginBottom: '6px' }}>
            <span>⚠️ Explicit Approval Required</span>
          </div>
          <div style={{ fontSize: '12px', color: '#f1f0ea', marginBottom: '4px' }}>
            <strong>{pendingApproval.job_title}</strong> at <strong>{pendingApproval.company_name}</strong>
          </div>
          <div style={{ fontSize: '11px', color: '#a1a1aa', marginBottom: '8px' }}>
            Resume: <code>{pendingApproval.resume_attached}</code> ({pendingApproval.fields_populated.length} fields filled)
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={handleApproveSubmission}
              style={{
                flex: 1,
                padding: '6px 10px',
                borderRadius: '6px',
                backgroundColor: '#10b981',
                color: '#000',
                border: 'none',
                fontWeight: 700,
                cursor: 'pointer',
                fontSize: '11px'
              }}
            >
              Confirm & Submit
            </button>
            <button
              onClick={handleCancelTask}
              style={{
                padding: '6px 10px',
                borderRadius: '6px',
                backgroundColor: 'transparent',
                color: '#ef4444',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                cursor: 'pointer',
                fontSize: '11px'
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Current Task Status */}
      {activeTask && (
        <div style={{ backgroundColor: '#141418', border: '1px solid #26262b', borderRadius: '8px', padding: '10px 12px', marginBottom: '12px' }}>
          <div style={{ fontSize: '11px', color: '#909099', marginBottom: '4px' }}>Active Task</div>
          <div style={{ fontWeight: 600, color: '#f1f0ea' }}>{activeTask.title}</div>
          <div style={{ fontSize: '11px', color: '#ff8400', marginTop: '2px' }}>{activeTask.operation}</div>
          {/* Progress bar */}
          <div style={{ width: '100%', height: '4px', backgroundColor: '#26262b', borderRadius: '2px', marginTop: '8px', overflow: 'hidden' }}>
            <div style={{ width: `${activeTask.progress}%`, height: '100%', backgroundColor: '#ff8400', transition: 'width 0.3s ease' }}></div>
          </div>
        </div>
      )}

      {/* Recent Activity Log */}
      <div style={{ backgroundColor: '#141418', border: '1px solid #26262b', borderRadius: '8px', padding: '10px 12px', marginBottom: '14px' }}>
        <div style={{ fontSize: '11px', color: '#909099', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Agent Activity</div>
        <div style={{ maxHeight: '110px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {recentLogs.map((log, idx) => (
            <div key={idx} style={{ fontSize: '11px', display: 'flex', gap: '6px' }}>
              <span style={{ color: '#71717a', fontFamily: 'monospace', flexShrink: 0 }}>{log.timestamp}</span>
              <span style={{
                color: log.type === 'error' ? '#ef4444' : log.type === 'warn' ? '#ff8400' : log.type === 'success' ? '#10b981' : '#d4d4d8'
              }}>
                {log.message}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Action Controls */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
        <button
          onClick={handleToggleConnect}
          style={{
            padding: '7px 10px',
            borderRadius: '6px',
            backgroundColor: connectionStatus === 'CONNECTED' ? '#222226' : '#ff8400',
            color: connectionStatus === 'CONNECTED' ? '#f1f0ea' : '#000',
            border: 'none',
            fontWeight: 600,
            cursor: 'pointer',
            fontSize: '11px'
          }}
        >
          {connectionStatus === 'CONNECTED' ? 'Disconnect Backend' : 'Connect Backend'}
        </button>

        <button
          onClick={handleTogglePause}
          style={{
            padding: '7px 10px',
            borderRadius: '6px',
            backgroundColor: '#1f1f23',
            color: '#f1f0ea',
            border: '1px solid #2e2e34',
            fontWeight: 600,
            cursor: 'pointer',
            fontSize: '11px'
          }}
        >
          {isPaused ? '▶ Resume Agent' : '⏸ Pause Agent'}
        </button>
      </div>
    </div>
  );
};

export default App;
