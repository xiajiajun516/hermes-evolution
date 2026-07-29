// src/web/assets/js/components/dashboard.js
import { t } from '../i18n.js';

function formatChangeType(type, lang) {
  const key = `type_${type}`;
  const translated = t(key, {}, lang);
  return translated !== key ? translated : type;
}

function formatEntryTitle(entry, lang) {
  if (!entry.changes || entry.changes.length === 0) {
    return entry.title || t('change_title_fallback', {}, lang);
  }
  const counts = {};
  entry.changes.forEach(c => {
    counts[c.type] = (counts[c.type] || 0) + 1;
  });
  const parts = [];
  if (counts.skill_added) parts.push(t('change_skill_added', { n: counts.skill_added }, lang));
  if (counts.skill_updated) parts.push(t('change_skill_updated', { n: counts.skill_updated }, lang));
  if (counts.skill_removed) parts.push(t('change_skill_removed', { n: counts.skill_removed }, lang));
  if (counts.memory_added) parts.push(t('change_memory_added', { n: counts.memory_added }, lang));
  if (counts.memory_removed) parts.push(t('change_memory_removed', { n: counts.memory_removed }, lang));
  if (counts.cron_added) parts.push(t('change_cron_added', { n: counts.cron_added }, lang));
  if (counts.cron_removed) parts.push(t('change_cron_removed', { n: counts.cron_removed }, lang));
  return parts.length > 0 ? parts.join(' · ') : entry.title;
}

function formatEntrySummary(entry, lang) {
  const count = entry.changes ? entry.changes.length : 0;
  return count > 0 ? t('change_summary', { n: count }, lang) : (entry.summary || '');
}

export function renderDashboard(state) {
  const lang = state.lang;
  const latest = state.latest || {};
  const stats = state.meta?.stats || {
    skills: latest.skills?.length || 0,
    memories: latest.memories?.length || 0,
    cron_jobs: latest.cron_jobs?.length || 0,
    total_changes: state.timeline?.length || 0
  };

  const evo = state.meta?.evolution || {
    skills_added: 0,
    skills_updated: 0,
    memories_changed: 0
  };

  const recentTimeline = (state.timeline || []).slice(0, 5);

  return `
    <div class="dashboard-view">
      <!-- 统计卡片 Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">🛠️</div>
          <div>
            <div class="stat-value">${stats.skills}</div>
            <div class="stat-label">${t('stat_skills', {}, lang)}</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">🧠</div>
          <div>
            <div class="stat-value">${stats.memories}</div>
            <div class="stat-label">${t('stat_memories', {}, lang)}</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">⏱️</div>
          <div>
            <div class="stat-value">${stats.cron_jobs}</div>
            <div class="stat-label">${t('stat_cron', {}, lang)}</div>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-icon">⚡</div>
          <div>
            <div class="stat-value">${stats.total_changes}</div>
            <div class="stat-label">${t('stat_changes', {}, lang)}</div>
          </div>
        </div>
      </div>

      <!-- 进化概览卡片 -->
      <div class="card" style="margin-bottom: 1.5rem;">
        <h2 class="card-title">${t('section_overview', {}, lang)}</h2>
        <div class="tags-list" style="margin-top: 0.75rem;">
          <span class="badge badge-green">✨ ${t('evo_skills_added', {}, lang)}: +${evo.skills_added || 0}</span>
          <span class="badge badge-blue">🔄 ${t('evo_skills_updated', {}, lang)}: ${evo.skills_updated || 0}</span>
          <span class="badge badge-purple">🧠 ${t('evo_memories_changed', {}, lang)}: ${evo.memories_changed || 0}</span>
        </div>
      </div>

      <!-- 最近进化动态 -->
      <div class="card">
        <h2 class="card-title">${t('section_recent_activity', {}, lang)}</h2>
        ${recentTimeline.length === 0 ? `
          <div class="empty-state">
            <p>${t('archive_empty_title', {}, lang)}</p>
          </div>
        ` : `
          <div class="timeline" style="margin-top: 1rem;">
            ${recentTimeline.map(item => `
              <div class="timeline-item">
                <div class="timeline-dot"></div>
                <div class="timeline-card">
                  <div class="timeline-header">
                    <span class="timeline-date">📅 ${item.date}</span>
                    <span class="badge badge-blue">${formatEntrySummary(item, lang)}</span>
                  </div>
                  <div class="timeline-summary">${formatEntryTitle(item, lang)}</div>
                  ${item.changes && item.changes.length > 0 ? `
                    <div style="margin-top: 0.5rem;">
                      ${item.changes.map(c => `
                        <div class="change-item">
                          <span class="badge ${c.type.includes('added') ? 'badge-green' : c.type.includes('updated') ? 'badge-blue' : 'badge-red'}">
                            ${formatChangeType(c.type, lang)}
                          </span>
                          <strong>${c.name}</strong>
                          ${c.desc ? `<span class="change-item-desc">(${c.desc})</span>` : ''}
                        </div>
                      `).join('')}
                    </div>
                  ` : ''}
                </div>
              </div>
            `).join('')}
          </div>
        `}
      </div>
    </div>
  `;
}
