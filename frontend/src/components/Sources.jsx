import { useMemo, useState } from 'react';
import { BookOpen, ExternalLink, Globe2, Search, Youtube } from 'lucide-react';
import { Badge, Notice } from './ui';

export function SourceLink({ source, compact = false }) {
  const safe = /^https?:\/\//i.test(source?.url || '');
  if (!source) return null;
  return safe ? <a href={source.url} target="_blank" rel="noopener noreferrer" className={compact ? 'citation-link' : 'source-link'}>{source.title}<ExternalLink size={12} /></a> : <span>{source.title}</span>;
}

export default function Sources({ lesson, sections }) {
  const [filter, setFilter] = useState('all');
  const [usedOnly, setUsedOnly] = useState(false);
  const used = useMemo(() => new Set(sections.flatMap((section) => section.source_ids || [])), [sections]);
  const sources = lesson.sources || [];
  const filtered = sources.filter((source) => (filter === 'all' || source.source_type === filter) && (!usedOnly || used.has(source.id)));
  const icons = { website: Globe2, book: BookOpen, youtube: Youtube };
  return <section className="sources-panel"><div className="section-heading"><div><h2>The research behind your lesson</h2><p>{sources.length} retrieved sources · {used.size} cited in lesson sections</p></div><Badge tone="neutral">Evidence, with context</Badge></div><Notice>Discovery is not verification. Book and video metadata help you discover material; they do not establish relevance or factual support. Website excerpts may be incomplete; inspect original sources before teaching.</Notice>
    {!!lesson.research_warnings?.length && <div className="research-warnings">{lesson.research_warnings.map((warning, index) => <Notice tone="warning" key={index}>{warning}</Notice>)}</div>}
    <div className="source-toolbar"><div className="filter-tabs">{[['all', 'All sources'], ['website', 'Websites'], ['book', 'Books'], ['youtube', 'Videos']].map(([value, label]) => <button key={value} className={filter === value ? 'active' : ''} onClick={() => setFilter(value)}>{label} <span>{sources.filter((s) => value === 'all' || s.source_type === value).length}</span></button>)}</div><label className="checkbox-label"><input type="checkbox" checked={usedOnly} onChange={(e) => setUsedOnly(e.target.checked)} />Cited sources only</label></div>
    {!filtered.length ? <div className="empty-state"><Search size={27} /><h3>No sources in this view</h3><p>{sources.length ? 'Choose a different source filter.' : 'Run research to discover relevant material. Any unavailable providers will be clearly identified.'}</p></div> : <div className="source-grid">{filtered.map((source) => { const Icon = icons[source.source_type] || Globe2; return <article className="source-card" key={source.id}><div className="source-card-heading"><span className={`source-type-icon ${source.source_type}`}><Icon size={21} /></span><div className="source-badges"><Badge tone={used.has(source.id) ? 'green' : 'neutral'}>{used.has(source.id) ? 'Cited in lesson' : 'Retrieved only'}</Badge><Badge>{source.evidence_kind === 'full_text' ? 'Retrieved text' : source.evidence_kind === 'snippet' ? 'Search excerpt' : 'Metadata only'}</Badge></div></div><h3><SourceLink source={source} /></h3><div className="source-author">{source.author || 'Author unavailable'}{source.published_date && ` · ${source.published_date}`}</div><p>{source.description || 'No description supplied by the provider.'}</p>{source.relevance && <div className="source-relevance"><strong>Relevance</strong><p>{source.relevance}</p></div>}{source.excerpt && <details className="evidence-details"><summary>Inspect retrieved evidence</summary><blockquote>{source.excerpt}</blockquote></details>}<div className="source-footnote"><code>{source.id}</code><span>{source.retrieved_at ? `Retrieved ${new Date(source.retrieved_at).toLocaleDateString()}` : source.source_type}</span></div></article>; })}</div>}
  </section>;
}

export function References({ sources, sections }) {
  const used = new Set(sections.flatMap((section) => section.source_ids || []));
  const cited = sources.filter((source) => used.has(source.id));
  const videos = sources.filter((source) => source.source_type === 'youtube');
  return <><section className="lesson-references"><div className="section-kicker">SOURCE NOTES</div><h2>References</h2>{cited.length ? <ol>{cited.map((source) => <li key={source.id}><SourceLink source={source} /><span>{source.author || 'Author unavailable'}{source.published_date ? ` · ${source.published_date}` : ''} · {source.id}</span></li>)}</ol> : <p className="muted">No sources are currently cited in the lesson sections.</p>}</section><section className="lesson-references"><div className="section-kicker">KEEP EXPLORING</div><h2>Supplementary videos</h2><p className="muted">Optional viewing beyond the core lesson. Watching these videos is not included in the 45-minute lesson estimate.</p>{videos.length ? <div className="video-links">{videos.map((source) => <div key={source.id}><Youtube size={20} /><div><SourceLink source={source} /><p>{source.author || 'Channel unavailable'}</p></div></div>)}</div> : <p className="muted">No videos retrieved. Connect YouTube and run research to discover supplementary resources.</p>}</section></>;
}
