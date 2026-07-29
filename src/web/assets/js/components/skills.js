// src/web/assets/js/components/skills.js
import { t } from '../i18n.js';
import { store } from '../store.js';

let currentPage = 1;
const pageSize = 12;
let lastCategory = null;
let lastSearchQuery = null;
const skillMap = new Map();

function renderPagination(currentPage, totalPages, lang) {
  if (totalPages <= 1) return '';

  let pageBtns = '';
  for (let i = 1; i <= totalPages; i++) {
    pageBtns += `<button class="page-btn ${i === currentPage ? 'active' : ''}" data-page="${i}">${i}</button>`;
  }

  return `
    <div class="pagination-bar">
      <button class="page-btn prev-page-btn" ${currentPage === 1 ? 'disabled' : ''} data-page="${currentPage - 1}">
        ${t('pagination_prev', {}, lang)}
      </button>
      <span class="page-info">${t('page_info', { current: currentPage, total: totalPages }, lang)}</span>
      ${pageBtns}
      <button class="page-btn next-page-btn" ${currentPage === totalPages ? 'disabled' : ''} data-page="${currentPage + 1}">
        ${t('pagination_next', {}, lang)}
      </button>
    </div>
  `;
}

export function openSkillModal(skill, lang = 'zh') {
  const existingModal = document.getElementById('skill-modal-backdrop');
  if (existingModal) {
    existingModal.remove();
  }

  const modalHtml = `
    <div class="modal-backdrop" id="skill-modal-backdrop">
      <div class="skill-modal-card" id="skill-modal-card">
        <div class="modal-header">
          <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <span class="modal-title">🛠️ ${skill.name}</span>
            <span class="badge badge-blue">v${skill.version || '1.0.0'}</span>
            ${skill.category ? `<span class="badge badge-purple">${skill.category}</span>` : ''}
          </div>
          <button class="btn-close" id="skill-modal-close" title="${t('close', {}, lang)}">❌</button>
        </div>
        <div class="modal-body" style="padding: 1.5rem; display: flex; flex-direction: column; gap: 1.25rem;">
          <!-- 📝 描述 (Description) -->
          <div>
            <div class="modal-section-title">📝 ${t('skill_modal_description', {}, lang)}</div>
            <p style="font-size: 0.95rem; color: var(--text-primary); line-height: 1.6; white-space: pre-wrap; word-break: break-word;">
              ${skill.description || t('skill_no_desc', {}, lang)}
            </p>
          </div>

          <!-- 🏷️ 标签 (Tags) -->
          ${skill.tags && skill.tags.length > 0 ? `
            <div>
              <div class="modal-section-title">🏷️ ${t('skill_modal_tags', {}, lang)}</div>
              <div class="tags-list">
                ${skill.tags.map(tag => `<span class="badge">${tag}</span>`).join('')}
              </div>
            </div>
          ` : ''}

          <!-- 📋 详细信息 (Details) -->
          <div class="modal-divider" style="font-size: 0.85rem; color: var(--text-secondary); display: flex; flex-direction: column; gap: 0.5rem;">
            <div class="modal-section-title">📋 ${t('skill_modal_details', {}, lang)}</div>
            <div><strong>${t('skill_path', {}, lang)}:</strong> <code style="font-family: var(--font-mono); background: var(--bg-secondary); padding: 0.2rem 0.4rem; border-radius: var(--radius-sm);">${skill.path || 'N/A'}</code></div>
            <div><strong>${t('skill_hash', {}, lang)}:</strong> <code style="font-family: var(--font-mono); background: var(--bg-secondary); padding: 0.2rem 0.4rem; border-radius: var(--radius-sm);">#${skill.content_hash || '---'}</code></div>
          </div>
        </div>
      </div>
    </div>
  `;

  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = modalHtml.trim();
  const backdrop = tempDiv.firstElementChild;

  document.body.appendChild(backdrop);

  const closeModal = () => {
    if (backdrop && backdrop.parentNode) {
      backdrop.parentNode.removeChild(backdrop);
    }
    document.removeEventListener('keydown', handleKeyDown);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Escape') {
      closeModal();
    }
  };

  const closeBtn = backdrop.querySelector('#skill-modal-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', closeModal);
  }

  backdrop.addEventListener('click', (e) => {
    if (e.target === backdrop) {
      closeModal();
    }
  });

  document.addEventListener('keydown', handleKeyDown);
}

export function renderSkills(state) {
  const lang = state.lang;
  const skills = state.latest?.skills || [];
  const searchQuery = (state.searchQuery || '').toLowerCase().trim();
  const selectedCategory = state.selectedCategory || 'all';

  if (lastCategory !== selectedCategory || lastSearchQuery !== searchQuery) {
    currentPage = 1;
    lastCategory = selectedCategory;
    lastSearchQuery = searchQuery;
  }

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

  const totalPages = Math.ceil(filteredSkills.length / pageSize) || 1;
  if (currentPage > totalPages) currentPage = totalPages;
  if (currentPage < 1) currentPage = 1;

  const startIndex = (currentPage - 1) * pageSize;
  const pagedSkills = filteredSkills.slice(startIndex, startIndex + pageSize);

  skillMap.clear();

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
          ${pagedSkills.map((skill, index) => {
            const skillKey = `skill_${startIndex + index}`;
            skillMap.set(skillKey, skill);
            return `
              <div class="card skill-card" data-skill-id="${skillKey}">
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
                    ${skill.tags.slice(0, 4).map(tag => `<span class="badge">${tag}</span>`).join('')}
                    ${skill.tags.length > 4 ? `<span class="badge">+${skill.tags.length - 4}</span>` : ''}
                  </div>
                ` : ''}

                <div style="margin-top: 0.85rem; font-size: 0.75rem; color: var(--text-secondary); border-top: 1px solid var(--border-color); padding-top: 0.5rem; display: flex; justify-content: space-between;">
                  <span title="${skill.path}">${skill.path ? skill.path.split('\\').pop() : ''}</span>
                  <span>#${skill.content_hash || '---'}</span>
                </div>
              </div>
            `;
          }).join('')}
        </div>
        ${renderPagination(currentPage, totalPages, lang)}
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

  container.querySelectorAll('.pagination-bar .page-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      if (e.currentTarget.hasAttribute('disabled')) return;
      const page = parseInt(e.currentTarget.getAttribute('data-page'), 10);
      if (page && page !== currentPage) {
        currentPage = page;
        store.notify();
        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  container.querySelectorAll('.skill-card').forEach(card => {
    card.addEventListener('click', (e) => {
      const skillId = card.getAttribute('data-skill-id');
      const skill = skillMap.get(skillId);
      if (skill) {
        const state = store.state;
        openSkillModal(skill, state.lang);
      }
    });
  });
}
