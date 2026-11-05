'use strict';
(() => {
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const state = { data: null, papers: [], status: null, editorialStatus: null, land: null, selectedSchool: null, selectedCity: null, topic: '', search: '', unreadOnly: false, view: 'atlas', read: {}, storageEnabled: true };
  const READ_KEY = 'comm-atlas.read-revisions.v1';
  const svgNS = 'http://www.w3.org/2000/svg';
  const bounds = { west: 99, east: 133, south: 17.5, north: 48 };
  const knownClusters = {
    tsinghua: 'beijing', pku: 'beijing', buaa: 'beijing', bit: 'beijing', bupt: 'beijing',
    seu: 'yangtze', sjtu: 'yangtze', zju: 'yangtze', ustc: 'yangtze', fudan: 'yangtze', tongji: 'yangtze',
    hku: 'hongkong', cuhk: 'hongkong', hkust: 'hongkong', cityu: 'hongkong', polyu: 'hongkong',
    xjtu: 'xian', nwpu: 'xian', xidian: 'xian',
    uestc: 'chengdu', scut: 'guangzhou', hust: 'wuhan'
  };
  const clusterConfig = {
    beijing: { name: '北京', lon: 116.4, lat: 39.9 }, yangtze: { name: '长三角', lon: 119.5, lat: 31.5 },
    hongkong: { name: '香港', lon: 114.2, lat: 21.9 }, xian: { name: '西安', lon: 108.9, lat: 34.3 },
    chengdu: { name: '成都', lon: 104.1, lat: 30.7 }, guangzhou: { name: '广州', lon: 112.7, lat: 24.0 },
    wuhan: { name: '武汉', lon: 113.8, lat: 30.6 }, shenzhen: { name: '深圳', lon: 113.974, lat: 22.591 }, harbin: { name: '哈尔滨', lon: 126.6, lat: 45.8 }
  };
  const node = (tag, className, text) => { const el = document.createElement(tag); if (className) el.className = className; if (text !== undefined && text !== null) el.textContent = String(text); return el; };
  const svgNode = (tag, attributes = {}) => { const el = document.createElementNS(svgNS, tag); Object.entries(attributes).forEach(([key, value]) => el.setAttribute(key, String(value))); return el; };
  const list = value => Array.isArray(value) ? value : value ? [value] : [];
  const displayText = value => { if (value === null || value === undefined) return ''; if (typeof value === 'string' || typeof value === 'number') return String(value); if (Array.isArray(value)) return value.map(displayText).join('\n'); return Object.entries(value).map(([k,v]) => `${k}：${displayText(v)}`).join('\n'); };
  const safeURL = value => { try { const url = new URL(value); return ['http:', 'https:'].includes(url.protocol) ? url.href : null; } catch { return null; } };
  const link = (label, url, className) => { const safe = safeURL(url); const el = node(safe ? 'a' : 'span', className, label); if (safe) { el.href = safe; el.target = '_blank'; el.rel = 'noopener noreferrer'; } return el; };
  const schoolFor = group => state.data.schools.find(school => school.id === group.schoolId);
  const groupsFor = schoolId => state.data.groups.filter(group => group.schoolId === schoolId);
  const revisionFor = group => String(group.revision ?? group.evidenceDate ?? 'baseline-1');
  const logsFor = group => list(group.logs);
  const isBaseline = log => ['baseline', 'initial', '基线', '首版'].includes(log.kind) || log.baseline === true;
  const actualLogs = group => logsFor(group).filter(log => !isBaseline(log));
  const unread = group => state.read[group.id] === undefined ? Boolean(group.updatedThisEdition || actualLogs(group).length || Number(group.revision) > 1) : state.read[group.id] !== revisionFor(group);
  const dateLabel = value => typeof value === 'string' ? value.slice(0, 10) : '';
  const saveRead = () => { try { localStorage.setItem(READ_KEY, JSON.stringify(state.read)); } catch { state.storageEnabled = false; } };
  const loadRead = () => { try { const saved = JSON.parse(localStorage.getItem(READ_KEY) || '{}'); state.read = saved && typeof saved === 'object' && !Array.isArray(saved) ? saved : {}; } catch { state.read = {}; state.storageEnabled = false; } };
  const tagNode = value => node('span', 'tag', value);
  const empty = (title, description, symbol = '⌁') => { const el = node('div', 'empty-state'); el.append(node('span', '', symbol), node('h3', '', title), node('p', '', description)); return el; };
  function toast(message) { const el = $('#toast'); el.textContent = message; el.classList.add('show'); clearTimeout(toast.timer); toast.timer = setTimeout(() => el.classList.remove('show'), 2200); }
  function searchMatches(group) {
    const school = schoolFor(group) || {};
    const text = [group.name, group.tagline, school.name, school.shortName, school.city, ...list(group.topics), ...list(group.leaders).flatMap(leader => [leader.name, leader.en])].join(' ').toLowerCase();
    return !state.search || state.search.toLowerCase().split(/\s+/).every(term => text.includes(term));
  }
  function matches(group, includeSchool = true) {
    return (!includeSchool || !state.selectedSchool || group.schoolId === state.selectedSchool) && (!state.topic || list(group.topics).includes(state.topic)) && (!state.unreadOnly || unread(group)) && searchMatches(group);
  }
  function getClusters() {
    const clusters = new Map();
    state.data.schools.forEach(school => {
      if (!groupsFor(school.id).length) return;
      const city = String(school.city || '');
      const cityKeys = { '北京': 'beijing', '香港': 'hongkong', '西安': 'xian', '成都': 'chengdu', '武汉': 'wuhan', '深圳': 'shenzhen', '广州': 'guangzhou', '哈尔滨': 'harbin', '南京': 'yangtze', '上海': 'yangtze', '杭州': 'yangtze', '合肥': 'yangtze' };
      const key = cityKeys[city] || (city ? city : knownClusters[school.id] || school.id);
      const config = clusterConfig[key] || { name: school.city || school.shortName || school.name };
      const lon = Number(school.lon); const lat = Number(school.lat);
      if (!Number.isFinite(lon) || !Number.isFinite(lat)) return;
      if (!clusters.has(key)) clusters.set(key, { ...config, lon: 0, lat: 0, id: key, schools: [] });
      const cluster = clusters.get(key); cluster.schools.push(school); cluster.lon += lon; cluster.lat += lat;
    });
    return [...clusters.values()].map(cluster => ({ ...cluster, lon: cluster.lon / cluster.schools.length, lat: cluster.lat / cluster.schools.length }));
  }
  const project = (lon, lat) => [100 * (lon - bounds.west) / (bounds.east - bounds.west), 100 * (bounds.north - lat) / (bounds.north - bounds.south)];
  function drawMap() {
    const root = $('#map'); root.replaceChildren();
    const svg = svgNode('svg', { viewBox: '0 0 600 500', class: 'map-svg', 'aria-hidden': 'true' });
    const defs = svgNode('defs'); const clip = svgNode('clipPath', { id: 'map-clip' }); clip.append(svgNode('rect', { width: 600, height: 500 })); defs.append(clip); svg.append(defs);
    [100, 110, 120, 130].forEach(lon => { const [x] = project(lon, 0); svg.append(svgNode('line', { x1: x * 6, y1: 18, x2: x * 6, y2: 482, class: 'grid-line' })); const label = svgNode('text', { x: x * 6 + 4, y: 489, class: 'map-coordinate' }); label.textContent = `${lon}° E`; svg.append(label); });
    [20, 30, 40].forEach(lat => { const [, y] = project(0, lat); svg.append(svgNode('line', { x1: 14, y1: y * 5, x2: 585, y2: y * 5, class: 'grid-line' })); const label = svgNode('text', { x: 7, y: y * 5 - 5, class: 'map-coordinate' }); label.textContent = `${lat}° N`; svg.append(label); });
    if (state.land) {
      const shapes = svgNode('g', { 'clip-path': 'url(#map-clip)' });
      state.land.features.forEach(feature => {
        const polygons = feature.geometry.type === 'Polygon' ? [feature.geometry.coordinates] : feature.geometry.type === 'MultiPolygon' ? feature.geometry.coordinates : [];
        polygons.forEach(polygon => {
          const coordinates = polygon[0];
          if (!coordinates.some(([lon,lat]) => lon >= bounds.west - 20 && lon <= bounds.east + 20 && lat >= bounds.south - 10 && lat <= bounds.north + 10)) return;
          const path = coordinates.map(([lon,lat], i) => { const [x,y] = project(lon,lat); return `${i ? 'L' : 'M'}${(x * 6).toFixed(2)},${(y * 5).toFixed(2)}`; }).join(' ') + ' Z';
          shapes.append(svgNode('path', { d: path, class: 'land' }));
        });
      }); svg.append(shapes);
    }
    root.append(svg, node('div', 'map-water-label', '西太平洋'));
    getClusters().forEach(cluster => {
      const [x,y] = project(cluster.lon,cluster.lat);
      const visibleGroups = cluster.schools.flatMap(school => groupsFor(school.id)).filter(group => matches(group, false));
      const selected = cluster.id === state.selectedCity;
      const button = node('button', `map-pin pin-${cluster.id}${selected ? ' active' : ''}${!visibleGroups.length ? ' muted' : ''}${visibleGroups.some(unread) ? ' unread' : ''}`);
      button.type = 'button'; button.style.left = `${x}%`; button.style.top = `${y}%`;
      button.setAttribute('aria-label', `${cluster.name}，${cluster.schools.length}所学校，${visibleGroups.length}个符合筛选的大组`); button.setAttribute('aria-pressed', String(selected));
      button.append(node('i'), node('b', '', cluster.name)); if (cluster.schools.length > 1) button.append(node('small', '', `${cluster.schools.length}校`));
      button.addEventListener('click', () => selectCity(cluster.id)); root.append(button);
    });
  }
  function selectCity(id) { state.selectedCity = id; const cluster = getClusters().find(item => item.id === id); if (cluster) { const available = cluster.schools.find(school => groupsFor(school.id).some(group => matches(group, false))); if (available) state.selectedSchool = available.id; } render(); }
  function selectSchool(id) { state.selectedSchool = id; state.selectedCity = getClusters().find(cluster => cluster.schools.some(school => school.id === id))?.id || null; render(); }
  function renderSchoolButtons() {
    const index = $('#school-index'); index.replaceChildren();
    const all = node('button', !state.selectedSchool ? 'active' : '', '全部学校'); all.type = 'button'; all.setAttribute('aria-pressed', String(!state.selectedSchool)); all.addEventListener('click', () => { state.selectedSchool = null; state.selectedCity = null; render(); }); index.append(all);
    const visibleSchools = state.data.schools.filter(school => groupsFor(school.id).some(group => matches(group, false)));
    visibleSchools.forEach(school => {
      const count = groupsFor(school.id).filter(group => matches(group, false)).length;
      const button = node('button', school.id === state.selectedSchool ? 'active' : '', school.shortName || school.name); button.type = 'button'; button.setAttribute('aria-pressed', String(school.id === state.selectedSchool)); button.title = school.name;
      button.append(node('small', '', count)); if (groupsFor(school.id).filter(group => matches(group, false)).some(unread)) { const dot = node('span', 'small-dot'); dot.setAttribute('aria-label', '有未读更新'); button.append(dot); }
      button.addEventListener('click', () => selectSchool(school.id)); index.append(button);
    });
    $('#school-visible-count').textContent = `${visibleSchools.length} 所`;
    const cityRoot = $('#city-schools'); cityRoot.replaceChildren();
    const cluster = getClusters().find(item => item.id === state.selectedCity);
    if (!cluster) return;
    const label = node('div', 'city-label'); label.append(node('span', '', `${cluster.name} · 选择学校`), node('span', '', `${cluster.schools.length} 所已收录`));
    const buttons = node('div', 'city-school-buttons');
    cluster.schools.forEach(school => { const button = node('button', school.id === state.selectedSchool ? 'active' : '', school.name); button.type = 'button'; button.setAttribute('aria-pressed', String(school.id === state.selectedSchool)); button.addEventListener('click', () => selectSchool(school.id)); buttons.append(button); });
    cityRoot.append(label, buttons);
  }
  function renderGroupList() {
    const root = $('#group-list'); root.replaceChildren();
    const school = state.data.schools.find(item => item.id === state.selectedSchool);
    const groups = state.data.groups.filter(group => matches(group));
    $('#selected-school-overline').textContent = school ? [school.region, school.city].filter(Boolean).join(' / ') : '精选研究档案';
    $('#groups-title').textContent = school ? school.name : state.search ? '搜索结果' : state.unreadOnly ? '尚未读过的更新' : state.topic ? `${state.topic}方向` : '全部精选大组';
    $('#groups-subtitle').textContent = school ? `${school.shortName || school.name}的通信研究脉络 · 点开组档案深入查看` : '先读研究主线，再按需展开论文与原始证据。';
    $('#visible-groups').textContent = `${groups.length} 个组`;
    if (!groups.length) { root.append(empty(state.unreadOnly ? '已读完所有符合条件的更新' : '没有符合条件的大组', state.unreadOnly ? '首版用于建立研究基线。新的核实更新会在组名旁出现红点。' : '尝试换一个方向，或重置筛选查看精选名单。', '✓')); return; }
    groups.forEach(group => {
      const card = node('button', 'group-card'); card.type = 'button'; card.setAttribute('aria-label', `${group.name}，${schoolFor(group)?.name || ''}${unread(group) ? '，有未读核实更新' : ''}，查看研究档案`);
      const overline = node('div', 'card-overline'); overline.append(node('span', '', schoolFor(group)?.name || '研究档案')); if (group.updatedThisEdition) overline.append(node('span', 'edition-badge', '本轮更新')); else overline.append(node('span', '', '精选档案'));
      const title = node('h3', '', group.name); if (unread(group)) { const dot = node('span', 'small-dot'); dot.setAttribute('aria-label', '未读更新'); title.append(dot); }
      const tags = node('div', 'tags'); list(group.topics).slice(0,4).forEach(topic => tags.append(tagNode(topic)));
      card.append(overline,title,node('p','tagline',group.tagline || displayText(group.current)),tags,node('span','card-arrow','↗')); card.addEventListener('click',() => openGroup(group)); root.append(card);
    });
  }
  function allLogs() { return state.data.groups.flatMap(group => logsFor(group).map(log => ({ ...log, group }))).sort((a,b) => String(b.date || '').localeCompare(String(a.date || ''))); }
  function logEntry(log, includeGroup = true) {
    const root = node('article','log-entry'); const date = node('div','log-date',dateLabel(log.date)); date.append(node('span','log-type',isBaseline(log) ? '首版基线' : log.kind === 'direction' ? '方向更新' : '核实更新')); root.append(date);
    root.append(node('h3','',log.title || (isBaseline(log) ? '建立研究主线档案' : '研究档案更新')));
    if (includeGroup && log.group) { const button = node('button','log-group-link',`${schoolFor(log.group)?.shortName || ''} · ${log.group.name} ↗`); button.type='button'; button.addEventListener('click',()=>openGroup(log.group)); root.append(button); }
    root.append(node('p','',displayText(log.summary || log.content)));
    if (list(log.sources).length) { const sources = node('div','log-sources'); list(log.sources).forEach((source,i)=>{ if(i) sources.append(document.createTextNode(' · ')); sources.append(link(typeof source === 'string' ? '原始来源' : source.title || '原始来源', typeof source === 'string' ? source : source.url)); }); root.append(sources); }
    return root;
  }
  function renderUpdates() {
    const root = $('#updates-feed'); root.replaceChildren();
    const logs = allLogs().filter(log => !isBaseline(log));
    $('#verified-total').textContent = logs.length;
    $('#change-count').textContent = logs.length ? String(logs.length) : '';
    if (!logs.length) root.append(empty('研究基线已建立，等待第一条核实更新', '首版不把已有成果包装成新动态。后续只有核实后的新论文、研究主线变化或重要团队进展，才会进入这里。'));
    else logs.forEach(log => root.append(logEntry(log)));
    const candidates = state.papers.filter(paper => paper.candidateStatus === 'pending' || !paper.candidateStatus);
    $('#candidate-count').textContent = `${candidates.length} 篇`;
    const candidateRoot = $('#candidate-list'); candidateRoot.replaceChildren();
    if (!candidates.length) candidateRoot.append(node('p','baseline-note','暂无待核实候选。采集无结果、尚未运行与网络失败会在采集状态中分别显示。'));
    candidates.slice().sort((a,b)=>String(b.published||'').localeCompare(String(a.published||''))).slice(0,50).forEach(paper => {
      const card = node('article','candidate-card'); card.append(node('h4','',paper.title)); const groupNames = list(paper.groupIds).map(id => state.data.groups.find(group=>group.id===id)?.name).filter(Boolean);
      card.append(node('p','',[dateLabel(paper.published),groupNames.join('、'),'待核实归属与贡献'].filter(Boolean).join(' · '))); card.append(link('查看 arXiv 原文 ↗',paper.url)); candidateRoot.append(card);
    });
    if(candidates.length > 50) candidateRoot.append(node('p','muted',`页面仅展示最近50篇；全部${candidates.length}篇保留在数据文件中。`));
  }
  function detailsSection(title, content, label) {
    const section = node('section','detail-section'); const heading=node('h3','',title); if(label) heading.append(node('span','',label)); section.append(heading,node('p','',displayText(content) || '暂无充分证据，待核实后补充。')); return section;
  }
  function sourceList(sources, papers = false) {
    const root = node('ul',`source-list${papers ? ' paper-list' : ''}`);
    list(sources).forEach(source => { const item = node('li'); item.append(link(source.title || source.url || '原始来源',source.url)); if(source.note || source.date) item.append(node('p','',[dateLabel(source.date),displayText(source.note)].filter(Boolean).join(' · '))); root.append(item); });
    if(!root.children.length) root.append(node('li','','暂无可展示的原始链接。'));
    return root;
  }
  function openGroup(group, updateHash = true) {
    const wasUnread = unread(group); state.read[group.id] = revisionFor(group); saveRead();
    const root = $('#group-detail'); root.replaceChildren(); const school=schoolFor(group)||{};
    const header = node('div','detail-header'); header.append(node('p','eyebrow',[school.name,school.city].filter(Boolean).join(' / ')),node('h2','',group.name)); $('#detail-title')?.removeAttribute('id'); $('h2',header).id='detail-title'; header.append(node('p','detail-tagline',group.tagline));
    const tags=node('div','detail-tags');list(group.topics).forEach(topic=>tags.append(tagNode(topic)));header.append(tags);
    const leaders=node('p','detail-leaders'); leaders.append(document.createTextNode('主要负责人  '),node('strong','',list(group.leaders).map(leader=>[leader.name,leader.en].filter(Boolean).join(' / ')).join('；'))); header.append(leaders);
    const body=node('div','detail-body'); body.append(node('p','detail-summary',displayText(group.whyFollow)));
    body.append(detailsSection('过去积累',group.past,'FOUNDATION'), detailsSection('当前在做什么',group.current,'OBSERVED'));
    const next=detailsSection('下一步看什么',group.next,'WATCH');next.classList.add('next-question');next.append(node('p','note','这是基于现有证据提出的跟踪问题，不代表团队已公布的未来计划。'));body.append(next);
    const logDetails=node('details','detail-collapsible'); const logSummary=node('summary','','组内研究日志');logSummary.append(node('small','',`${actualLogs(group).length} 条核实更新`));logDetails.append(logSummary);
    const logs=logsFor(group);if(logs.length) logs.slice().sort((a,b)=>String(b.date||'').localeCompare(String(a.date||''))).forEach(log=>logDetails.append(logEntry(log,false)));else logDetails.append(node('p','baseline-note','本组已建立首版研究基线，目前没有新增核实动态。'));
    const paperDetails=node('details','detail-collapsible');const paperSummary=node('summary','','代表论文与近期证据');paperSummary.append(node('small','',`${list(group.papers).length} 项`));paperDetails.append(paperSummary,sourceList(group.papers,true));
    const sources=node('details','detail-collapsible');const sourceSummary=node('summary','','入选依据与原始来源');sourceSummary.append(node('small','',`${list(group.sources).length} 项`));sources.append(sourceSummary,sourceList(group.sources));
    const pending=state.papers.filter(paper=>list(paper.groupIds).includes(group.id)&&(paper.candidateStatus==='pending'||!paper.candidateStatus));
    body.append(logDetails,paperDetails,sources);
    if(pending.length) {const note=node('p','confidence-note',`${pending.length}篇arXiv论文处于候选池，尚未核实。请在“更新日志”查看，不作为本组方向结论。`);body.append(note);}
    body.append(node('p','confidence-note',[`证据核对：${dateLabel(group.evidenceDate) || '以来源日期为准'}`,displayText(group.confidence)].filter(Boolean).join(' · ')));
    root.append(header,body);const dialog=$('#group-dialog');if(!dialog.open) dialog.showModal();dialog.scrollTop=0;
    if(updateHash) history.replaceState(null,'',`#group=${encodeURIComponent(group.id)}`);
    render();if(wasUnread) toast(state.storageEnabled ? '已读状态已保存在本设备' : '已标为已读；当前浏览器无法持久保存阅读状态');
  }
  function closeDialog() { const dialog=$('#group-dialog');dialog.close();if(location.hash.startsWith('#group='))history.replaceState(null,'',location.pathname+location.search); }
  function renderStatus() {
    const el=$('#collection-status');el.classList.remove('error');const status=state.status;const editorial=state.editorialStatus;$('#editorial-status').textContent=editorial?.lastReviewAt?`编辑核对：${dateLabel(editorial.lastReviewAt)}`:'编辑核对日期见组内证据';$('#pipeline-status').textContent=[editorial?.lastReviewAt?`编辑审阅：${dateLabel(editorial.lastReviewAt)}`:'',editorial?.summary||'',status?.lastAttemptAt?`采集尝试：${dateLabel(status.lastAttemptAt)}`:'自动采集尚无运行记录',status?.state==='error'?'采集失败，保留旧数据':status?.state==='partial'?'采集不完整（失败或窗口截断）':status?.state==='ok'?'采集完成，候选仍待核实':''].filter(Boolean).join(' · ');
    if(!status) {el.textContent='自动采集尚无运行记录';return;}
    const last=status.lastSuccessAt?dateLabel(status.lastSuccessAt):'';
    if(status.state==='error') {el.textContent=`最近采集失败${last?` · 保留${last}数据`:''}`;el.classList.add('error');}
    else if(status.state==='partial') {el.textContent=`采集不完整（失败或窗口截断）${last?` · 上次成功${last}`:''}`;el.classList.add('error');}
    else if(status.state==='ok') el.textContent=`采集检查：${dateLabel(status.lastAttemptAt)||last||'已有运行记录'} · 候选待核实`;
    else el.textContent='自动采集尚无成功运行记录';
  }
  function render() {if(!state.data)return;drawMap();renderSchoolButtons();renderGroupList();renderUpdates();}
  function buildTopicFilters() {
    if(!state.data)return;
    const root=$('#topic-filters');root.replaceChildren();const counts=new Map();state.data.groups.forEach(group=>list(group.topics).forEach(topic=>counts.set(topic,(counts.get(topic)||0)+1)));
    const topics=['',...Array.from(counts).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],'zh-CN')).map(([topic])=>topic)];
    topics.forEach(topic=>{const button=node('button',`topic-chip${state.topic===topic?' active':''}`,topic||'全部');button.type='button';button.setAttribute('aria-pressed',String(state.topic===topic));button.addEventListener('click',()=>{state.topic=topic;state.selectedSchool=null;state.selectedCity=null;buildTopicFilters();render();});root.append(button);});
  }
  function switchView(view) {state.view=view;$$('.nav-item').forEach(button=>{const selected=button.dataset.view===view;button.classList.toggle('active',selected);button.setAttribute('aria-current',selected?'page':'false');});['atlas','changes','method'].forEach(id=>{const el=$(`#${id}-view`);el.hidden=id!==view;el.classList.toggle('active',id===view);});}
  async function optionalJSON(path) {try{const response=await fetch(path,{cache:'no-cache'});if(!response.ok)return null;return await response.json();}catch{return null;}}
  async function load() {
    $('#load-error').hidden=true;
    try {
      const response=await fetch('data/groups.json',{cache:'no-cache'});if(!response.ok)throw new Error('Missing research data');const data=await response.json();if(!Array.isArray(data.groups)||!Array.isArray(data.schools))throw new Error('Invalid research schema');state.data=data;
      const [papers,status,land,editorial]=await Promise.all([optionalJSON('data/papers.json'),optionalJSON('data/status.json'),optionalJSON('assets/land.geojson'),optionalJSON('data/editorial-status.json')]);state.papers=Array.isArray(papers?.papers)?papers.papers:[];state.status=status;state.land=land;state.editorialStatus=editorial;
      loadRead();data.groups.forEach(group=>{if(state.read[group.id]===undefined&&!group.updatedThisEdition&&!actualLogs(group).length&&!(Number(group.revision)>1))state.read[group.id]=revisionFor(group);});saveRead();
      state.selectedSchool=state.search||state.topic||state.unreadOnly?null:data.schools.find(school=>groupsFor(school.id).length)?.id||null;state.selectedCity=getClusters().find(cluster=>cluster.schools.some(school=>school.id===state.selectedSchool))?.id||null;
      $('#school-total').textContent=data.schools.filter(school=>groupsFor(school.id).length).length;$('#group-total').textContent=data.groups.length;
      const edition=data.edition;$('#edition').textContent=typeof edition==='object'?(dateLabel(edition?.date||edition?.publishedAt)||edition?.label||'首版基线'):String(edition||data.updatedAt||data.version||'首版基线');
      if(data.repositoryUrl&&safeURL(data.repositoryUrl))$('#github-link').href=safeURL(data.repositoryUrl);
      buildTopicFilters();renderStatus();render();
      if(location.hash.startsWith('#group=')){const id=decodeURIComponent(location.hash.slice(7));const group=data.groups.find(item=>item.id===id);if(group)openGroup(group,false);}
    }catch(error){$('#load-error').hidden=false;$('#atlas-view').hidden=true;$('#edition').textContent='待载入';console.error('研究档案读取失败',error);}
  }
  $('#search').addEventListener('input',event=>{state.search=event.target.value.trim();state.selectedSchool=null;state.selectedCity=null;render();});
  $('#unread-only').addEventListener('change',event=>{state.unreadOnly=event.target.checked;state.selectedSchool=null;state.selectedCity=null;render();});
  $('#reset-filters').addEventListener('click',()=>{state.search='';state.topic='';state.unreadOnly=false;state.selectedSchool=null;state.selectedCity=null;$('#search').value='';$('#unread-only').checked=false;buildTopicFilters();render();});
  $$('.nav-item').forEach(button=>button.addEventListener('click',()=>switchView(button.dataset.view)));
  $('#close-dialog').addEventListener('click',closeDialog);$('#group-dialog').addEventListener('click',event=>{if(event.target===$('#group-dialog')){const rect=event.target.getBoundingClientRect();if(event.clientX<rect.left||event.clientX>rect.right||event.clientY<rect.top||event.clientY>rect.bottom)closeDialog();}});
  $('#group-dialog').addEventListener('cancel',()=>{if(location.hash.startsWith('#group='))history.replaceState(null,'',location.pathname+location.search);});
  $('#retry-load').addEventListener('click',()=>{switchView('atlas');load();});
  document.addEventListener('keydown',event=>{if(event.key==='/'&&!['INPUT','TEXTAREA'].includes(document.activeElement?.tagName)&&!$('#group-dialog').open){event.preventDefault();switchView('atlas');$('#search').focus();}});
  window.addEventListener('storage',event=>{if(event.key===READ_KEY&&state.data){loadRead();render();}});
  load();
})();
