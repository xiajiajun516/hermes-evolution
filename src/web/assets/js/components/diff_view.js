// src/web/assets/js/components/diff_view.js

function escapeHtml(text) {
  return (text || '')
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

/**
 * 纯前端轻量 LCS Diff 算法
 */
export function diffLines(oldLines, newLines) {
  const M = oldLines.length;
  const N = newLines.length;
  const dp = Array.from({ length: M + 1 }, () => new Int32Array(N + 1));

  for (let i = M - 1; i >= 0; i--) {
    for (let j = N - 1; j >= 0; j--) {
      if (oldLines[i] === newLines[j]) {
        dp[i][j] = dp[i + 1][j + 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i + 1][j], dp[i][j + 1]);
      }
    }
  }

  const result = [];
  let i = 0, j = 0;
  let oldLineNum = 1, newLineNum = 1;

  while (i < M && j < N) {
    if (oldLines[i] === newLines[j]) {
      result.push({
        type: 'unchanged',
        oldLineNum: oldLineNum++,
        newLineNum: newLineNum++,
        oldVal: oldLines[i],
        newVal: newLines[j]
      });
      i++;
      j++;
    } else if (dp[i + 1][j] >= dp[i][j + 1]) {
      result.push({
        type: 'removed',
        oldLineNum: oldLineNum++,
        newLineNum: null,
        oldVal: oldLines[i],
        newVal: ''
      });
      i++;
    } else {
      result.push({
        type: 'added',
        oldLineNum: null,
        newLineNum: newLineNum++,
        oldVal: '',
        newVal: newLines[j]
      });
      j++;
    }
  }
  while (i < M) {
    result.push({
      type: 'removed',
      oldLineNum: oldLineNum++,
      newLineNum: null,
      oldVal: oldLines[i],
      newVal: ''
    });
    i++;
  }
  while (j < N) {
    result.push({
      type: 'added',
      oldLineNum: null,
      newLineNum: newLineNum++,
      oldVal: '',
      newVal: newLines[j]
    });
    j++;
  }

  return result;
}

/**
 * 构建 Side-by-Side 对齐行
 */
function buildSideBySideRows(diffItems) {
  const rows = [];
  let i = 0;

  while (i < diffItems.length) {
    const item = diffItems[i];
    if (item.type === 'unchanged') {
      rows.push({
        left: { type: 'unchanged', lineNum: item.oldLineNum, text: item.oldVal },
        right: { type: 'unchanged', lineNum: item.newLineNum, text: item.newVal }
      });
      i++;
    } else {
      const removedList = [];
      const addedList = [];
      while (i < diffItems.length && diffItems[i].type !== 'unchanged') {
        if (diffItems[i].type === 'removed') {
          removedList.push(diffItems[i]);
        } else if (diffItems[i].type === 'added') {
          addedList.push(diffItems[i]);
        }
        i++;
      }
      const maxLen = Math.max(removedList.length, addedList.length);
      for (let k = 0; k < maxLen; k++) {
        const rem = removedList[k];
        const add = addedList[k];
        rows.push({
          left: rem ? { type: 'removed', lineNum: rem.oldLineNum, text: rem.oldVal } : { type: 'empty', lineNum: '', text: '' },
          right: add ? { type: 'added', lineNum: add.newLineNum, text: add.newVal } : { type: 'empty', lineNum: '', text: '' }
        });
      }
    }
  }

  return rows;
}

function renderSideBySideTable(diffItems) {
  const rows = buildSideBySideRows(diffItems);
  return `
    <table class="diff-table diff-sbs">
      <thead>
        <tr>
          <th class="diff-col-num">#</th>
          <th class="diff-col-content">Original (旧版本)</th>
          <th class="diff-col-num">#</th>
          <th class="diff-col-content">Modified (新版本)</th>
        </tr>
      </thead>
      <tbody>
        ${rows.map(row => `
          <tr>
            <td class="diff-num ${row.left.type}">${row.left.lineNum || ''}</td>
            <td class="diff-code ${row.left.type}"><code>${escapeHtml(row.left.text)}</code></td>
            <td class="diff-num ${row.right.type}">${row.right.lineNum || ''}</td>
            <td class="diff-code ${row.right.type}"><code>${escapeHtml(row.right.text)}</code></td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
}

function renderUnifiedTable(diffItems) {
  return `
    <table class="diff-table diff-unified">
      <thead>
        <tr>
          <th class="diff-col-num">Old</th>
          <th class="diff-col-num">New</th>
          <th class="diff-col-prefix">+/-</th>
          <th class="diff-col-content">Content</th>
        </tr>
      </thead>
      <tbody>
        ${diffItems.map(item => {
          let prefix = ' ';
          if (item.type === 'added') prefix = '+';
          if (item.type === 'removed') prefix = '-';
          const text = item.type === 'removed' ? item.oldVal : item.newVal;

          return `
            <tr class="diff-row-${item.type}">
              <td class="diff-num ${item.type}">${item.oldLineNum || ''}</td>
              <td class="diff-num ${item.type}">${item.newLineNum || ''}</td>
              <td class="diff-prefix ${item.type}">${prefix}</td>
              <td class="diff-code ${item.type}"><code>${escapeHtml(text)}</code></td>
            </tr>
          `;
        }).join('')}
      </tbody>
    </table>
  `;
}

/**
 * 渲染 Diff 组件 HTML
 */
export function renderDiffView(oldText = '', newText = '', mode = 'side-by-side') {
  const oldStr = typeof oldText === 'string' ? oldText : JSON.stringify(oldText, null, 2);
  const newStr = typeof newText === 'string' ? newText : JSON.stringify(newText, null, 2);

  const oldLines = oldStr.split('\n');
  const newLines = newStr.split('\n');
  const diffItems = diffLines(oldLines, newLines);

  let additions = 0;
  let deletions = 0;
  diffItems.forEach(item => {
    if (item.type === 'added') additions++;
    if (item.type === 'removed') deletions++;
  });

  return `
    <div class="diff-viewer-container" data-mode="${mode}">
      <div class="diff-toolbar">
        <div class="diff-mode-switch">
          <button class="btn btn-sm diff-mode-btn ${mode === 'side-by-side' ? 'active' : ''}" data-mode="side-by-side">
            Side-by-Side ↔️
          </button>
          <button class="btn btn-sm diff-mode-btn ${mode === 'unified' ? 'active' : ''}" data-mode="unified">
            Unified 📄
          </button>
        </div>
        <div class="diff-legend">
          <span class="diff-tag diff-tag-del">-${deletions}</span>
          <span class="diff-tag diff-tag-add">+${additions}</span>
        </div>
      </div>
      <div class="diff-content-wrapper">
        ${mode === 'side-by-side' ? renderSideBySideTable(diffItems) : renderUnifiedTable(diffItems)}
      </div>
    </div>
  `;
}

/**
 * 绑定 Diff 视图交互事件 (切换模式)
 */
export function bindDiffEvents(container, oldText, newText) {
  const modeBtns = container.querySelectorAll('.diff-mode-btn');
  modeBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      const mode = e.currentTarget.getAttribute('data-mode');
      const viewer = container.querySelector('.diff-viewer-container');
      if (viewer) {
        viewer.outerHTML = renderDiffView(oldText, newText, mode);
        bindDiffEvents(container, oldText, newText);
      }
    });
  });
}

/**
 * 弹窗模式渲染 Visual Diff
 */
export function openDiffModal(title, oldText, newText) {
  const modalContainer = document.getElementById('modal-container');
  if (!modalContainer) return;

  const modalHtml = `
    <div class="modal-backdrop" id="diff-modal-backdrop">
      <div class="modal-card diff-modal-card">
        <div class="modal-header">
          <h3 class="modal-title">🔍 Visual Diff: ${escapeHtml(title)}</h3>
          <button class="btn-close" id="diff-modal-close" title="关闭">&times;</button>
        </div>
        <div class="modal-body" id="diff-modal-body">
          ${renderDiffView(oldText, newText, 'side-by-side')}
        </div>
      </div>
    </div>
  `;

  modalContainer.innerHTML = modalHtml;

  const backdrop = document.getElementById('diff-modal-backdrop');
  const closeBtn = document.getElementById('diff-modal-close');

  const closeModal = () => {
    modalContainer.innerHTML = '';
  };

  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (backdrop) {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) closeModal();
    });
  }

  bindDiffEvents(modalContainer, oldText, newText);
}
