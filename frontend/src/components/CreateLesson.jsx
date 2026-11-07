import { useState } from 'react';
import { ArrowRight, BookOpen, Sparkles } from 'lucide-react';
import { api } from '../services/api';
import { Modal, Notice, Spinner } from './ui';

const examples = [
  { title: 'HTTP Requests and Responses', learning_objective: 'Explain GET and POST methods and distinguish between 2xx, 4xx, and 5xx response status categories.' },
  { title: 'Object-Oriented Programming: Inheritance and Polymorphism in Java', learning_objective: 'Explain inheritance and polymorphism in Java, demonstrate their differences through practical code examples, and identify situations where each concept is useful.' },
];

export default function CreateLesson({ onClose, onCreated }) {
  const [title, setTitle] = useState('');
  const [objective, setObjective] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event) {
    event.preventDefault();
    const generate = event.nativeEvent.submitter?.value !== 'draft';
    setBusy(true); setError('');
    try {
      const lesson = await api('/lessons', { method: 'POST', body: { title: title.trim(), learning_objective: objective.trim() } });
      onCreated(lesson, generate);
    } catch (err) { setError(err.message); setBusy(false); }
  }
  return <Modal title="Start with a learning goal" subtitle="A focused lesson begins with what your learners should be able to do." onClose={() => !busy && onClose()}>
    <form onSubmit={submit} className="create-form">
      <label htmlFor="lesson-title">Lesson title <span className="required">*</span></label>
      <input id="lesson-title" autoFocus required minLength={3} maxLength={180} placeholder="e.g. HTTP Requests and Responses" value={title} onChange={(e) => setTitle(e.target.value)} disabled={busy} />
      <label htmlFor="learning-objective">Learning objective <span className="required">*</span></label>
      <textarea id="learning-objective" required minLength={15} maxLength={3000} rows={4} placeholder="By the end of this lesson, learners will be able to…" value={objective} onChange={(e) => setObjective(e.target.value)} disabled={busy} />
      <p className="field-hint">Be specific. Include the concepts, skills, or outcomes you want to teach.</p>
      <div className="example-inputs"><span>Try an assignment input</span><div>{examples.map((example, i) => <button key={example.title} type="button" className="chip-button" disabled={busy} onClick={() => { setTitle(example.title); setObjective(example.learning_objective); }}>{i === 0 ? 'HTTP fundamentals' : 'Java OOP'}<ArrowRight size={13} /></button>)}</div></div>
      <div className="creation-promise"><BookOpen size={20} /><div><strong>One complete lesson. Up to 45 minutes.</strong><p>Research across websites, books, and videos, followed by separate factual and instructional reviews.</p></div></div>
      {error && <Notice tone="error">{error}</Notice>}
      <div className="modal-actions"><button type="submit" value="draft" className="button secondary" disabled={busy}>Save draft</button><button type="submit" value="generate" className="button primary" disabled={busy}>{busy ? <Spinner label="Creating…" /> : <><Sparkles size={16} />Generate lesson</>}</button></div>
    </form>
  </Modal>;
}
