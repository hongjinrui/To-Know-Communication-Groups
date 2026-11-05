# 独立证据复核（2026-11-05）

复核范围：`mainland-a.json` 的3篇及 `hk.json` 的3篇独立论文；逐一打开 arXiv 原始摘要页，并进一步检查全文作者单位。另检查两份文件中的研究计划、团队边界和规模表述。此为抽查，不代表其余论文、奖项和历史成果均已独立复验。

## 结论

六篇抽查论文的 arXiv ID、摘要页标题、完整作者顺序及首次提交日期均与JSON相符，未发现同名错归、虚构论文或把预印本写成已完成系统的阻断问题。未来部分均使用“跟踪/关注”观察问题，未发现应改为已宣布计划的情况。

## 六篇论文逐项结果

| 文件/组 | 原始来源 | 核对结果与单位证据 |
| --- | --- | --- |
| mainland-a / 戴凌龙组 | [2607.29341](https://arxiv.org/abs/2607.29341)、[v1全文](https://arxiv.org/html/2607.29341v1) | 标题、Mingyuan Zhou / Zhuo Xu / Linglong Dai及2026-07-31均匹配。全文作者均列清华电子系及清华空间网络与通信全国重点实验室。论文为理论及仿真工作；JSON未把这一篇误写成原型实验。 |
| mainland-a / 金石组 | [2605.19849](https://arxiv.org/abs/2605.19849)、[v1全文](https://arxiv.org/html/2605.19849v1) | SPA-MAE标题、全部5位作者顺序及2026-05-19均匹配。全文全部作者列东南大学信息科学与工程学院。物理先验与多径参数概述准确。 |
| mainland-a / 张朝阳组 | [2610.34135](https://arxiv.org/abs/2610.34135)、[v1全文](https://arxiv.org/html/2610.34135v1) | ID、全部4位作者顺序及2026-10-25均匹配。全文明确浙江大学信电学院，排除了仅靠Zhaoyang Zhang同名匹配。摘要页标题为Environment-Adaptive Dynamic KV Cache…，全文题名为Environment-Conditioned Dynamic KV Caching…；JSON采用摘要页标准题名是合理的。 |
| hk / 黄凯斌组 | [2609.01062](https://arxiv.org/abs/2609.01062)、[v1全文](https://arxiv.org/html/2609.01062v1) | 标题、全部4位作者顺序及2026-09-01均匹配。全文4人均为港大，K. Huang为通讯作者。正文为太阳能轨道模型约束下的计算通信联合优化，不是已经上星部署；JSON只标预印本和跟踪问题。 |
| hk / 李德富组、张军组合作 | [2609.39964](https://arxiv.org/abs/2609.39964)、[v2全文](https://arxiv.org/html/2609.39964v2) | AIMS标题、全部7位作者、2026-09-30首发和2026-10-01修订均匹配。全文均列HKUST清水湾ECE，排除港科大广州。本文可在两组出现，但只能算一项跨组合作成果，不能累计为两篇独立论文。 |
| hk / 穆乐思组合作 | [2511.21274](https://arxiv.org/abs/2511.21274)、[v3全文](https://arxiv.org/html/2511.21274v3) | MAPES摘要页题名、全部9位作者顺序和2025-11-26首发均匹配。v3于2026-06-29更新；全文明确主要作者及Ross Murch为HKUST，同时有NTU、ETH合作作者，不能据此合并合作方团队。 |

## 建议的小修正（均不阻断发布）

1. **补齐MAPES版本与期刊来源。** `hkust-murch.papers[0]` 可补 `updated: "2026-06-29"`。原文已于2026-08-26在线发表于TMTT，10月卷期为74(10):8692–8705。建议sources补[港科大机构成果记录](https://researchportal.hkust.edu.hk/en/publications/multiport-analytical-pixel-electromagnetic-simulator-mapes-for-ai/)或[IEEE出版记录](https://ieeexplore.ieee.org/abstract/document/11665549/)，DOI为 `10.1109/TMTT.2026.3723770`。当前“对应2026 TMTT期刊成果”事实正确，但加直接来源可降低追溯成本。

2. **明确摘要页与全文题名差异不触发新动态。** 2610.34135和2511.21274存在标题词序/措辞差异，ID和作者一致。采集器应依去版本arXiv ID去重，不应因页面题名差异生成第二篇或红点。

3. **AIMS跨组重复展示应去重统计。** 李德富组与张军组均参与，分别放入组内日志合理；如首页有“本轮新增论文数”，按arXiv ID统一去重。它体现合作动向，不能单凭同一篇宣称两个团队均整体转向智能体。

4. **规模证据避免精确现时化。** NIULAB来源note写2名faculty、11名博士、5名硕士，但正文whyFollow没有强行使用人数，这样较稳妥。浙大团队名单已明确是2021快照；应保留此限定。港理工刘亮组已明确成熟梯队而非国家级平台规模，应保留限定。没有发现需要删除的夸大规模数字。

## 姓名与组边界复核

- 黄凯斌中文名有[港大2026官方报道](https://www.keynotes.hku.hk/sc/story/croucher-senior-research-fellowship-2026/)直接支持，应保留“凯”，不要凭惯常记忆改为“锴”。
- [Wireless@HKU人员页](https://wireless.hku.hk/people)明确Group Leader、RAP、博士后和博士生；抽查论文中的Jierui Zhang、Jianhao Huang、Zhanwei Wang均能与该页队伍对应，不只是导师署名推定。
- [张军当前主页](https://eejzhang.people.ust.hk/)有2026博士培养、独立Group入口与通信/AI研究动态，支持其作为持续团队入口；与李德富存在合作不要求合并为同一个组。
- 6G@HK为跨校协作项目，现有JSON已明确“不与李德富个人组等同”，应保留；不把项目全部faculty收入其组。
- 尤肖虎组已对大平台合作及单篇无法证明全组转向作限定；陶梅霞组未穷举人员边界也已如实说明。它们是影响力判断与方向追踪入口，不应让UI把confidence缩成无条件的“全部已核实”。

## 未来方向表述

当前next均是可检验的问题，例如跨场景泛化、真实链路/能耗验证、实测信道及硬件约束；不是捏造将开展的项目。建议UI标题沿用“接下来关注什么”或“跟踪问题”，避免渲染为“团队未来计划”。如列在研项目，应保留具体项目年份与官方来源，与编辑观察分开。
