import { useCallback, useEffect, useRef, useState } from 'react';
import { BookOpen, ChevronRight, CircleHelp, LayoutDashboard, Menu, Moon, Plus, Settings2, ShieldCheck, Sun, X } from 'lucide-react';
import { api } from './services/api';
import { Badge, Modal, Notice, Spinner } from './components/ui';
import CreateLesson from './components/CreateLesson';
import Dashboard from './pages/Dashboard';
import LessonWorkspace from './pages/LessonWorkspace';

function selectedId() { return window.location.hash.startsWith('#lesson/') ? decodeURIComponent(window.location.hash.slice(8)) : null; }

export default function App() {
  const [theme, setTheme] = useState(() => {
    try { return localStorage.getItem('lessonforge-theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'); } catch { return 'light'; }
  });
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try { localStorage.setItem('lessonforge-theme', theme); } catch { /* Storage is optional. */ }
  }, [theme]);
  const [lessons, setLessons] = useState([]);
  const [health, setHealth] = useState(null);
  const [currentId, setCurrentId] = useState(selectedId);
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingLesson, setLoadingLesson] = useState(false);
  const [lessonRetry, setLessonRetry] = useState(0);
  const [error, setError] = useState('');
  const [newLesson, setNewLesson] = useState(false);
  const [settings, setSettings] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  const menuRef = useRef(null);
  const [narrow, setNarrow] = useState(() => window.matchMedia('(max-width: 800px)').matches);
  const [dirty, setDirty] = useState(false);
  const [navigation, setNavigation] = useState(null);

  const refresh = useCallback(async () => {
    const results = await Promise.allSettled([api('/lessons'), api('/health')]);
    if (results[0].status === 'fulfilled') { setLessons(results[0].value); setError(''); }
    else setError(results[0].reason.message);
    if (results[1].status === 'fulfilled') setHealth(results[1].value);
    setLoading(false);
  }, []);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => {
    const query = window.matchMedia('(max-width: 800px)');
    const changed = (event) => { setNarrow(event.matches); if (!event.matches) setMobileNav(false); };
    query.addEventListener('change', changed);
    return () => query.removeEventListener('change', changed);
  }, []);
  useEffect(() => {
    if (!mobileNav || !narrow) return;
    document.querySelector('#workspace-navigation button')?.focus();
    const onKey = (event) => {
      if (event.key === 'Escape') { setMobileNav(false); menuRef.current?.focus(); }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [mobileNav, narrow]);
  useEffect(() => {
    const onHash = () => setCurrentId(selectedId());
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);
  useEffect(() => {
    if (!currentId) { setLesson(null); return; }
    const controller = new AbortController();
    setLoadingLesson(true); setError('');
    api(`/lessons/${encodeURIComponent(currentId)}`, { signal: controller.signal }).then(setLesson).catch((err) => { if (err.name !== 'AbortError') setError(err.message); }).finally(() => { if (!controller.signal.aborted) setLoadingLesson(false); });
    return () => controller.abort();
  }, [currentId, lessonRetry]);
  const updateLesson = useCallback((next) => { setLesson(next); setLessons((current) => { const found = current.some((item) => item.id === next.id); return found ? current.map((item) => item.id === next.id ? next : item) : [next, ...current]; }); }, []);
  useEffect(() => {
    if (!currentId || lesson?.id !== currentId || lesson.status !== 'running') return;
    let cancelled = false;
    let timer;
    async function poll() {
      try { const next = await api(`/lessons/${encodeURIComponent(currentId)}`); if (!cancelled) { updateLesson(next); if (next.status === 'running') timer = setTimeout(poll, 1500); } }
      catch (err) { if (!cancelled) { setError(err.message); timer = setTimeout(poll, 4000); } }
    }
    timer = setTimeout(poll, 1500);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [currentId, lesson?.id, lesson?.status, updateLesson]);
  useEffect(() => {
    const unload = (e) => { if (dirty) { e.preventDefault(); e.returnValue = ''; } };
    window.addEventListener('beforeunload', unload);
    return () => window.removeEventListener('beforeunload', unload);
  }, [dirty]);

  function navigate(id) {
    if (dirty) { setNavigation({ id }); return; }
    window.location.hash = id ? `lesson/${encodeURIComponent(id)}` : '';
    setCurrentId(id); setMobileNav(false);
    if (!id) refresh();
  }
  async function created(record, generate) {
    setNewLesson(false); updateLesson(record); navigate(record.id);
    if (generate) {
      try { await api(`/lessons/${record.id}/run`, { method: 'POST', body: { stage: 'all' } }); updateLesson(await api(`/lessons/${record.id}`)); }
      catch (err) { setError(err.message); }
    }
  }
  const configurationIncomplete = health && ['llm', 'web', 'youtube'].some((key) => !health.providers?.[key]?.configured);
  return <div className="app-shell">
    {mobileNav && <button className="nav-scrim" aria-label="Close navigation" onClick={() => { setMobileNav(false); menuRef.current?.focus(); }} />}
    <aside id="workspace-navigation" inert={narrow && !mobileNav} aria-hidden={narrow && !mobileNav} className={`sidebar ${mobileNav ? 'sidebar-open' : ''}`}><button className="brand" onClick={() => navigate(null)}><span className="brand-symbol"><BookOpen size={23} /></span><span>LessonForge<span className="brand-ai">AI</span></span></button><div className="workspace-label"><span className="workspace-avatar">IW</span><div><strong>Instructor workspace</strong><small>Personal library</small></div><ChevronRight size={14} /></div><div className="nav-section-label">WORKSPACE</div><nav><button className={`nav-item ${!currentId ? 'active' : ''}`} onClick={() => navigate(null)}><LayoutDashboard size={18} />Overview</button><button className="nav-item" onClick={() => setNewLesson(true)} disabled={dirty}><Plus size={18} />New lesson</button></nav><div className="nav-section-label recent-label">RECENT LESSONS<span>{lessons.length}</span></div><div className="sidebar-lessons">{lessons.slice(0, 6).map((item) => <button key={item.id} title={item.title} className={`nav-item lesson-nav ${currentId === item.id ? 'active' : ''}`} onClick={() => navigate(item.id)}><BookOpen size={16} /><span>{item.title}</span>{item.status === 'running' && <span className="running-dot" />}</button>)}{!lessons.length && <p className="sidebar-empty">A space for your next<br />lightbulb moment.</p>}</div><div className="sidebar-bottom"><div className="integrity-card"><ShieldCheck size={20} /><strong>Good teaching starts<br />with good sources.</strong><p>Two independent reviews.<br />One thoughtful lesson.</p></div><button className="nav-item" onClick={() => setSettings(true)}><Settings2 size={18} />Connections{configurationIncomplete && <span className="config-dot" />}</button><div className="sidebar-footer">CRAFTED FOR EDUCATORS <span>v1.0</span></div></div></aside>
    <div className="main-shell"><header className="topbar"><button ref={menuRef} className="icon-button mobile-menu" aria-label="Open navigation" aria-controls="workspace-navigation" aria-expanded={mobileNav} onClick={() => setMobileNav(true)}><Menu size={21} /></button><div className="breadcrumb"><span>Workspace</span><ChevronRight size={13} /><strong>{currentId ? 'Lesson studio' : 'Overview'}</strong></div><div className="topbar-right"><button className="theme-toggle" type="button" aria-label={theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'} title={theme === 'light' ? 'Switch to dark theme' : 'Switch to light theme'} onClick={() => setTheme((current) => current === 'light' ? 'dark' : 'light')}>{theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}<span>{theme === 'light' ? 'Dark' : 'Light'}</span></button><span className={`connection-state ${health ? '' : 'offline'}`}><span />{health ? 'Local workspace' : 'Connecting…'}</span><button className="icon-button" aria-label="View connections and help" onClick={() => setSettings(true)}><CircleHelp size={19} /></button><span className="user-avatar">IN</span></div></header>
      <main>{error && <div className="global-notice"><Notice tone="error" onClose={() => setError('')}>{error}<button className="inline-button" onClick={() => { refresh(); if (currentId) setLessonRetry((value) => value + 1); }}>Retry connection</button></Notice></div>}{configurationIncomplete && <div className="setup-notice"><span><Settings2 size={15} />Connect your AI and research providers to generate lessons.</span><button onClick={() => setSettings(true)}>View setup<ChevronRight size={14} /></button></div>}
        {currentId ? loadingLesson ? <div className="page-loading"><Spinner label="Opening your lesson…" /></div> : lesson?.id !== currentId ? <div className="empty-state"><h2>Could not open this lesson</h2><p>Check the backend connection, then try again.</p><button className="button secondary" onClick={() => setLessonRetry((value) => value + 1)}>Try opening again</button></div> : <LessonWorkspace key={currentId} lesson={lesson} onUpdate={updateLesson} onDirty={setDirty} onBack={() => navigate(null)} /> : <Dashboard lessons={lessons} onNew={() => setNewLesson(true)} onOpen={navigate} loading={loading} />}
      </main><footer className="main-footer"><span>LessonForge AI</span><span>Research thoughtfully. Teach confidently.</span></footer>
    </div>
    {newLesson && <CreateLesson onClose={() => setNewLesson(false)} onCreated={created} />}
    {settings && <Modal title="Your provider connections" subtitle="Credentials stay on the backend. Your browser never receives API keys." onClose={() => setSettings(false)}><div className="connection-list">{[['llm', 'Lesson generation & review', health?.providers?.llm?.provider || 'Gemini or OpenAI'], ['web', 'Website research', 'Tavily Search'], ['books', 'Book discovery', 'Google Books'], ['youtube', 'Educational videos', 'YouTube Data API v3']].map(([key, title, provider]) => <div className="connection-row" key={key}><div><strong>{title}</strong><span>{provider}{key === 'llm' && health?.providers?.llm?.model ? ` · ${health.providers.llm.model}` : ''}</span></div><Badge tone={health?.providers?.[key]?.configured ? 'green' : 'amber'}>{health?.providers?.[key]?.configured ? 'Configured' : 'Needs setup'}</Badge></div>)}</div><div className="setup-instructions"><h3>Connect locally</h3><ol><li>Copy <code>backend/.env.example</code> to <code>backend/.env</code>.</li><li>Add a Gemini or OpenAI API key, a Tavily key, and a YouTube Data API key. Google Books can work without a key when quota allows.</li><li>Restart the backend, then refresh connections.</li></ol><p>Configured means a credential is present; availability is checked when a request runs. Research limitations appear alongside the returned sources.</p></div><div className="modal-actions"><button className="button secondary" onClick={refresh}>Refresh connections</button><button className="button primary" onClick={() => setSettings(false)}>Done</button></div></Modal>}
    {navigation && <Modal title="You have unsaved edits" subtitle="Save from the lesson editor before leaving, or discard this local draft." onClose={() => setNavigation(null)}><div className="modal-actions"><button className="button secondary" onClick={() => setNavigation(null)}>Keep editing</button><button className="button danger" onClick={() => { const target = navigation.id; setNavigation(null); setDirty(false); window.location.hash = target ? `lesson/${encodeURIComponent(target)}` : ''; setCurrentId(target); setMobileNav(false); }}>Discard and leave</button></div></Modal>}
  </div>;
}
