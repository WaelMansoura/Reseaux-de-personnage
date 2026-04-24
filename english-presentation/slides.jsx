/* Slide components for "Character Networks from Asimov's Foundation"
   Academic / minimal aesthetic, 1920x1080. */

const TYPE_SCALE = {
  display: 96,
  title: 64,
  subtitle: 44,
  bodyLg: 38,
  body: 32,
  small: 26,
  micro: 22
};

const SPACING = {
  paddingTop: 100,
  paddingBottom: 90,
  paddingX: 120,
  titleGap: 48,
  itemGap: 28,
  sectionGap: 64
};

const COLORS = {
  bg: '#fafafa', // crisp white
  bgAlt: '#f0f2f5', // light cool gray
  ink: '#1e293b', // slate text
  inkSoft: '#475569', // secondary text
  rule: '#cbd5e1', // border gray
  ruleSoft: '#e2e8f0', // soft border
  accent: '#2563eb', // crisp tech blue
  friendly: '#10b981',
  hostile: '#ef4444',
  neutral: '#94a3b8'
};

const FONT_SERIF = '"Source Serif 4", "Source Serif Pro", Georgia, serif';
const FONT_SANS = '"Inter Tight", "Helvetica Neue", Helvetica, Arial, sans-serif';
const FONT_MONO = '"JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace';

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "speciality": "M1 ILSEN",
  "specialityLong": "M1 ILSEN",
  "university": "Avignon Université",
  "year": "2026",
  "showFooter": true
} /*EDITMODE-END*/;

const TweaksCtx = React.createContext(null);
function useT() {return React.useContext(TweaksCtx) || {
    speciality: 'M1 ILSEN', specialityLong: 'M1 ILSEN',
    university: 'Avignon Université', year: '2026', showFooter: true };}

/* =====================================================================
   Shared chrome — slide frame, header label, footer page
   ===================================================================== */

function Frame({ label, page, total, children, bg, style }) {
  return (
    <div style={{
      position: 'absolute', inset: 0,
      background: bg || COLORS.bg,
      color: COLORS.ink,
      fontFamily: FONT_SANS,
      padding: `${SPACING.paddingTop}px ${SPACING.paddingX}px ${SPACING.paddingBottom}px`,
      display: 'flex', flexDirection: 'column',
      ...(style || {})
    }}>
      <Header label={label} page={page} total={total} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        {children}
      </div>
      <Footer />
    </div>);

}

function Header({ label, page, total }) {
  return (
    <div style={{
      position: 'absolute', top: 48, left: SPACING.paddingX, right: SPACING.paddingX,
      display: 'flex', justifyContent: 'space-between', alignItems: 'baseline',
      fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro,
      color: COLORS.inkSoft, letterSpacing: '0.08em', textTransform: 'uppercase'
    }}>
      <span>{label || 'Réseaux de Personnages'}</span>
      <span>{page != null ? `${String(page).padStart(2, '0')} / ${String(total).padStart(2, '0')}` : ''}</span>
    </div>);

}

function Footer() {
  if (!useT().showFooter) return null;
  return (
    <div style={{
      position: 'absolute', bottom: 44, left: SPACING.paddingX, right: SPACING.paddingX,
      display: 'flex', justifyContent: 'space-between',
      fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro,
      color: COLORS.inkSoft, letterSpacing: '0.04em'
    }}>
      <span>Lotfi Abdallah · Wael Mansoura</span>
      <span>{useT().university} · {useT().speciality} · {useT().year}</span>
    </div>);

}

function SlideTitle({ children, style }) {
  return (
    <h1 style={{
      fontFamily: FONT_SERIF, fontWeight: 400,
      fontSize: TYPE_SCALE.title, lineHeight: 1.05,
      letterSpacing: '-0.015em', margin: 0,
      color: COLORS.ink, ...(style || {}), height: "50px"
    }}>{children}</h1>);

}

function Eyebrow({ children, color }) {
  return (
    <div style={{
      fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro,
      letterSpacing: '0.14em', textTransform: 'uppercase',
      color: color || COLORS.accent, marginBottom: 18
    }}>{children}</div>);

}

function Rule({ color, thickness, my }) {
  return <div style={{
    height: thickness || 1, background: color || COLORS.rule,
    margin: `${my || 0}px 0`, alignSelf: 'stretch'
  }} />;
}

/* =====================================================================
   Slide 1 — Title
   ===================================================================== */

function SlideTitleCover({ page, total }) {
  return (
    <div style={{
      position: 'absolute', inset: 0, background: COLORS.bg,
      color: COLORS.ink, fontFamily: FONT_SANS,
      padding: `${SPACING.paddingTop}px ${SPACING.paddingX}px ${SPACING.paddingBottom}px`,
      display: 'flex', flexDirection: 'column'
    }}>
      <Header label="Réseaux de Personnages · Final Defense" page={page} total={total} />

      <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1.15fr 1fr', gap: 80, alignItems: 'center' }}>
        <div>
          <Eyebrow>NLP · Networks of Fiction</Eyebrow>
          <h1 style={{
            fontFamily: FONT_SERIF, fontWeight: 400,
            fontSize: TYPE_SCALE.display, lineHeight: 1.0,
            letterSpacing: '-0.025em', margin: 0
          }}>
            Character&nbsp;Networks<br />
            <span style={{ fontStyle: 'italic', color: COLORS.accent }}>from&nbsp;Asimov's</span><br />
            Foundation Cycle.
          </h1>

          <div style={{ marginTop: 64, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.small, color: COLORS.inkSoft, lineHeight: 1.7 }}>
            <div>Lotfi&nbsp;Abdallah &nbsp;·&nbsp; Wael&nbsp;Mansoura</div>
            <div>Supervised by Pr.&nbsp;Juan-Manuel&nbsp;Torres-Moreno</div>
            <div style={{ marginTop: 18, color: COLORS.ink }}>{useT().university} &nbsp;·&nbsp; {useT().specialityLong}</div>
          </div>
        </div>

        <NetworkHero />
      </div>
    </div>);

}

function NetworkHero() {
  // A small, controlled network diagram — abstract, monochrome with one accent
  const nodes = [
  { id: 'A', x: 200, y: 120, r: 36, label: 'Seldon' },
  { id: 'B', x: 460, y: 80, r: 22, label: 'Demerzel' },
  { id: 'C', x: 540, y: 280, r: 28, label: 'Dors' },
  { id: 'D', x: 280, y: 340, r: 24, label: 'Hummin' },
  { id: 'E', x: 100, y: 280, r: 18, label: 'Yugo' },
  { id: 'F', x: 380, y: 460, r: 20, label: 'Raych' },
  { id: 'G', x: 600, y: 460, r: 16, label: 'Rashelle' },
  { id: 'H', x: 80, y: 470, r: 14, label: 'Davan' }];

  const edges = [
  ['A', 'B', 'n'], ['A', 'C', 'f'], ['A', 'D', 'f'], ['A', 'E', 'f'],
  ['A', 'F', 'f'], ['B', 'C', 'n'], ['C', 'D', 'n'], ['C', 'F', 'f'],
  ['D', 'E', 'n'], ['F', 'G', 'h'], ['E', 'H', 'n'], ['A', 'G', 'h']];

  const pos = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const colorOf = (t) => t === 'f' ? COLORS.friendly : t === 'h' ? COLORS.hostile : COLORS.neutral;

  return (
    <div style={{ width: '100%', aspectRatio: '1 / 1', position: 'relative' }}>
      <svg viewBox="0 0 700 600" style={{ width: '100%', height: '100%' }}>
        {edges.map(([a, b, t], i) =>
        <line key={i} x1={pos[a].x} y1={pos[a].y} x2={pos[b].x} y2={pos[b].y}
        stroke={colorOf(t)} strokeWidth={t === 'n' ? 1.4 : 2.4} strokeOpacity={0.85} />
        )}
        {nodes.map((n) =>
        <g key={n.id}>
            <circle cx={n.x} cy={n.y} r={n.r} fill={COLORS.bg} stroke={COLORS.ink} strokeWidth={1.6} />
            <text x={n.x} y={n.y + n.r + 22} textAnchor="middle"
          fontFamily={FONT_MONO} fontSize={16} fill={COLORS.ink}>{n.label}</text>
          </g>
        )}
      </svg>
    </div>);

}

/* =====================================================================
   Slide 2 — Project Goal
   ===================================================================== */

function SlideGoal({ page, total }) {
  return (
    <Frame label="01 · Context" page={page} total={total}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: SPACING.sectionGap, alignItems: 'center', flex: 1 }}>
        <div>
          <Eyebrow>Project Goal</Eyebrow>
          <SlideTitle>
            Turn a 700-page novel<br />
            into a <em style={{ color: COLORS.accent }}>graph of who&nbsp;knows&nbsp;whom</em>.
          </SlideTitle>
          <Rule my={40} />
          <p style={{
            fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.bodyLg,
            lineHeight: 1.4, color: COLORS.inkSoft, margin: 0,
            textWrap: 'pretty'
          }}>
            Given the raw text of an Asimov novel, build the underlying social network
            of its characters &mdash; who appears together, how often, and with what affect.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 24 }}>
          <Stat n="2" label="novels analysed" sub="Foundation · The Caves of Steel" />
          <Stat n="34" label="chapters" sub="processed independently" />
          <Stat n="≈ 250k" label="tokens of French prose" />
          <Stat n="5" label="pipeline stages" sub="NER → aliases → co-occurrence → relations → graph" />
        </div>
      </div>
    </Frame>);

}

function Stat({ n, label, sub }) {
  return (
    <div style={{
      borderTop: `1px solid ${COLORS.rule}`,
      padding: '18px 0',
      display: 'grid', gridTemplateColumns: '180px 1fr', alignItems: 'baseline', gap: 24
    }}>
      <div style={{ fontFamily: FONT_SERIF, fontSize: 64, lineHeight: 1, color: COLORS.ink }}>{n}</div>
      <div>
        <div style={{ fontFamily: FONT_SANS, fontSize: TYPE_SCALE.body, color: COLORS.ink }}>{label}</div>
        {sub && <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.inkSoft, marginTop: 6 }}>{sub}</div>}
      </div>
    </div>);

}

/* =====================================================================
   Slide 3 — Pipeline Overview
   ===================================================================== */

function SlidePipeline({ page, total }) {
  const stages = [
  { n: '01', name: 'NER', desc: 'Detect named entities — persons & locations' },
  { n: '02', name: 'Aliases', desc: 'Merge surface forms into canonical characters' },
  { n: '03', name: 'Co-occurrence', desc: 'Pairs that appear inside the same window' },
  { n: '04', name: 'Relations', desc: 'Classify each edge: friendly · hostile · neutral' },
  { n: '05', name: 'Graph', desc: 'NetworkX → GraphML → interactive HTML' }];

  return (
    <Frame label="02 · Architecture" page={page} total={total}>
      <Eyebrow>Pipeline Overview</Eyebrow>
      <SlideTitle>Five stages, one direction.</SlideTitle>

      <div style={{ marginTop: 80, display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 24 }}>
        {stages.map((s, i) =>
        <div key={s.n} style={{ position: 'relative' }}>
            <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.1em' }}>{s.n}</div>
            <div style={{ marginTop: 12, paddingTop: 18, borderTop: `2px solid ${COLORS.ink}` }}>
              <div style={{ fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.subtitle, lineHeight: 1.05 }}>{s.name}</div>
              <div style={{ marginTop: 18, fontFamily: FONT_SANS, fontSize: TYPE_SCALE.small, color: COLORS.inkSoft, lineHeight: 1.4 }}>{s.desc}</div>
            </div>
            {i < stages.length - 1 &&
          <div style={{
            position: 'absolute', top: 12, right: -16,
            fontFamily: FONT_MONO, fontSize: TYPE_SCALE.body, color: COLORS.rule
          }}>→</div>
          }
          </div>
        )}
      </div>

      <div style={{ marginTop: 100, padding: '32px 36px', background: COLORS.bgAlt, border: `1px solid ${COLORS.rule}` }}>
        <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.1em' }}>INPUT &nbsp;→&nbsp; OUTPUT</div>
        <div style={{ marginTop: 18, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.bodyLg, color: COLORS.ink, lineHeight: 1.4 }}>
          One chapter of French prose &nbsp; ⟶ &nbsp; one weighted, signed graph of its characters.
        </div>
      </div>
    </Frame>);

}

/* =====================================================================
   Slide 4 — Stage 1 NER intro
   ===================================================================== */

function SlideNER({ page, total }) {
  return (
    <Frame label="03 · Stage 1 of 5" page={page} total={total}>
      <Eyebrow>Stage 1 — Named Entity Recognition</Eyebrow>
      <SlideTitle>Find every person <em>before</em> we can connect them.</SlideTitle>
      <Rule my={48} />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 80, flex: 1 }}>
        <div>
          <h3 style={{ fontFamily: FONT_SANS, fontWeight: 600, fontSize: TYPE_SCALE.body, color: COLORS.ink, margin: 0, letterSpacing: '0.04em', textTransform: 'uppercase' }}>The hard parts</h3>
          <ul style={{ marginTop: 24, padding: 0, listStyle: 'none', fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.bodyLg, lineHeight: 1.45, color: COLORS.inkSoft }}>
            <li style={{ display: 'flex', gap: 18, marginBottom: SPACING.itemGap }}>
              <span style={{ color: COLORS.accent, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.body, flexShrink: 0 }}>—</span>
              <span><b style={{ color: COLORS.ink }}>Sci-fi proper nouns</b> rarely appear in standard NER training data.</span>
            </li>
            <li style={{ display: 'flex', gap: 18, marginBottom: SPACING.itemGap }}>
              <span style={{ color: COLORS.accent, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.body, flexShrink: 0 }}>—</span>
              <span><b style={{ color: COLORS.ink }}>French + invented words</b> confuse mono-lingual or English-leaning models.</span>
            </li>
            <li style={{ display: 'flex', gap: 18, marginBottom: SPACING.itemGap }}>
              <span style={{ color: COLORS.accent, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.body, flexShrink: 0 }}>—</span>
              <span><b style={{ color: COLORS.ink }}>Capitalised non-names</b> at sentence starts produce false positives.</span>
            </li>
          </ul>
        </div>

        <div style={{ background: COLORS.bgAlt, padding: 36, border: `1px solid ${COLORS.rule}`, alignSelf: 'start' }}>
          <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.1em' }}>SAMPLE SENTENCE</div>
          <div style={{ marginTop: 22, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.bodyLg, lineHeight: 1.55, color: COLORS.ink, fontStyle: 'italic' }}>
            “<Tag c="per">Hari Seldon</Tag> regarda <Tag c="per">Dors&nbsp;Venabili</Tag> traverser le secteur de <Tag c="loc">Mycogène</Tag>, où <Tag c="per">Hummin</Tag> les attendait.”
          </div>
          <div style={{ marginTop: 28, display: 'flex', gap: 24, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.inkSoft }}>
            <Legend swatch={COLORS.accent} label="PER · person" />
            <Legend swatch={COLORS.inkSoft} label="LOC · location" />
          </div>
        </div>
      </div>
    </Frame>);

}

function Tag({ c, children }) {
  const bg = c === 'per' ? 'rgba(122,59,46,0.12)' : 'rgba(61,58,53,0.12)';
  const bd = c === 'per' ? COLORS.accent : COLORS.inkSoft;
  return (
    <span style={{
      background: bg, borderBottom: `2px solid ${bd}`,
      padding: '0 4px', borderRadius: 2
    }}>{children}</span>);

}

function Legend({ swatch, label }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
      <span style={{ width: 14, height: 14, background: swatch, display: 'inline-block' }} />
      {label}
    </span>);

}

/* =====================================================================
   Slide 5 — Take 1: AI Ensemble
   ===================================================================== */

function SlideAIEnsemble({ page, total }) {
  const models = [
    { name: 'spaCy', detail: 'fr_core_news_lg' },
    { name: 'Stanza', detail: 'stanza fr' },
    { name: 'Flair', detail: 'fr-ner BiLSTM-CRF' }
  ];

  return (
    <Frame label="04 · Stage 1 of 5: Take 1" page={page} total={total}>
      <Eyebrow>NER · Take 1</Eyebrow>
      <SlideTitle>First attempt: Heavy AI Ensemble.</SlideTitle>
      
      <div style={{ marginTop: 64, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 32 }}>
        {models.map((m) => (
          <div key={m.name} style={{ border: `1px solid ${COLORS.rule}`, padding: 36, background: COLORS.bg }}>
            <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.1em' }}>{m.detail}</div>
            <div style={{ marginTop: 14, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.title, lineHeight: 1 }}>{m.name}</div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 56, padding: '36px', background: COLORS.bgAlt, border: `1px solid ${COLORS.rule}` }}>
        <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.1em' }}>MAJORITY VOTE (≥ 2)</div>
        <div style={{ marginTop: 18, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.bodyLg, color: COLORS.ink, lineHeight: 1.4 }}>
          Each sentence goes through all three models. An entity is kept only if at least two models independently detect it.
        </div>
      </div>
    </Frame>
  );
}

/* =====================================================================
   Slide 6 — The Reality
   ===================================================================== */

function SlideAIFailures({ page, total }) {
  const issues = [
    { title: "Science Fiction Domain Gap", desc: "Models trained on Wikipedia completely missed Asimov's invented proper nouns and unearthly locations." },
    { title: "The Capitalization Trap", desc: "French sentences starting with capitalized adjectives or verbs (e.g. “Soudain”, “Étouffant”) were routinely tagged as people." },
    { title: "Unbearably Slow Inference", desc: "Loading and chunking text safely for three heavy models (especially Flair's BiLSTM) bottlenecked our pipeline." }
  ];

  return (
    <Frame label="05 · Stage 1 of 5: The Reality" page={page} total={total}>
      <Eyebrow>NER · The Reality</Eyebrow>
      <SlideTitle>Why the AI ensemble failed us.</SlideTitle>

      <div style={{ marginTop: 64, display: 'grid', gridTemplateColumns: 'minmax(0, 1fr)', gap: 32, flex: 1 }}>
        {issues.map((issue, i) => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: '60px 1fr', gap: 32, borderTop: `1px solid ${COLORS.rule}`, paddingTop: 32 }}>
            <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.body, color: COLORS.accent }}>{String(i + 1).padStart(2, '0')}</div>
            <div>
              <div style={{ fontFamily: FONT_SANS, fontWeight: 600, fontSize: TYPE_SCALE.bodyLg, color: COLORS.ink }}>{issue.title}</div>
              <div style={{ marginTop: 12, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.body, color: COLORS.inkSoft, lineHeight: 1.5 }}>{issue.desc}</div>
            </div>
          </div>
        ))}
      </div>
    </Frame>
  );
}

/* =====================================================================
   Slide 7 — Rule-Based Solution
   ===================================================================== */

function SlideManualNER({ page, total }) {
  return (
    <Frame label="06 · Stage 1 of 5: Take 2" page={page} total={total}>
      <Eyebrow>NER · Take 2</Eyebrow>
      <SlideTitle>The solution: <em style={{ color: COLORS.accent, fontStyle: 'normal' }}>Zero-AI</em>, purely rule-based extraction.</SlideTitle>

      <div style={{ marginTop: 64, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 32, flex: 1 }}>
        <RuleBox 
          n="01" 
          title="Gazetteer Lookup" 
          code="build_gazetteer()" 
          desc="Strict matching against a hand-curated Asimov dictionary. Prioritizes longest matches." 
        />
        <RuleBox 
          n="02" 
          title="Capitalization Heuristics" 
          code="_capitalization_scan()" 
          desc="Groups consecutive mid-sentence capitalized words. Filters out words that appear uncapitalized elsewhere." 
        />
        <RuleBox 
          n="03" 
          title="Regex Patterns" 
          code="_title_regex_scan()" 
          desc="Catches titles (“Docteur X”, “M. Y”) and Asimov robot conventions (“R. Daneel”)." 
        />
      </div>
    </Frame>
  );
}

function RuleBox({ n, title, code, desc }) {
  return (
    <div style={{ background: COLORS.bgAlt, border: `1px solid ${COLORS.rule}`, padding: 36, display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.1em' }}>STRATEGY {n}</div>
      </div>
      <div style={{ marginTop: 24, paddingBottom: 24, borderBottom: `1px solid ${COLORS.ruleSoft}` }}>
        <div style={{ fontFamily: FONT_SANS, fontWeight: 600, fontSize: TYPE_SCALE.body, color: COLORS.ink, lineHeight: 1.2 }}>{title}</div>
        <div style={{ marginTop: 12, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.inkSoft }}>{code}</div>
      </div>
      <div style={{ marginTop: 24, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.body, color: COLORS.inkSoft, lineHeight: 1.5 }}>
        {desc}
      </div>
    </div>
  );
}

/* =====================================================================
   Slide 7 — Rule-Based Solution
   ===================================================================== */

// function SlideManualNER({ page, total }) {
//   return (
//     <Frame label="06 · Stage 1 of 5: Take 2" page={page} total={total}>
//       <Eyebrow>NER · Take 2</Eyebrow>
//       <SlideTitle>The solution: <em style={{ color: COLORS.accent, fontStyle: 'normal' }}>Zero-AI</em>, purely rule-based extraction.</SlideTitle>

//       <div style={{ marginTop: 64, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 32, flex: 1 }}>
//         <RuleBox 
//           n="01" 
//           title="Gazetteer Lookup" 
//           code="build_gazetteer()" 
//           desc="Strict matching against a hand-curated Asimov dictionary. Prioritizes longest matches." 
//         />
//         <RuleBox 
//           n="02" 
//           title="Capitalization Heuristics" 
//           code="_capitalization_scan()" 
//           desc="Groups consecutive mid-sentence capitalized words. Filters out words that appear uncapitalized elsewhere." 
//         />
//         <RuleBox 
//           n="03" 
//           title="Regex Patterns" 
//           code="_title_regex_scan()" 
//           desc="Catches titles (“Docteur X”, “M. Y”) and Asimov robot conventions (“R. Daneel”)." 
//         />
//       </div>
//     </Frame>
//   );
// }

// function RuleBox({ n, title, code, desc }) {
//   return (
//     <div style={{ background: COLORS.bgAlt, border: `1px solid ${COLORS.rule}`, padding: 36, display: 'flex', flexDirection: 'column' }}>
//       <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
//         <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.1em' }}>STRATEGY {n}</div>
//       </div>
//       <div style={{ marginTop: 24, paddingBottom: 24, borderBottom: `1px solid ${COLORS.ruleSoft}` }}>
//         <div style={{ fontFamily: FONT_SANS, fontWeight: 600, fontSize: TYPE_SCALE.body, color: COLORS.ink, lineHeight: 1.2 }}>{title}</div>
//         <div style={{ marginTop: 12, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.inkSoft }}>{code}</div>
//       </div>
//       <div style={{ marginTop: 24, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.body, color: COLORS.inkSoft, lineHeight: 1.5 }}>
//         {desc}
//       </div>
//     </div>
//   );
// }

/* =====================================================================
   Slide 7 — Stage 2 Aliases
   ===================================================================== */

function SlideAliases({ page, total }) {
  const surfaces = [
  { name: 'Hari Seldon', count: 50, group: 0 },
  { name: 'Seldon', count: 30, group: 0 },
  { name: 'Hari', count: 20, group: 0 },
  { name: 'Bayta Darell', count: 12, group: 1 },
  { name: 'Bayta', count: 8, group: 1 },
  { name: 'Arcadia Darell', count: 10, group: 2 },
  { name: 'Arkady', count: 7, group: 2 },
  { name: 'Darell', count: 6, group: null }, // ambiguous
  { name: 'Harinder', count: 3, group: 3 }];

  return (
    <Frame label="08 · Stage 2 of 5" page={page} total={total}>
      <Eyebrow>Stage 2 — Alias Resolution</Eyebrow>
      <SlideTitle>“Hari”, “Seldon”, “Hari Seldon” are <em>one</em> person.</SlideTitle>

      <div style={{ marginTop: 64, display: 'grid', gridTemplateColumns: '1fr 1.1fr', gap: SPACING.sectionGap, flex: 1, alignItems: 'start' }}>
        <div style={{ background: COLORS.bgAlt, border: `1px solid ${COLORS.rule}`, padding: 32 }}>
          <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.1em' }}>RAW NER OUTPUT</div>
          <div style={{ marginTop: 18 }}>
            {surfaces.map((s) =>
            <div key={s.name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '10px 0', borderBottom: `1px solid ${COLORS.ruleSoft}`, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.body }}>
                <span>{s.name}</span>
                <span style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.small, color: COLORS.inkSoft }}>×{s.count}</span>
              </div>
            )}
          </div>
        </div>

        <div>
          <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.1em' }}>AFTER ALIAS RESOLUTION</div>
          <div style={{ marginTop: 18 }}>
            <Cluster canonical="Hari Seldon" total={100} aliases={['Hari Seldon', 'Seldon', 'Hari']} />
            <Cluster canonical="Bayta Darell" total={20} aliases={['Bayta Darell', 'Bayta', '·Darell (ambiguous → most-frequent)']} />
            <Cluster canonical="Arcadia Darell" total={17} aliases={['Arcadia Darell', 'Arkady']} />
            <Cluster canonical="Harinder" total={3} aliases={['Harinder']} note="≠ Hari (fuzzy guard)" />
          </div>
        </div>
      </div>
    </Frame>);

}

function Cluster({ canonical, total, aliases, note }) {
  return (
    <div style={{ padding: '18px 0', borderBottom: `1px solid ${COLORS.rule}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <div style={{ fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.bodyLg, color: COLORS.ink }}>{canonical}</div>
        <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.small, color: COLORS.accent }}>×{total}</div>
      </div>
      <div style={{ marginTop: 8, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.inkSoft, lineHeight: 1.5 }}>
        ← {aliases.join(' · ')}
      </div>
      {note && <div style={{ marginTop: 6, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.hostile }}>⚠ {note}</div>}
    </div>);

}

/* =====================================================================
   Slide 8 — Union-Find with ambiguity
   ===================================================================== */

function SlideUnionFind({ page, total }) {
  return (
    <Frame label="08 · Stage 2 of 5" page={page} total={total}>
      <Eyebrow>Alias Resolution · Algorithm</Eyebrow>
      <SlideTitle>Union-Find with an ambiguity guard.</SlideTitle>

      <div style={{ marginTop: 56, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: SPACING.sectionGap, flex: 1 }}>
        <div>
          <h3 style={{ fontFamily: FONT_SANS, fontSize: TYPE_SCALE.small, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: COLORS.ink, margin: 0 }}>Three merge rules</h3>

          <RuleRow n="01"
          title="Subset rule"
          desc="Two multi-word names merge only if one keyword set is a subset of the other. ‘Bayta Darell’ and ‘Arcadia Darell’ stay separate." />
          
          <RuleRow n="02"
          title="Single → multi"
          desc="A single token merges into the multi-word name that contains it as a meaningful keyword." />
          
          <RuleRow n="03"
          title="Fuzzy fallback"
          desc="If no overlap, fall back to fuzzy ratio ≥ 88 — but only when at least one name is multi-word. ‘Hari’ ≠ ‘Harinder’." />
          
        </div>

        <div style={{ background: COLORS.bgAlt, border: `1px solid ${COLORS.rule}`, padding: 36 }}>
          <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.1em' }}>AMBIGUITY GUARD</div>
          <div style={{ marginTop: 22, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.body, color: COLORS.ink, lineHeight: 1.5 }}>
            ‘Darell’ on its own could be Bayta, Toran or Arcadia. We pre-assign the bare token to the <i>most-frequent</i> multi-word match — never split it across families.
          </div>

          <div style={{ marginTop: 32, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.small, color: COLORS.inkSoft, lineHeight: 1.7 }}>
            <div style={{ color: COLORS.ink }}>Darell&nbsp;&nbsp;×6</div>
            <div>↳ Bayta Darell &nbsp;×12 &nbsp;<span style={{ color: COLORS.friendly }}>← winner</span></div>
            <div>↳ Arcadia Darell &nbsp;×10</div>
            <div>↳ Toran Darell &nbsp;×4</div>
          </div>

          <Rule my={32} color={COLORS.rule} />

          <div style={{ fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.small, color: COLORS.inkSoft, lineHeight: 1.5 }}>
            Path-compressed union-find on ~150 surface forms per chapter; the gazetteer step then forces author-supplied groupings on top.
          </div>
        </div>
      </div>
    </Frame>);

}

function RuleRow({ n, title, desc }) {
  return (
    <div style={{ marginTop: 24, display: 'grid', gridTemplateColumns: '60px 1fr', gap: 24, padding: '16px 0', borderTop: `1px solid ${COLORS.rule}` }}>
      <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.small, color: COLORS.accent, letterSpacing: '0.08em' }}>{n}</div>
      <div>
        <div style={{ fontFamily: FONT_SANS, fontWeight: 600, fontSize: TYPE_SCALE.body, color: COLORS.ink }}>{title}</div>
        <div style={{ marginTop: 8, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.body, color: COLORS.inkSoft, lineHeight: 1.45 }}>{desc}</div>
      </div>
    </div>);

}

/* =====================================================================
   Slide 9 — Co-occurrence
   ===================================================================== */

function SlideCooccurrence({ page, total }) {
  return (
    <Frame label="09 · Stage 3 of 5" page={page} total={total}>
      <Eyebrow>Stage 3 — Co-occurrence Detection</Eyebrow>
      <SlideTitle>An edge for every pair inside a 25-word window.</SlideTitle>

      <div style={{ marginTop: 56, flex: 1, display: 'flex', flexDirection: 'column', gap: SPACING.sectionGap }}>
        <CoOccurrenceWindow />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 32 }}>
          <Metric label="Window size" value="25 tokens" sub="default — tunable per chapter" />
          <Metric label="Lookup" value="O(log n)" sub="bisect over sorted positions" />
          <Metric label="Output" value="Counter[(A,B)] → ω" sub="weighted, undirected" />
        </div>
      </div>
    </Frame>);

}

function CoOccurrenceWindow() {
  const tokens = ['…', 'Hari', 'Seldon', 'sourit', 'à', 'Dors', 'avant', 'que', 'Hummin', 'ne', 'frappe', 'à', 'la', 'porte', '…'];
  const persons = { 'Hari': COLORS.accent, 'Seldon': COLORS.accent, 'Dors': COLORS.accent, 'Hummin': COLORS.accent };
  return (
    <div style={{ background: COLORS.bgAlt, border: `1px solid ${COLORS.rule}`, padding: 36 }}>
      <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.1em' }}>WINDOW · 25 TOKENS</div>
      <div style={{ marginTop: 24, display: 'flex', flexWrap: 'wrap', gap: 14, alignItems: 'baseline' }}>
        {tokens.map((t, i) =>
        <span key={i} style={{
          fontFamily: persons[t] ? FONT_SANS : FONT_SERIF,
          fontWeight: persons[t] ? 600 : 400,
          fontSize: TYPE_SCALE.bodyLg,
          color: persons[t] || COLORS.inkSoft,
          borderBottom: persons[t] ? `2px solid ${persons[t]}` : 'none',
          padding: persons[t] ? '0 4px' : 0
        }}>{t}</span>
        )}
      </div>
      <div style={{ marginTop: 32, display: 'flex', gap: 18, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.small, color: COLORS.ink }}>
        <Pair a="Seldon" b="Dors" />
        <Pair a="Seldon" b="Hummin" />
        <Pair a="Dors" b="Hummin" />
        <span style={{ color: COLORS.inkSoft }}>→ all three pairs +1 weight</span>
      </div>
    </div>);

}

function Pair({ a, b }) {
  return (
    <span style={{ padding: '6px 12px', border: `1px solid ${COLORS.accent}`, color: COLORS.accent }}>
      ({a}, {b})
    </span>);

}

function Metric({ label, value, sub }) {
  return (
    <div style={{ borderTop: `2px solid ${COLORS.ink}`, paddingTop: 20 }}>
      <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.inkSoft, letterSpacing: '0.08em', textTransform: 'uppercase' }}>{label}</div>
      <div style={{ marginTop: 12, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.subtitle, color: COLORS.ink }}>{value}</div>
      {sub && <div style={{ marginTop: 8, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.inkSoft }}>{sub}</div>}
    </div>);

}

/* =====================================================================
   Slide 10 — Relationship classification
   ===================================================================== */

function SlideRelations({ page, total }) {
  return (
    <Frame label="10 · Stage 4 of 5" page={page} total={total}>
      <Eyebrow>Stage 4 — Relationship Classification</Eyebrow>
      <SlideTitle>An edge isn't just <em>weight</em>. It has a <em>sign</em>.</SlideTitle>

      <div style={{ marginTop: 56, display: 'grid', gridTemplateColumns: '1.1fr 1fr', gap: SPACING.sectionGap, flex: 1 }}>
        <div>
          <h3 style={{ fontFamily: FONT_SANS, fontSize: TYPE_SCALE.small, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: COLORS.ink, margin: 0 }}>Method</h3>
          <ol style={{ marginTop: 24, padding: 0, listStyle: 'none', counterReset: 'step', fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.body, lineHeight: 1.45, color: COLORS.inkSoft }}>
            {[
            ['Extract context snippets around every co-occurrence (≤ 100 tokens, max 5 per pair).'],
            ['Feed each snippet to a multilingual sentiment model — XLM-RoBERTa fine-tuned on Twitter sentiment.'],
            ['Map sentiment → relation: positive → friendly · negative → hostile · weak → neutral.'],
            ['Confidence-weighted vote across snippets · threshold 0.45 · default neutral.']].
            map((s, i) =>
            <li key={i} style={{ display: 'grid', gridTemplateColumns: '60px 1fr', gap: 16, marginBottom: 22 }}>
                <span style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.small, color: COLORS.accent }}>0{i + 1}</span>
                <span>{s[0]}</span>
              </li>
            )}
          </ol>
        </div>

        <div style={{ background: COLORS.bgAlt, border: `1px solid ${COLORS.rule}`, padding: 32, alignSelf: 'start' }}>
          <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.1em' }}>EDGE TYPES</div>
          <div style={{ marginTop: 22, display: 'flex', flexDirection: 'column', gap: 18 }}>
            <EdgeRow color={COLORS.friendly} label="friendly" desc="Trust, support, affection" example="Seldon ↔ Dors" />
            <EdgeRow color={COLORS.hostile} label="hostile" desc="Conflict, opposition" example="Baley ↔ Clousarr" />
            <EdgeRow color={COLORS.neutral} label="neutral" desc="Co-present, no strong affect" example="Demerzel ↔ Hummin" />
          </div>
          <Rule my={28} color={COLORS.rule} />
          <div style={{ fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.small, color: COLORS.inkSoft, lineHeight: 1.5 }}>
            Cached per (chapter, pair) — running the pipeline a second time on the same chapter is essentially free.
          </div>
        </div>
      </div>
    </Frame>);

}

function EdgeRow({ color, label, desc, example }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '12px 1fr', gap: 20, paddingBottom: 14, borderBottom: `1px solid ${COLORS.ruleSoft}` }}>
      <div style={{ width: 12, height: 12, borderRadius: '50%', background: color, marginTop: 14 }} />
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <span style={{ fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.bodyLg, color: COLORS.ink }}>{label}</span>
          <span style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.inkSoft }}>{example}</span>
        </div>
        <div style={{ marginTop: 4, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.small, color: COLORS.inkSoft }}>{desc}</div>
      </div>
    </div>);

}

/* =====================================================================
   Slide 11 — Graph & visualization
   ===================================================================== */

function SlideGraph({ page, total }) {
  return (
    <Frame label="11 · Stage 5 of 5" page={page} total={total}>
      <Eyebrow>Stage 5 — Graph & Visualization</Eyebrow>
      <SlideTitle>From Counter to interactive HTML.</SlideTitle>

      <div style={{ marginTop: 56, display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: SPACING.sectionGap, flex: 1 }}>
        <div>
          <Pipeline2 />
          <div style={{ marginTop: 40, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.body, color: COLORS.inkSoft, lineHeight: 1.5 }}>
            Each character is a node weighted by mention count; each co-occurrence is a coloured edge weighted by frequency. The combined HTML viewer renders all chapters in one navigable page with a sidebar grouped by book.
          </div>
        </div>

        <div style={{ background: '#1e293b', borderRadius: 4, padding: 24, position: 'relative' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: '#7a8694', letterSpacing: '0.1em' }}>
            <span>all_networks.html · paf_03</span>
            <span>nodes 28 · edges 41</span>
          </div>
          <div style={{ marginTop: 18, height: 460, background: '#0f0f0f', borderRadius: 2, position: 'relative', overflow: 'hidden' }}>
            <NetworkPreview />
          </div>
          <div style={{ marginTop: 18, display: 'flex', gap: 24, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: '#cfd4da' }}>
            <Legend swatch={COLORS.friendly} label="friendly" />
            <Legend swatch={COLORS.hostile} label="hostile" />
            <Legend swatch={COLORS.neutral} label="neutral" />
          </div>
        </div>
      </div>
    </Frame>);

}

function Pipeline2() {
  const items = [
  'Counter[(A,B)] → weights',
  'Counter[A] → node sizes',
  'edge_labels → colours',
  'NetworkX nx.Graph',
  'GraphML  +  PyVis HTML'];

  return (
    <div>
      {items.map((it, i) =>
      <div key={i} style={{
        display: 'grid', gridTemplateColumns: '60px 1fr', gap: 20,
        padding: '16px 0', borderTop: i === 0 ? `2px solid ${COLORS.ink}` : `1px solid ${COLORS.rule}`
      }}>
          <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent }}>{String(i + 1).padStart(2, '0')}</div>
          <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.body, color: COLORS.ink }}>{it}</div>
        </div>
      )}
    </div>);

}

function NetworkPreview() {
  // A larger, denser network for the screenshot-style preview
  const nodes = [
  { id: 'Seldon', x: 320, y: 240, r: 38 },
  { id: 'Dors', x: 440, y: 160, r: 28 },
  { id: 'Hummin', x: 200, y: 150, r: 26 },
  { id: 'Demerzel', x: 540, y: 250, r: 24 },
  { id: 'Yugo', x: 180, y: 320, r: 20 },
  { id: 'Raych', x: 380, y: 370, r: 22 },
  { id: 'Cléon', x: 600, y: 130, r: 22 },
  { id: 'Davan', x: 100, y: 250, r: 16 },
  { id: 'Rashelle', x: 540, y: 380, r: 18 },
  { id: 'Marron', x: 260, y: 410, r: 14 },
  { id: 'Mycélium', x: 660, y: 320, r: 16 },
  { id: 'Casilia', x: 70, y: 380, r: 14 }];

  const pos = Object.fromEntries(nodes.map((n) => [n.id, n]));
  const edges = [
  ['Seldon', 'Dors', 'f'], ['Seldon', 'Hummin', 'f'], ['Seldon', 'Demerzel', 'n'],
  ['Seldon', 'Yugo', 'f'], ['Seldon', 'Raych', 'f'], ['Seldon', 'Cléon', 'n'],
  ['Dors', 'Hummin', 'f'], ['Dors', 'Raych', 'f'], ['Dors', 'Demerzel', 'n'],
  ['Hummin', 'Davan', 'n'], ['Demerzel', 'Cléon', 'f'], ['Cléon', 'Rashelle', 'h'],
  ['Raych', 'Rashelle', 'h'], ['Raych', 'Marron', 'h'], ['Yugo', 'Davan', 'n'],
  ['Mycélium', 'Demerzel', 'n'], ['Casilia', 'Davan', 'n'], ['Seldon', 'Mycélium', 'n'],
  ['Yugo', 'Casilia', 'n'], ['Hummin', 'Cléon', 'h'], ['Marron', 'Davan', 'h']];

  const colorOf = (t) => t === 'f' ? COLORS.friendly : t === 'h' ? COLORS.hostile : '#5a6470';
  return (
    <svg viewBox="0 0 720 480" style={{ width: '100%', height: '100%' }}>
      {edges.map(([a, b, t], i) =>
      <line key={i} x1={pos[a].x} y1={pos[a].y} x2={pos[b].x} y2={pos[b].y}
      stroke={colorOf(t)} strokeWidth={t === 'n' ? 1 : 1.8} strokeOpacity={0.7} />
      )}
      {nodes.map((n) =>
      <g key={n.id}>
          <circle cx={n.x} cy={n.y} r={n.r} fill="#e7d8c4" fillOpacity={0.95} stroke="#f5e9d6" strokeWidth={1} />
          <text x={n.x} y={n.y + n.r + 16} textAnchor="middle"
        fontFamily={FONT_MONO} fontSize={11} fill="#cfd4da">{n.id}</text>
        </g>
      )}
    </svg>);

}

/* =====================================================================
   Slide 12 — Results
   ===================================================================== */

function SlideResults({ page, total }) {
  return (
    <Frame label="12 · Results" page={page} total={total}>
      <Eyebrow>Results</Eyebrow>
      <SlideTitle>Two novels, 34 chapter graphs, one viewer.</SlideTitle>

      <div style={{ marginTop: 56, display: 'grid', gridTemplateColumns: '1fr 1fr', gap: SPACING.sectionGap, flex: 1 }}>
        <NovelCard
          code="paf"
          title="Prélude à Fondation"
          author="Isaac Asimov · 1988"
          stats={[
          ['Chapters', '— '],
          ['Avg. characters / chapter', '— '],
          ['Total edges', '— '],
          ['Recurring protagonist', 'Hari Seldon']]
          } />
        
        <NovelCard
          code="lca"
          title="Les Cavernes d'Acier"
          author="Isaac Asimov · 1953"
          stats={[
          ['Chapters', '— '],
          ['Avg. characters / chapter', '— '],
          ['Total edges', '— '],
          ['Recurring protagonist', 'Elijah Baley']]
          } />
        
      </div>

      <div style={{ marginTop: 32, fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.inkSoft }}>
        ⓘ Numerical results to be filled in from the IEEE final report.
      </div>
    </Frame>);

}

function NovelCard({ code, title, author, stats }) {
  return (
    <div style={{ border: `1px solid ${COLORS.rule}`, padding: 36, background: COLORS.bg }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
        <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.accent, letterSpacing: '0.14em', textTransform: 'uppercase' }}>{code}</div>
        <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: COLORS.inkSoft }}>{author}</div>
      </div>
      <div style={{ marginTop: 16, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.subtitle, color: COLORS.ink, lineHeight: 1.05 }}>{title}</div>
      <Rule my={28} />
      <div>
        {stats.map(([k, v], i) =>
        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', padding: '12px 0', borderBottom: i === stats.length - 1 ? 'none' : `1px solid ${COLORS.ruleSoft}` }}>
            <span style={{ fontFamily: FONT_SANS, fontSize: TYPE_SCALE.body, color: COLORS.inkSoft }}>{k}</span>
            <span style={{ fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.body, color: COLORS.ink }}>{v}</span>
          </div>
        )}
      </div>
    </div>);

}

/* =====================================================================
   Slide 13 — Challenges & lessons
   ===================================================================== */

function SlideChallenges({ page, total }) {
  const items = [
  { n: '01', t: 'Sci-fi vocabulary', d: 'Off-the-shelf French NER misses ~40 % of Asimov\'s proper nouns. The Asimov gazetteer + EntityRuler closed most of the gap.' },
  { n: '02', t: 'Capitalised non-names', d: 'Sentence-initial words like “Étouffant” were tagged as people. Solved with a per-corpus dynamic blocklist + lowercase-vocabulary check.' },
  { n: '03', t: 'Shared surnames', d: '“Darell” spans three Foundation characters. Without the ambiguity guard, Union-Find collapses them into one super-node.' },
  { n: '04', t: 'Slow inference', d: 'Three NER models + a transformer per pair was unworkable. Lazy-loading, position bisect, and per-pair caching cut per-chapter time by ~5×.' },
  { n: '05', t: 'Sentiment ≠ relationship', d: '“He killed his enemy” reads as negative but expresses a hostile relation correctly. Other cases fail; we accept noise and aggregate by majority.' }];

  return (
    <Frame label="13 · Reflection" page={page} total={total}>
      <Eyebrow>Challenges & Lessons Learned</Eyebrow>
      <SlideTitle>What broke, and what we did about it.</SlideTitle>

      <div style={{ marginTop: 56, columnCount: 2, columnGap: 56, columnFill: 'balance' }}>
        {items.map((it) =>
        <div key={it.n} style={{ breakInside: 'avoid', paddingBottom: 28, marginBottom: 16, borderTop: `2px solid ${COLORS.ink}`, paddingTop: 18 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 16 }}>
              <span style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.small, color: COLORS.accent }}>{it.n}</span>
              <span style={{ fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.subtitle, color: COLORS.ink, lineHeight: 1.05 }}>{it.t}</span>
            </div>
            <div style={{ marginTop: 14, fontFamily: FONT_SERIF, fontSize: TYPE_SCALE.body, color: COLORS.inkSoft, lineHeight: 1.45 }}>{it.d}</div>
          </div>
        )}
      </div>
    </Frame>);

}

/* =====================================================================
   Slide 14 — Thanks / Q&A
   ===================================================================== */

function SlideEnd({ page, total }) {
  return (
    <div style={{
      position: 'absolute', inset: 0, background: COLORS.ink,
      color: COLORS.bg, fontFamily: FONT_SANS,
      padding: `${SPACING.paddingTop}px ${SPACING.paddingX}px ${SPACING.paddingBottom}px`,
      display: 'flex', flexDirection: 'column'
    }}>
      <div style={{
        position: 'absolute', top: 48, left: SPACING.paddingX, right: SPACING.paddingX,
        display: 'flex', justifyContent: 'space-between',
        fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro,
        color: 'rgba(250,250,250,0.5)', letterSpacing: '0.08em', textTransform: 'uppercase'
      }}>
        <span>Réseaux de Personnages</span>
        <span>{String(page).padStart(2, '0')} / {String(total).padStart(2, '0')}</span>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <Eyebrow color="#60a5fa">End</Eyebrow>
        <h1 style={{
          fontFamily: FONT_SERIF, fontWeight: 400,
          fontSize: TYPE_SCALE.display, lineHeight: 1.0,
          letterSpacing: '-0.025em', margin: 0, maxWidth: '70%'
        }}>
          Thank you.<br />
          <span style={{ fontStyle: 'italic', color: '#60a5fa' }}>Questions?</span>
        </h1>

        <div style={{ marginTop: 80, display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 56 }}>
          <Endblock title="Authors" lines={['Lotfi Abdallah', 'Wael Mansoura']} />
          <Endblock title="Supervisor" lines={['Pr. Juan-Manuel', 'Torres-Moreno']} />
          <Endblock title="Source" lines={['github.com/lotfi-abdallah', '/Reseaux-de-personnage']} mono />
        </div>
      </div>

      <div style={{
        position: 'absolute', bottom: 44, left: SPACING.paddingX, right: SPACING.paddingX,
        display: 'flex', justifyContent: 'space-between',
        fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro,
        color: 'rgba(250,250,250,0.5)', letterSpacing: '0.04em'
      }}>
        <span>Lotfi Abdallah · Wael Mansoura</span>
        <span>{useT().university} · {useT().speciality} · {useT().year}</span>
      </div>
    </div>);

}

function Endblock({ title, lines, mono }) {
  return (
    <div>
      <div style={{ fontFamily: FONT_MONO, fontSize: TYPE_SCALE.micro, color: '#60a5fa', letterSpacing: '0.14em', textTransform: 'uppercase' }}>{title}</div>
      <div style={{ marginTop: 18, fontFamily: mono ? FONT_MONO : FONT_SERIF, fontSize: mono ? TYPE_SCALE.small : TYPE_SCALE.body, color: COLORS.bg, lineHeight: 1.5 }}>
        {lines.map((l, i) => <div key={i}>{l}</div>)}
      </div>
    </div>);

}

/* =====================================================================
   Mount everything
   ===================================================================== */

const SLIDES = [
SlideTitleCover, SlideGoal, SlidePipeline, SlideNER, SlideAIEnsemble,
SlideAIFailures, SlideManualNER, SlideAliases, SlideUnionFind, SlideCooccurrence, SlideRelations,
SlideGraph, SlideResults, SlideChallenges, SlideEnd];


const LABELS = [
'01 Title', '02 Goal', '03 Pipeline', '04 NER', '05 Take 1',
'06 The Reality', '07 Take 2', '08 Aliases', '09 Union-Find', '10 Co-occurrence', '11 Relations',
'12 Graph', '13 Results', '14 Challenges', '15 End'];


function App() {
  const [tweaks, setTweaks] = useTweaks(TWEAK_DEFAULTS);
  const total = SLIDES.length;
  return (
    <TweaksCtx.Provider value={tweaks}>
      {SLIDES.map((S, i) =>
      <section key={i} data-label={LABELS[i]}>
          <S page={i + 1} total={total} />
        </section>
      )}
      <TweaksPanel title="Tweaks">
        <TweakSection title="Affiliation">
          <TweakText label="University" value={tweaks.university} onChange={(v) => setTweaks({ university: v })} />
          <TweakText label="Speciality (short)" value={tweaks.speciality} onChange={(v) => setTweaks({ speciality: v })} />
          <TweakText label="Speciality (long, cover)" value={tweaks.specialityLong} onChange={(v) => setTweaks({ specialityLong: v })} />
          <TweakText label="Year" value={tweaks.year} onChange={(v) => setTweaks({ year: v })} />
        </TweakSection>
        <TweakSection title="Display">
          <TweakToggle label="Show footer" value={tweaks.showFooter} onChange={(v) => setTweaks({ showFooter: v })} />
        </TweakSection>
      </TweaksPanel>
    </TweaksCtx.Provider>);

}

const root = ReactDOM.createRoot(document.querySelector('deck-stage'));
root.render(<App />);