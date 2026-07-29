// src/web/assets/js/store.js

export const store = {
  state: {
    meta: {
      generated_at: "",
      lang: "zh",
      project: "",
      stats: { skills: 0, memories: 0, cron_jobs: 0, total_changes: 0 },
      evolution: { skills_added: 0, skills_updated: 0, memories_changed: 0 },
      projects: []
    },
    timeline: [],
    latest: {
      timestamp: "",
      hermes_home: "",
      skills: [],
      memories: [],
      cron_jobs: []
    },
    currentTab: localStorage.getItem('hermes_tab') || 'dashboard',
    searchQuery: '',
    selectedProject: 'all',
    selectedCategory: 'all',
    lang: localStorage.getItem('hermes_lang') || 'zh',
    loading: true,
    error: null
  },

  listeners: [],

  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  },

  notify() {
    this.listeners.forEach(fn => {
      try {
        fn(this.state);
      } catch (err) {
        console.error("Store listener error:", err);
      }
    });
  },

  setLang(newLang) {
    if (this.state.lang === newLang) return;
    this.state.lang = newLang;
    localStorage.setItem('hermes_lang', newLang);
    this.notify();
  },

  setTab(tab) {
    if (this.state.currentTab === tab) return;
    this.state.currentTab = tab;
    localStorage.setItem('hermes_tab', tab);
    this.notify();
  },

  setSearchQuery(query) {
    this.state.searchQuery = query;
    this.notify();
  },

  setSelectedProject(project) {
    this.state.selectedProject = project;
    this.notify();
  },

  setSelectedCategory(category) {
    this.state.selectedCategory = category;
    this.notify();
  },

  async loadData() {
    this.state.loading = true;
    this.notify();

    // 1. 尝试从 window.__INITIAL_DATA__ 降级读取
    if (window.__INITIAL_DATA__) {
      const data = window.__INITIAL_DATA__;
      this.state.meta = data.meta || this.state.meta;
      this.state.timeline = data.timeline || [];
      this.state.latest = data.latest || this.state.latest;
      // 恢复受 localStorage 持久化的状态（刷新后保留）
      this.state.currentTab = localStorage.getItem('hermes_tab') || 'dashboard';
      this.state.lang = localStorage.getItem('hermes_lang') || 'zh';
      this.state.loading = false;
      this.notify();
      return;
    }

    // 2. 从 RESTful JSON API 异步拉取
    try {
      const [metaRes, timelineRes, latestRes] = await Promise.all([
        fetch('api/v1/meta.json').then(r => r.ok ? r.json() : null).catch(() => null),
        fetch('api/v1/timeline.json').then(r => r.ok ? r.json() : null).catch(() => null),
        fetch('api/v1/latest.json').then(r => r.ok ? r.json() : null).catch(() => null)
      ]);

      if (metaRes) this.state.meta = metaRes;
      if (timelineRes) this.state.timeline = timelineRes;
      if (latestRes) this.state.latest = latestRes;

      // 如果全部拉取失败且没有数据，尝试回退根目录 timeline.json
      if (!latestRes && !timelineRes) {
        const legacyTimeline = await fetch('timeline.json').then(r => r.ok ? r.json() : []).catch(() => []);
        if (legacyTimeline && legacyTimeline.length > 0) {
          this.state.timeline = legacyTimeline;
        }
      }

      this.state.loading = false;
    } catch (err) {
      console.warn("API fetch error, using fallback empty state", err);
      this.state.error = err.message;
      this.state.loading = false;
    }

    this.notify();
  }
};
