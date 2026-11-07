import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, BookOpen, Check, ChevronDown, Circle, Clock3, Download, Edit3, Eye, FileText, History, ListChecks, LoaderCircle, RefreshCw, Save, Search, ShieldCheck, Sparkles, Undo2 } from 'lucide-react';
import { api, downloadExport } from '../services/api';
import { Badge, Markdown, Modal, Notice, Spinner, StatusBadge, timeAgo } from '../components/ui';
import Sources, { References, SourceLink } from '../components/Sources';
import AuditPanel from '../components/AuditPanel';

const steps = [
  { id: 'research', title: 'Research', subtitle: 'Gather relevant sources', icon: Search },
  { id: 'generation', title: 'Create', subtitle: 'Build your lesson', icon: BookOpen },
  { id: 'qc_research', title: 'Factual review', subtitle: 'Inspect the evidence', icon: ShieldCheck },
  { id: 'qc_instructional', title: 'Teaching review', subtitle: 'Review the learning', icon: ListChecks },
];

export default function LessonWorkspace({ lesson, onUpdate, onDirty, onBack }) {
  const [tab, setTab] = useState('lesson');
  const [sections, setSections] = useState(lesson.sections || []);
  const [editId, setEditId] = useState(null);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [versions, setVersions] = useState([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [restoring, setRestoring] = useState(null);
  const [discard, setDiscard] = useState(false);
  const [exporting, setExporting] = useState(false);
  const exportRef = useRef(null);
  const running = lesson.status === 'running';
  const disabled = running || busy || dirty;
  const total = sections.reduce((sum, section) => sum + Number(section.minutes || 0), 0);

  useEffect(() => { if (!dirty) setSections(lesson.sections || []); }, [lesson.sections, dirty]);
  useEffect(() => { onDirty(dirty); return () => onDirty(false); }, [dirty, onDirty]);
  useEffect(() => {
    if (tab !== 'history') return;
    let cancelled = false; setVersionsLoading(true);
    api(`/lessons/${lesson.id}/versions`).then((data) => { if (!cancelled) setVersions(data); }).catch((err) => { if (!cancelled) setError(err.message); }).finally(() => { if (!cancelled) setVersionsLoading(false); });
    return () => { cancelled = true; };
  }, [tab, lesson.id, lesson.version]);
  useEffect(() => {
    if (!success) return;
    const timer = setTimeout(() => setSuccess(''), 6000);
    return () => clearTimeout(timer);
  }, [success]);

  function changeSection(id, field, value) { setSections((current) => current.map((section) => section.id === id ? { ...section, [field]: value } : section)); setDirty(true); setError(''); setSuccess(''); }
  async function save() {
    if (total > 45) { setError('The core lesson must fit within 45 minutes. Reduce section time allocations before saving.'); return; }
    if (sections.some((section) => !section.content.trim() || !section.title.trim() || !Number.isInteger(section.minutes) || section.minutes < 1)) { setError('Every section needs a title, content, and a positive whole-number time allocation.'); return; }
    setBusy(true); setError('');
    try { const next = await api(`/lessons/${lesson.id}`, { method: 'PATCH', body: { expected_version: lesson.version, sections } }); setDirty(false); setSections(next.sections); onUpdate(next); setSuccess('Your edits are saved. Previous content remains in version history.'); }
    catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  async function run(stage) {
    if (disabled) return;
    setBusy(true); setError(''); setSuccess('');
    try { await api(`/lessons/${lesson.id}/run`, { method: 'POST', body: { stage } }); onUpdate(await api(`/lessons/${lesson.id}`)); }
    catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  async function decide(layer, issueId, action) {
    setBusy(true); setError('');
    try { const next = await api(`/lessons/${lesson.id}/recommendations/${layer}/${issueId}`, { method: 'POST', body: { action, expected_version: lesson.version } }); onUpdate(next); setSuccess(action === 'apply' ? 'Recommendation applied. Run the reviews again to assess the updated lesson.' : 'Recommendation rejected. Your lesson is unchanged.'); return true; }
    catch (err) { setError(err.message); return false; } finally { setBusy(false); }
  }
  async function restore() {
    setBusy(true); setError('');
    try { const next = await api(`/lessons/${lesson.id}/restore/${restoring.id}`, { method: 'POST', body: { expected_version: lesson.version } }); onUpdate(next); setRestoring(null); setSuccess('Previous content restored as a new saved version.'); }
    catch (err) { setError(err.message); } finally { setBusy(false); }
  }
  async function exportFile(format, scope) {
    exportRef.current?.removeAttribute('open'); setExporting(true); setError('');
    try { await downloadExport(lesson.id, format, scope); setSuccess('Your export is ready in your downloads.'); }
    catch (err) { setError(err.message); } finally { setExporting(false); }
  }

  return <div className="lesson-workspace page-enter"><button className="back-link" onClick={onBack}><ArrowLeft size={14} />Back to your library</button><div className="lesson-heading"><div><div className="lesson-heading-meta"><StatusBadge status={lesson.status} /><span>Version {lesson.version}</span><span>Saved {timeAgo(lesson.updated_at)}</span></div><h1>{lesson.title}</h1><p>{lesson.learning_objective}</p></div><div className="lesson-heading-actions"><details className="export-menu" ref={exportRef}><summary className={`button secondary ${disabled || exporting || !sections.length ? 'button-disabled' : ''}`} onClick={(e) => { if (disabled || exporting || !sections.length) e.preventDefault(); }}>{exporting ? <LoaderCircle className="spin" size={16} /> : <Download size={16} />}Export<ChevronDown size={14} /></summary><div className="export-options"><span>LESSON</span><button onClick={() => exportFile('pdf', 'lesson')}>PDF document</button><button onClick={() => exportFile('markdown', 'lesson')}>Markdown document</button><button onClick={() => exportFile('json', 'lesson')}>Structured JSON</button><span>AUDIT REPORTS</span><button disabled={!lesson.reports?.research} onClick={() => exportFile('pdf', 'research')}>Factual review · PDF</button><button disabled={!lesson.reports?.instructional} onClick={() => exportFile('pdf', 'instructional')}>Instructional review · PDF</button><span>EVERYTHING TOGETHER</span><button onClick={() => exportFile('zip', 'package')}>Complete lesson package · ZIP</button></div></details><button className="button primary" disabled={!dirty || busy || running} onClick={save}>{busy && dirty ? <Spinner label="Saving…" /> : <><Save size={16} />{dirty ? 'Save changes' : 'All changes saved'}</>}</button></div></div>
    {error && <Notice tone="error" onClose={() => setError('')}>{error}</Notice>}{success && <Notice tone="success" onClose={() => setSuccess('')}>{success}</Notice>}{dirty && <Notice>Unsaved edits are protected locally. Save before running reviews, applying recommendations, or exporting.<button className="inline-button" onClick={() => setDiscard(true)}>Discard local edits</button></Notice>}
    <section className="pipeline" aria-label="Lesson workflow">{steps.map(({ id, title, subtitle, icon: Icon }, index) => { const stage = lesson.stages?.[id]; const stale = id.startsWith('qc_') && lesson.reports?.[id.slice(3)]?.stale; const completed = ['completed', 'complete', 'success'].includes(stage?.status) && !stale; const active = stage?.status === 'running'; const failed = ['failed', 'error'].includes(stage?.status); return <button key={id} className={`pipeline-step ${completed ? 'complete' : ''} ${active ? 'active' : ''} ${failed ? 'failed' : ''}`} disabled={disabled || (id !== 'research' && id !== 'generation' && !sections.length) || (id === 'generation' && !!sections.length)} onClick={() => run(id)} title={id === 'generation' && sections.length ? 'Existing lesson content is preserved' : `${failed ? 'Retry' : 'Run'} ${title.toLowerCase()}`}><span className="pipeline-icon">{active ? <LoaderCircle size={18} className="spin" /> : completed ? <Check size={18} /> : <Icon size={18} />}</span><span><strong>{title}</strong><small>{active ? 'Working on this step…' : stale ? 'Out of date · run again' : failed ? 'Needs attention · retry' : completed ? 'Completed' : subtitle}</small></span><span className="step-number">0{index + 1}</span></button>; })}</section>
    {Object.entries(lesson.stages || {}).filter(([, stage]) => stage.error).map(([key, stage]) => <Notice key={key} tone="error"><strong>{steps.find((step) => step.id === key)?.title || key}: </strong>{stage.error}<button className="inline-button" disabled={disabled} onClick={() => run(key)}>Retry this step</button></Notice>)}
    <div className="studio-toolbar"><div className="studio-tabs" role="tablist" aria-label="Lesson workspace" onKeyDown={(event) => { if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return; const tabs = [...event.currentTarget.querySelectorAll('[role="tab"]')]; const index = tabs.indexOf(document.activeElement); if (index < 0) return; event.preventDefault(); const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length; tabs[next].focus(); tabs[next].click(); }}>{[['lesson', 'Lesson', FileText], ['sources', 'Sources', Search], ['research', 'Factual QC', ShieldCheck], ['instructional', 'Teaching QC', ListChecks], ['history', 'History', History]].map(([key, label, Icon]) => <button key={key} role="tab" aria-selected={tab === key} tabIndex={tab === key ? 0 : -1} className={tab === key ? 'active' : ''} onClick={() => setTab(key)}><Icon size={16} />{label}{key === 'sources' && <span>{lesson.sources?.length || 0}</span>}{['research', 'instructional'].includes(key) && lesson.reports?.[key]?.stale && <i className="stale-dot" title="Review is out of date" />}</button>)}</div><div className={`time-budget ${total > 45 ? 'over-budget' : ''}`}><Clock3 size={15} /><strong>{total}</strong><span>/ 45 min</span></div></div>
    <div role="tabpanel" className="studio-content">
      {tab === 'lesson' && (!sections.length ? <div className="empty-state lesson-empty"><span className="empty-icon"><Sparkles size={30} /></span><div className="eyebrow">YOUR LESSON IS TAKING SHAPE</div><h2>{running ? 'Good research is the first step.' : 'Ready when you are.'}</h2><p>{running ? 'We’re working through the stages above. Completed work is saved along the way, and any unavailable service will be identified.' : 'Run the workflow to discover sources, create a complete lesson, and evaluate it with two independent quality reviews.'}</p><button className="button primary" disabled={disabled} onClick={() => run('all')}>{running ? <Spinner label="Workflow in progress…" /> : <><Sparkles size={16} />{lesson.status === 'error' ? 'Resume workflow' : 'Generate lesson'}</>}</button></div> : <div className="lesson-editor-layout"><aside className="lesson-outline"><div className="outline-heading">IN THIS LESSON</div>{sections.map((section, index) => <a href={`#section-${section.id}`} key={section.id} onClick={(e) => { e.preventDefault(); document.getElementById(`section-${section.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }}><span>{String(index + 1).padStart(2, '0')}</span><div>{section.title}<small>{section.minutes} min</small></div></a>)}<div className="outline-summary"><Clock3 size={17} /><div><strong>{total} minute lesson</strong><span>Includes activities & checks</span></div></div><button className="button secondary small" disabled={disabled} onClick={() => run('qc_both')}><RefreshCw size={14} />Run both reviews</button></aside><div className="lesson-document"><div className="document-heading"><Badge tone="green"><BookOpen size={13} />Instructor lesson</Badge><button className="text-button" disabled={running || busy} onClick={() => setEditId(editId ? null : sections[0].id)}>{editId ? <><Eye size={15} />Preview lesson</> : <><Edit3 size={15} />Edit a section</>}</button></div>{sections.map((section, index) => <section className={`lesson-section ${editId === section.id ? 'editing' : ''}`} id={`section-${section.id}`} key={section.id}><div className="lesson-section-heading"><span className="section-number">{String(index + 1).padStart(2, '0')}</span><div><span className="section-kicker">{section.kind.replaceAll('_', ' ')}</span><h2>{section.title}</h2></div><div className="section-controls"><span><Clock3 size={12} />{section.minutes} min</span><button className="icon-button" aria-label={`${editId === section.id ? 'Preview' : 'Edit'} ${section.title}`} disabled={running || busy} onClick={() => setEditId(editId === section.id ? null : section.id)}>{editId === section.id ? <Eye size={16} /> : <Edit3 size={16} />}</button></div></div>{editId === section.id ? <div className="section-edit-form"><div className="section-edit-meta"><label>Section title<input value={section.title} maxLength={200} onChange={(e) => changeSection(section.id, 'title', e.target.value)} /></label><label>Minutes<input type="number" min="1" max="45" step="1" value={section.minutes} onChange={(e) => changeSection(section.id, 'minutes', Number(e.target.value))} /></label></div><label>Content <span>Markdown supported</span><textarea rows={Math.min(24, Math.max(8, section.content.split('\n').length + 2))} value={section.content} maxLength={20000} onChange={(e) => changeSection(section.id, 'content', e.target.value)} /></label><fieldset className="citation-editor"><legend>Cited sources</legend>{lesson.sources?.length ? lesson.sources.map((source) => <label key={source.id}><input type="checkbox" checked={section.source_ids.includes(source.id)} onChange={(e) => changeSection(section.id, 'source_ids', e.target.checked ? [...section.source_ids, source.id] : section.source_ids.filter((id) => id !== source.id))} /><span>{source.title}</span></label>) : <p className="muted">No research sources available.</p>}</fieldset><button className="button secondary small" onClick={() => setEditId(null)}><Eye size={14} />Preview this section</button></div> : <><Markdown>{section.content}</Markdown>{!!section.source_ids?.length && <div className="section-citations"><span>Sources</span>{section.source_ids.map((id) => <SourceLink compact key={id} source={lesson.sources.find((source) => source.id === id)} />)}</div>}</>}</section>)}<References sources={lesson.sources || []} sections={sections} /></div></div>)}
      {tab === 'sources' && <Sources lesson={lesson} sections={sections} />}
      {['research', 'instructional'].includes(tab) && <AuditPanel lesson={lesson} layer={tab} onRun={run} onDecision={decide} disabled={disabled} />}
      {tab === 'history' && <section className="history-panel"><div className="section-heading"><div><h2>A record of your work</h2><p>Restore previous content without losing your current saved version.</p></div><Badge>Current version {lesson.version}</Badge></div>{versionsLoading ? <Spinner label="Loading version history…" /> : versions.length ? <div className="version-list">{versions.map((version) => <article key={version.id} className="version-card"><span className="version-icon"><History size={20} /></span><div><h3>Version {version.version}<Badge tone={version.version === lesson.version ? 'green' : 'neutral'}>{version.version === lesson.version ? 'Current' : 'Saved snapshot'}</Badge></h3><p>{version.reason}</p><small>{new Date(version.created_at).toLocaleString()} · {version.sections?.length || 0} sections</small></div><button className="button secondary small" disabled={disabled || version.version === lesson.version || !version.sections?.length} onClick={() => setRestoring(version)}><Undo2 size={14} />Review & restore</button></article>)}</div> : <div className="empty-state"><History size={29} /><h3>Your history starts with your first lesson</h3><p>Generated content, saved edits, and applied changes create recoverable versions.</p></div>}</section>}
    </div>
    {restoring && <Modal wide title={`Restore version ${restoring.version}?`} subtitle="Review the saved content. Restoring creates a new version and makes existing QC reports out of date." onClose={() => !busy && setRestoring(null)}><div className="restore-preview">{restoring.sections.map((section) => <section key={section.id}><h3>{section.title} <span className="muted">· {section.minutes} min</span></h3><Markdown>{section.content}</Markdown></section>)}</div><div className="modal-actions"><button className="button secondary" disabled={busy} onClick={() => setRestoring(null)}>Cancel</button><button className="button primary" disabled={disabled} onClick={restore}><Undo2 size={15} />Restore this content</button></div></Modal>}
    {discard && <Modal title="Discard your unsaved edits?" subtitle="The last saved version will remain intact. Your local changes will be removed." onClose={() => setDiscard(false)}><div className="modal-actions"><button className="button secondary" onClick={() => setDiscard(false)}>Keep editing</button><button className="button danger" onClick={() => { setSections(lesson.sections); setDirty(false); setDiscard(false); setEditId(null); }}>Discard changes</button></div></Modal>}
  </div>;
}
