# 通信大组地图：长期维护约定

用户已授权直接向 hongjinrui/To-Know-Communication-Groups 提交并发布，无须再次征求发布许可。请维护现有仓库，不另建站点。所有任务均以当前远端内容为准，勿用会话缓存覆盖别人的修改。

## 研究编辑

- 范围：内地39所985、用户特例加入的北邮与西电、以及香港五校（HKU/CUHK/HKUST/CityU/PolyU），以通信工程为主。校区要说明；港中文深圳、港科大广州不作为香港校区团队纳入。未入选不代表质量低。
- 关注持续团队及研究路线，禁止批量收录所有教师。每次新增必须有团队存在、影响力、近期活跃三类依据，单凭论文数、Fellow、引用量不够。
- 优先学校及实验室官网、原始论文、官方奖项/项目。联网核对现任归属。记录来源与可证日期，不把搜索抓取时间当发表时间。
- arXiv 中姓名匹配只意味着候选。须通过论文单位、团队官网论文列表或可信核心合作者核实；合作论文不自动说明整个组改变路线。
- `past` 是已发生主线；`current` 是公开成果所反映的方向；`next` 是编辑提出的跟踪问题，不能冒充已公开的未来计划。
- `whyFollow` 必须给可查事实及来源。方向推断要说清依据及限度。只保留高密度短摘要，避免堆论文。
- 每组的 `sources`、`papers` 及 `logs` 保留出处。日志追加、不可改写旧记录来伪造历史。重大成果、路线变化、团队迁移、开放代码/测试平台优先；普通新论文不必每篇都写日志。

## 每轮更新

1. `git fetch origin main`，从最新远端开始。检查 `data/status.json` 与 `data/papers.json`，自动采集失败时可用已授权的网页搜索查证；失败不等于没有成果。
2. 核实上轮之后的新成果；读取原论文，判断实际新增了什么。对同名及归属不明条目保持 pending，不得硬归组。
3. 有实质变化才改组档案、追加一条短日志：`{date,title,summary,kind:'verified',sources:[{title,url}]}`，必要时保留论文的版本与原始日期。
4. 核实候选可将其 candidateStatus 置为 verified / rejected，并写 reviewNote 与 reviewedAt。采集器必须保留这些编辑字段。
5. `python3 scripts/release.py --against HEAD` 自动计算 revision、updatedThisEdition、edition，清除上轮红点但保留日志和未读revision。没有实质变化的组不得增加revision。
6. 执行 `python3 -m unittest discover -s tests -v`、`node --check app.js`、`python3 scripts/build_site.py`，检查来源、筛选、地图、红点及空态。提交推送 main，确认 Actions 发布结果。不可宣称未经确认的上线成功。
7. 更新 `data/editorial-status.json` 的 lastReviewAt/state/summary（如存在），没有变化也记录已检查与覆盖限度；不要为打红点而改正文。

第一次发布全部 baseline，revision=1，无新增红点。本轮变化（updatedThisEdition）和本设备未读（localStorage revision）是不同概念，保持明确。读取组详情清除本设备未读；本轮标记持续到下次编辑版本。

## 技术

纯静态HTML/JS/CSS，部署GitHub Pages。浏览器不调用私钥或LLM API，不引入需要长期维护的后端。自动采集仅抓候选；定时研究任务负责证据归纳。更新 cadence 以 Asia/Shanghai 周三/周六为准，Actions及定时任务可能排队。网络错误保留旧数据并显示失败。
