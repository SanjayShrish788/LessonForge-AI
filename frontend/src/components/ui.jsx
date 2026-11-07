import { useEffect, useId, useRef } from 'react';
import { AlertCircle, CheckCircle2, LoaderCircle, X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function Badge({ children, tone = 'neutral', dot = false }) {
  return <span className={`badge badge-${tone}`}>{dot && <span className="badge-dot" />}{children}</span>;
}

export function Spinner({ label = 'Loading' }) {
  return <span className="spinner-label"><LoaderCircle size={16} className="spin" />{label}</span>;
}

export function Notice({ children, tone = 'warning', onClose }) {
  const Icon = tone === 'success' ? CheckCircle2 : AlertCircle;
  return <div className={`notice notice-${tone}`} role={tone === 'error' ? 'alert' : 'status'}><Icon size={18} /><div>{children}</div>{onClose && <button className="icon-button" onClick={onClose} aria-label="Dismiss message"><X size={16} /></button>}</div>;
}

export function Modal({ title, subtitle, children, onClose, wide = false }) {
  const dialogRef = useRef(null);
  const titleId = useId();
  const subtitleId = useId();
  useEffect(() => {
    const dialog = dialogRef.current;
    const prior = document.activeElement;
    dialog.showModal();
    return () => { dialog.close(); prior?.focus?.(); };
  }, []);
  return <dialog ref={dialogRef} aria-labelledby={titleId} aria-describedby={subtitle ? subtitleId : undefined} className={`modal ${wide ? 'modal-wide' : ''}`} onCancel={(e) => { e.preventDefault(); onClose(); }} onClick={(e) => { if (e.target === dialogRef.current) onClose(); }}>
    <div className="modal-heading"><div><h2 id={titleId}>{title}</h2>{subtitle && <p id={subtitleId}>{subtitle}</p>}</div><button type="button" className="icon-button" aria-label="Close dialog" onClick={onClose}><X size={20} /></button></div>
    {children}
  </dialog>;
}

export function Markdown({ children }) {
  return <div className="prose"><ReactMarkdown remarkPlugins={[remarkGfm]} components={{ a: ({ node, ...props }) => <a {...props} target="_blank" rel="noopener noreferrer" /> }}>{children || ''}</ReactMarkdown></div>;
}

export function timeAgo(value) {
  if (!value) return 'Not yet';
  const seconds = Math.max(0, (Date.now() - new Date(value).getTime()) / 1000);
  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export function StatusBadge({ status }) {
  const labels = { draft: 'Draft', running: 'In progress', review: 'Ready to review', error: 'Needs attention', complete: 'Complete', completed: 'Complete', pending: 'Pending', failed: 'Failed' };
  const tones = { draft: 'neutral', running: 'blue', review: 'green', error: 'amber', complete: 'green', completed: 'green', failed: 'red' };
  return <Badge tone={tones[status] || 'neutral'} dot>{labels[status] || status || 'Not started'}</Badge>;
}
