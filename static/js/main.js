/* ============================================================
   main.js — Map Coloring CSP Solver Frontend Logic
   ============================================================ */

// ── Color Configuration ──────────────────────────────────────
const COLOR_META = {
  Red:    { hex: '#ef4444', badge: 'badge-red',    dot: '#ef4444' },
  Green:  { hex: '#10b981', badge: 'badge-green',  dot: '#10b981' },
  Blue:   { hex: '#3b82f6', badge: 'badge-blue',   dot: '#3b82f6' },
  Yellow: { hex: '#f59e0b', badge: 'badge-yellow', dot: '#f59e0b' },
  Purple: { hex: '#8b5cf6', badge: 'badge-purple', dot: '#8b5cf6' },
  Orange: { hex: '#f97316', badge: 'badge-orange', dot: '#f97316' },
  Cyan:   { hex: '#06b6d4', badge: 'badge-cyan',   dot: '#06b6d4' },
};

// ── Tag Input (Regions) ───────────────────────────────────────
class TagInput {
  constructor(wrapperId, hiddenId) {
    this.wrap   = document.getElementById(wrapperId);
    this.hidden = document.getElementById(hiddenId);
    this.tags   = [];
    if (!this.wrap) return;
    this.input  = this.wrap.querySelector('.tag-real-input');
    this._bind();
  }

  _bind() {
    this.input.addEventListener('keydown', e => {
      if ((e.key === 'Enter' || e.key === ',') && this.input.value.trim()) {
        e.preventDefault();
        this.add(this.input.value.trim().replace(/,/g, ''));
      }
      if (e.key === 'Backspace' && !this.input.value && this.tags.length) {
        this.remove(this.tags[this.tags.length - 1]);
      }
    });
    this.wrap.addEventListener('click', () => this.input.focus());
  }

  add(val) {
    if (!val || this.tags.includes(val)) return;
    this.tags.push(val);
    this._render();
    this._refresh();
    this.input.value = '';
  }

  remove(val) {
    this.tags = this.tags.filter(t => t !== val);
    this._render();
    this._refresh();
  }

  _render() {
    const existing = this.wrap.querySelectorAll('.tag');
    existing.forEach(t => t.remove());
    this.tags.forEach(tag => {
      const el = document.createElement('span');
      el.className = 'tag';
      el.innerHTML = `${tag}<span class="tag-remove" data-tag="${tag}">×</span>`;
      el.querySelector('.tag-remove').addEventListener('click', e => {
        e.stopPropagation();
        this.remove(tag);
      });
      this.wrap.insertBefore(el, this.input);
    });
  }

  _refresh() {
    if (this.hidden) this.hidden.value = this.tags.join(',');
  }

  getRegions() { return [...this.tags]; }
}

// ── Neighbor Builder ──────────────────────────────────────────
class NeighborBuilder {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.rows = {};
  }

  buildRows(regions) {
    if (!this.container) return;
    this.container.innerHTML = '';
    this.rows = {};

    if (!regions.length) {
      this.container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;padding:12px;">Add regions above to configure adjacency.</p>';
      return;
    }

    regions.forEach(region => {
      const div = document.createElement('div');
      div.className = 'form-group';
      div.innerHTML = `
        <label class="form-label">
          <span style="color:var(--accent2);font-weight:700;">${region}</span> is adjacent to:
        </label>
        <div class="tag-input-wrap" id="nbr-wrap-${region}">
          <input class="tag-real-input" placeholder="Type neighbor name, press Enter" id="nbr-input-${region}">
        </div>
      `;
      this.container.appendChild(div);

      const nbrTag = new TagInput(`nbr-wrap-${region}`, null);
      nbrTag.wrap.querySelector('.tag-real-input').addEventListener('keydown', e => {
        if ((e.key === 'Enter' || e.key === ',') && e.target.value.trim()) {
          e.preventDefault();
          const val = e.target.value.trim().replace(/,/g, '');
          if (regions.includes(val) && val !== region) {
            nbrTag.add(val);
          } else {
            showToast(`"${val}" is not a valid region.`, 'warning');
          }
        }
      });
      this.rows[region] = nbrTag;
    });
  }

  getNeighbors() {
    const out = {};
    for (const [region, tagInput] of Object.entries(this.rows)) {
      out[region] = tagInput.getRegions();
    }
    return out;
  }
}

// ── Confidence Ring ───────────────────────────────────────────
function animateConfidenceRing(score) {
  const fill  = document.getElementById('ring-fill');
  const label = document.getElementById('ring-score');
  if (!fill || !label) return;

  const circumference = 314;
  const color = score >= 80 ? '#10b981' : score >= 50 ? '#f59e0b' : '#ef4444';

  fill.style.stroke = color;
  label.style.color = color;

  let current = 0;
  const target = score;
  const step = target / 60;

  const interval = setInterval(() => {
    current = Math.min(current + step, target);
    const offset = circumference - (current / 100) * circumference;
    fill.style.strokeDashoffset = offset;
    label.textContent = Math.round(current) + '%';
    if (current >= target) clearInterval(interval);
  }, 16);
}

// ── Timeline Renderer ─────────────────────────────────────────
function renderTimeline(timeline) {
  const container = document.getElementById('timeline-container');
  if (!container) return;
  container.innerHTML = '';

  if (!timeline || !timeline.length) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">No steps to display.</p>';
    return;
  }

  timeline.forEach((item, i) => {
    const div = document.createElement('div');
    div.className = `timeline-item ${item.cls || item.type}`;
    div.style.opacity = '0';
    div.style.transform = 'translateX(-10px)';
    div.innerHTML = `
      <div class="timeline-body">
        <div class="timeline-step">STEP ${item.step} &nbsp;•&nbsp; ${item.icon} ${item.label}</div>
        <div class="timeline-msg">${item.message}</div>
      </div>
    `;
    container.appendChild(div);

    setTimeout(() => {
      div.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
      div.style.opacity = '1';
      div.style.transform = 'translateX(0)';
    }, i * 40);
  });
}

// ── Constraint Renderer ───────────────────────────────────────
function renderConstraints(satisfied, violated) {
  const container = document.getElementById('constraint-container');
  if (!container) return;
  container.innerHTML = '';

  const all = [
    ...satisfied.map(c => ({ ...c, type: 'satisfied' })),
    ...violated.map(c => ({ ...c, type: 'violated' })),
  ];

  if (!all.length) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">No adjacency constraints found.</p>';
    return;
  }

  all.forEach(item => {
    const div = document.createElement('div');
    div.className = `constraint-item ${item.type}`;
    const icon   = item.type === 'satisfied' ? '✓' : '✗';
    const badge  = item.type === 'satisfied' ? 'badge-success' : 'badge-danger';
    const detail = item.detail || '';
    div.innerHTML = `
      <span style="font-weight:600;">${item.pair}</span>
      <div style="display:flex;align-items:center;gap:8px;">
        <span style="font-size:12px;color:var(--text-muted);">${detail}</span>
        <span class="badge ${badge}">${icon} ${item.type}</span>
      </div>
    `;
    container.appendChild(div);
  });
}

// ── Solution Cards Renderer ───────────────────────────────────
function renderSolutionCards(solution) {
  const container = document.getElementById('solution-cards');
  if (!container) return;
  container.innerHTML = '';

  const entries = Object.entries(solution);
  if (!entries.length) {
    container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;">No solution generated.</p>';
    return;
  }

  entries.forEach(([region, color]) => {
    const meta = COLOR_META[color] || { hex: '#888', badge: 'badge-purple', dot: '#888' };
    const card = document.createElement('div');
    card.className = `region-card color-${color}`;
    card.style.opacity = '0';
    card.style.transform = 'scale(0.9)';
    card.innerHTML = `
      <div class="rc-dot" style="background:${meta.hex};"></div>
      <div class="rc-name">${region}</div>
      <span class="badge ${meta.badge}">${color}</span>
    `;
    container.appendChild(card);

    requestAnimationFrame(() => {
      card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      card.style.opacity = '1';
      card.style.transform = 'scale(1)';
    });
  });
}

// ── Adjacency Matrix Renderer ─────────────────────────────────
function renderMatrix(matrixData) {
  const container = document.getElementById('matrix-container');
  if (!container || !matrixData) return;
  const { regions, matrix } = matrixData;

  let html = '<div class="matrix-wrap"><table class="matrix-table"><thead><tr><th></th>';
  regions.forEach(r => { html += `<th>${r}</th>`; });
  html += '</tr></thead><tbody>';

  matrix.forEach((row, i) => {
    html += `<tr><th>${regions[i]}</th>`;
    row.forEach((val, j) => {
      const cls = i === j ? 'self' : val ? 'adj' : 'none';
      html += `<td class="${cls}">${i === j ? '—' : val ? '1' : '0'}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody></table></div>';
  container.innerHTML = html;
}

// ── Complexity Banner ─────────────────────────────────────────
function setComplexityBanner(label) {
  const el = document.getElementById('complexity-banner');
  if (!el) return;
  const cls = label.startsWith('LOW') ? 'complexity-low'
            : label.startsWith('MED') ? 'complexity-medium'
            : 'complexity-high';
  el.className = `complexity-banner ${cls}`;
  el.textContent = label;
}

// ── Toast Notification ────────────────────────────────────────
function showToast(message, type = 'info') {
  const colors = { success: '#10b981', danger: '#ef4444', warning: '#f59e0b', info: '#6c63ff' };
  const toast = document.createElement('div');
  toast.style.cssText = `
    position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:10px;
    background:var(--bg-card);border:1px solid ${colors[type]||colors.info};
    color:#fff;font-size:13px;font-weight:500;z-index:9999;
    box-shadow:0 8px 32px rgba(0,0,0,.4);display:flex;align-items:center;gap:10px;
    transform:translateY(20px);opacity:0;transition:all 0.3s ease;
  `;
  const dot = document.createElement('span');
  dot.style.cssText = `width:8px;height:8px;border-radius:50%;background:${colors[type]||colors.info};flex-shrink:0;`;
  toast.appendChild(dot);
  toast.appendChild(document.createTextNode(message));
  document.body.appendChild(toast);

  requestAnimationFrame(() => {
    toast.style.transform = 'translateY(0)';
    toast.style.opacity = '1';
  });
  setTimeout(() => {
    toast.style.transform = 'translateY(20px)';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ── Progress Bar Animater ─────────────────────────────────────
function animateProgress(id, percent) {
  const bar = document.getElementById(id);
  if (!bar) return;
  bar.style.width = '0%';
  setTimeout(() => { bar.style.width = percent + '%'; }, 100);
}

// ── Main Solver Form ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const solverForm = document.getElementById('solver-form');
  if (!solverForm) return;

  const tagInput      = new TagInput('region-wrap', 'regions-hidden');
  const neighborBuild = new NeighborBuilder('neighbor-container');

  // Rebuild neighbor rows whenever regions change
  const observer = new MutationObserver(() => {
    neighborBuild.buildRows(tagInput.getRegions());
  });
  if (tagInput.wrap) {
    observer.observe(tagInput.wrap, { childList: true, subtree: true });
  }

  solverForm.addEventListener('submit', async e => {
    e.preventDefault();

    const regions   = tagInput.getRegions();
    const neighbors = neighborBuild.getNeighbors();
    const colorSel  = document.getElementById('color-select');
    const colors    = colorSel ? Array.from(colorSel.selectedOptions).map(o => o.value)
                               : ['Red', 'Green', 'Blue'];

    if (regions.length < 2) {
      showToast('Add at least 2 regions.', 'warning');
      return;
    }

    const submitBtn = document.getElementById('solve-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner" style="width:18px;height:18px;border-width:2px;display:inline-block;vertical-align:middle;margin-right:8px;"></span>Solving…';

    const resultSection = document.getElementById('result-section');
    if (resultSection) { resultSection.style.display = 'none'; }

    try {
      const res  = await fetch('/solve_map', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ regions, neighbors, colors }),
      });
      const data = await res.json();

      if (!res.ok || data.errors) {
        showToast((data.errors || ['Server error.']).join(' '), 'danger');
        return;
      }

      if (resultSection) { resultSection.style.display = 'block'; }

      // Render all panels
      renderSolutionCards(data.solution || {});
      renderTimeline(data.timeline || []);
      renderConstraints(data.constraints_satisfied || [], data.constraints_violated || []);
      renderMatrix(data.adj_matrix);
      animateConfidenceRing(data.confidence_score || 0);
      setComplexityBanner(data.complexity_label || '');
      animateProgress('satisfaction-bar', data.satisfaction_pct || 0);

      // Update stats
      _setText('stat-backtracks',   data.backtracks);
      _setText('stat-elapsed',      data.elapsed_ms + ' ms');
      _setText('stat-regions',      `${data.regions_colored}/${data.total_regions}`);
      _setText('stat-sat-pct',      data.satisfaction_pct + '%');
      _setText('exec-id-badge',     '#' + data.execution_id);

      const statusEl = document.getElementById('solve-status');
      if (statusEl) {
        statusEl.className = 'badge ' + (data.success ? 'badge-success' : 'badge-danger');
        statusEl.textContent = data.success ? '✓ SOLVED' : '✗ NO SOLUTION';
      }

      if (data.warnings && data.warnings.length) {
        data.warnings.forEach(w => showToast(w, 'warning'));
      }

      showToast(data.success ? 'Map colored successfully!' : 'No valid coloring found. Try more colors.', data.success ? 'success' : 'danger');

    } catch (err) {
      showToast('Network error: ' + err.message, 'danger');
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '🗺️ Solve Map Coloring';
    }
  });

  function _setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  // ── PDF Download Button ──────────────────────────────────────
  const pdfBtn = document.getElementById('pdf-btn');
  if (pdfBtn) {
    pdfBtn.addEventListener('click', () => {
      const execId = document.getElementById('exec-id-badge')?.textContent?.replace('#', '');
      if (!execId || execId === '—') {
        showToast('Solve a map first to generate a report.', 'warning');
        return;
      }
      window.open(`/generate_report/${execId}`, '_blank');
    });
  }

  // Auto-dismiss flash messages
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 4000);
  });
});
