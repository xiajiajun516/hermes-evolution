// src/web/assets/js/components/dashboard.js
import { t } from '../i18n.js';

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
                    <span class="badge badge-blue">${item.summary || ''}</span>
                  </div>
                  <div class="timeline-summary">${item.title}</div>
                  ${item.changes && item.changes.length > 0 ? `
                    <div style="margin-top: 0.5rem;">
                      ${item.changes.map(c => `
                        <div class="change-item">
                          <span class="badge ${c.type.includes('added') ? 'badge-green' : c.type.includes('updated') ? 'badge-blue' : 'badge-red'}">
                            ${c.type}
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
