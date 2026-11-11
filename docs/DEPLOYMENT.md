# GitHub Pages 部署

本站已开通 GitHub Pages，在线地址为 <https://hongjinrui.github.io/To-Know-Communication-Groups/>。`main` 更新会由 [发布工作流](https://github.com/hongjinrui/To-Know-Communication-Groups/actions/workflows/atlas.yml) 自动构建并部署；周三/六的采集工作流完成后也会发布。

2026-11-11 已核实 [发布运行 #7](https://github.com/hongjinrui/To-Know-Communication-Groups/actions/runs/42948654451) 的 Pages 配置、产物上传和部署步骤均成功，返回的站点地址与上述地址一致。

## 新仓库首次开通

以下步骤供迁移或重新建仓时参考，当前仓库无需重复开通。仓库的 Pages 服务需先启用，单纯推送代码不会开启账号设置。

1. 打开 <https://github.com/hongjinrui/To-Know-Communication-Groups/settings/pages>。
2. 将 **Build and deployment → Source** 选择为 **GitHub Actions**。
3. 在 Actions 重跑最新失败的发布工作流；之后每次 main 更新以及周三/六的采集工作流会发布。
4. 以 Actions 返回的成功 URL 为上线依据，预期地址是 <https://hongjinrui.github.io/To-Know-Communication-Groups/>。

历史记录：2026-11-05 首次运行的源码检出、Python准备、公开构建均通过；configure-pages 曾返回 Pages site Not Found。后续成功部署已表明该首次开通问题解决。

`offline.html` 是首版单文件快照，下载后可直接在浏览器打开，无需本机服务器。后续数据更新以正式站点和 data/ 为准，快照不会自动同步。其海陆轮廓许可与主站相同。
