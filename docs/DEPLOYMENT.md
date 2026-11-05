# GitHub Pages 首次开通

代码和构建工作流已经存在。仓库的 Pages 服务需先开通，单纯推送代码不会开启账号设置。

1. 打开 <https://github.com/hongjinrui/To-Know-Communication-Groups/settings/pages>。
2. 将 **Build and deployment → Source** 选择为 **GitHub Actions**。
3. 在 Actions 重跑最新失败的发布工作流；之后每次 main 更新以及周三/六的采集工作流会发布。
4. 以 Actions 返回的成功 URL 为上线依据，预期地址是 <https://hongjinrui.github.io/To-Know-Communication-Groups/>。

2026-11-05 首次运行的源码检出、Python准备、公开构建均通过；configure-pages 返回 Pages site Not Found。已连接的 GitHub 工具可以写仓库内容及查看 Actions，但不提供 Pages 管理设置，不能代替这个首次设置。

`offline.html` 是首版单文件快照，下载后可直接在浏览器打开，无需本机服务器。后续数据更新以正式站点和 data/ 为准，快照不会自动同步。其海陆轮廓许可与主站相同。
