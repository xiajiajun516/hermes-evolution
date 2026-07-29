// src/web/assets/js/components/skills.js
import { t } from '../i18n.js';
import { store } from '../store.js';

export function renderSkills(state) {
  const lang = state.lang;
  const skills = state.latest?.skills || [];
  const searchQuery = (state.searchQuery || '').toLowerCase().trim();
  const selectedCategory = state.selectedCategory || 'all';

  // 统计各分类的数量
  const categoriesSet = new Set();
  const categoryCounts = {};
  skills.forEach(s => {
    if (s.category) {
      categoriesSet.add(s.category);
      categoryCounts[s.category] = (categoryCounts[s.category] || 0) + 1;
    }
  });
  const categories = Array.from(categoriesSet).sort();

  function formatCatName(cat) {
    if (!cat) return '';
    if (cat.toLowerCase() === 'mlops') return 'MLOps';
    if (cat.toLowerCase() === 'github') return 'GitHub';
    return cat.split(/[-_]/).map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  }

  // 过滤 Skills
  const filteredSkills = skills.filter(skill => {
    // 1. 分类过滤
    if (selectedCategory !== 'all' && skill.category !== selectedCategory) {
      return false;
    }
    // 2. 搜索框过滤
    if (searchQuery) {
      const matchName = skill.name.toLowerCase().includes(searchQuery);
      const matchDesc = (skill.description || '').toLowerCase().includes(searchQuery);
      const matchCategory = (skill.category || '').toLowerCase().includes(searchQuery);
      const matchTags = (skill.tags || []).some(t => t.toLowerCase().includes(searchQuery));
      return matchName || matchDesc || matchCategory || matchTags;
    }
    return true;
  });

  return `
    <div class="skills-view">
      <!-- 分类 Chip 过滤条 -->
      <div class="tag-filter-bar">
        <button class="filter-chip ${selectedCategory === 'all' ? 'active' : ''}" data-category="all">
          ${t('skill_category_all', {}, lang)} (${skills.length})
        </button>
        ${categories.map(cat => `
          <button class="filter-chip ${selectedCategory === cat ? 'active' : ''}" data-category="${cat}">
            ${formatCatName(cat)} (${categoryCounts[cat] || 0})
          </button>
        `).join('')}
      </div>

      <!-- Skills Cards Grid -->
      ${filteredSkills.length === 0 ? `
        <div class="empty-state card">
          <div class="empty-icon">🔍</div>
          <p>${t('search_empty', {}, lang)}</p>
        </div>
      ` : `
        <div class="grid-container">
          ${filteredSkills.map(skill => `
            <div class="card skill-card">
              <div class="card-title">
                <span>🛠️ ${skill.name}</span>
                <span class="badge badge-blue">v${skill.version || '1.0.0'}</span>
              </div>
              ${skill.category ? `
                <div style="margin-bottom: 0.5rem;">
                  <span class="badge badge-purple">${skill.category}</span>
                </div>
              ` : ''}
              <p class="card-desc">${skill.description || t('skill_no_desc', {}, lang)}</p>
              
              ${skill.tags && skill.tags.length > 0 ? `
                <div class="tags-list">
                  ${skill.tags.map(tag => `<span class="badge">${tag}</span>`).join('')}
                </div>
              ` : ''}

              <div style="margin-top: 0.85rem; font-size: 0.75rem; color: var(--text-secondary); border-top: 1px solid var(--border-color); padding-top: 0.5rem; display: flex; justify-content: space-between;">
                <span title="${skill.path}">${skill.path ? skill.path.split('\\').pop() : ''}</span>
                <span>#${skill.content_hash || '---'}</span>
              </div>
            </div>
          `).join('')}
        </div>
      `}
    </div>
  `;
}

export function bindSkillsEvents(container) {
  container.querySelectorAll('.filter-chip').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const category = e.currentTarget.getAttribute('data-category');
      store.setSelectedCategory(category);
    });
  });
}
