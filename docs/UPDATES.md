# 更新、证据与采集健康

## 两条互补的更新路径

1. GitHub Actions 在每周三、周六北京时间 08:17 请求 arXiv Atom API，把候选论文和采集健康提交回仓库，再部署 Pages。GitHub 的定时工作可能延迟；没有精确到分钟的执行保证。公开仓库长期无活动时 GitHub 可能暂停定时工作，应留意 Actions 状态。
2. 定时研究审阅任务核对团队官网、论文作者单位和论文内容，把值得关注的变化追加到 `data/groups.json` 各组的 `logs`，并更新组简介。方向判断必须附原始来源。`data/updates.json` 可作更新索引，首版为空数组；它不是日志的权威存储。采集脚本绝不修改这两个文件。

`authorQueries` 是英文完整姓名白名单，不是唯一身份标识。即使全名精确命中，仍可能同名、换单位、只有合作关系。所有机器收集条目固定为 `candidateStatus: "pending"`，不能凭姓名命中就变成组进展。标题关键词门槛也会漏掉边缘方向，所以官网与人工检索仍是补充。arXiv 是预印本来源，不等于同行评审结论，也不覆盖未上传 arXiv 的工作。

首次成功抓取建立各组自己的基线，不把历史存量当作新增。之后的新 ID 标记 `new`，同一 ID 的更高版本标记 `revision`；不会把 v1/v2 当成两篇论文。跨组共同署名的候选只存一条，分别记录匹配线索。相同版本重复采集保留 `verified` / `rejected` 状态、`reviewNote`、`reviewedAt` 等编辑字段。版本更新会重新进入待审阅，把旧稿审阅移入 `previousReview` / `previousReviews`，清除新稿的当前审阅字段，但不自动创建日志或红点。

## 公开数据契约

- `groups.json`：数组或 `{ "groups": [...] }`，每组至少 `id` 和 `authorQueries: ["Full Name"]`。
- `papers.json`：`{schemaVersion, baselineEstablishedAt, groupBaselines, papers}`。条目含 `id`（不带 v）、`version`、`versions`、标题、时间、完整作者、摘要、`groupIds`、`matchEvidence`、`candidateStatus`、`changeType`、首次/最后观察时间。`groupIds` 只表示待核实的作者匹配，不表示已确认团队归属。
- `groups.json` 的 `logs`：权威编辑日志，由研究任务追加；首次条目是 `baseline`。研究任务执行 `python scripts/release.py --against HEAD` 自动计算 `revision`、`updatedThisEdition` 与 `edition`；红点只看已核实、非基线的实质变化。`updatedThisEdition` 表示本轮有变化，本设备是否未读由 localStorage 中的组 `revision` 判断。
- `updates.json`：可选更新索引，首版为空数组；不替代组内 `logs`，界面以组档案为准。
- `status.json`：`state` 是 `not_started`（尚未采集）、`ok`、`partial` 或 `error`。含本次尝试、上次完整近期窗口成功与逐组上次成功时间，以及 `sourceTotalResults`、`historicalResultsTruncated`、`windowCutoff`、`windowComplete`。`ok` 仅指近期窗口，不表示抓取了作者全部历史论文。失败不能解释成“没有新论文”。

采集窗口默认最近 45 天，按 `lastUpdatedDate` 排序后在客户端筛选更新时间，单组最多返回 80 条；每个请求至少间隔 3.1 秒，失败最多尝试三次。连续三组失败后暂停其余请求，避免上游故障时长时间无效重试。若全部返回记录仍在窗口内且达到上限，健康状态会标记 `partial` 提醒补查。脚本不会声称穷尽所有论文。抓取失败保留旧候选与原有成功时间，总失败时候选文件逐字节保持不变，仍发布错误状态以便发现。JSON 原子替换防止半写入。没有 API key 或付费模型依赖。接口格式和节流依据 [arXiv 官方 API 手册](https://info.arxiv.org/help/api/user-manual.html) 与 [API 使用条款](https://info.arxiv.org/help/api/tou.html)。

## 本地操作

```bash
python -m unittest discover -s tests -v
python scripts/collect_arxiv.py
python scripts/build_site.py
```

离线执行使用 `--fixture path.json`。Fixture 结构为 `{"now":"...Z","results":{"group-id":{"xml":"<feed ...>...</feed>"},"other-id":{"error":"timeout"}}}`，不会发出网络请求。不要把测试候选提交到生产 `data/`。

Pages 的 Source 需设为 GitHub Actions。Workflow 权限按作业收窄：采集作业只有仓库内容写入；发布作业只有内容读取、Pages 写入和 OIDC。不会打包 `.git`、脚本、研究草稿或凭据；公共构建白名单是 `index.html`、`styles.css`、`app.js`、`assets/` 与 `data/`。

## 参考工具的取舍

已核对 [arxiv-sanity-lite](https://github.com/karpathy/arxiv-sanity-lite) 的官方 README：适合对论文打标签和用 TF-IDF/SVM 推荐，需要定期计算、持久数据库与 Flask 服务。这里的核心是学校—组的证据归纳，且要求 GitHub Pages 静态发布，因此没有直接搬入这套服务。

也核对 [cv-arxiv-daily](https://github.com/Vincentqyw/cv-arxiv-daily)：它演示了 GitHub Actions 定时收集与按主题归档的可行路径。本项目采用同类部署方式，但独立编写了标准库采集器，增加英文全名白名单、版本去重、逐组基线、采集失败保留、待核实状态与独立编辑日志。未复制这两个仓库的代码或资产。
