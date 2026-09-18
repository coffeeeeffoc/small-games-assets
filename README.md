# 素材物料

按主题保存可编辑源文件、运行时模型、预览与制作脚本。

- [`bund/`](bund/README.md)：外滩滨江环境，Blender 源文件、独立 GLB 配件与组合场景。
- [`english-dict/`](english-dict/README.md)：独立 Git submodule，保存英语词库、教材词表及原始素材。应用读取 `english-dict/精简词库/英语词库.sqlite`，按需在构建时导出词表 JSON；`完整素材/` 用于追溯和重建，不进入应用包。

在 `small-games` 根目录运行 `git submodule update --init --recursive assets`，可一并获取素材与词库的锁定版本。

游戏直接引用本子仓库中的资源目录；不要把模型再复制并提交到各游戏的 `public/`。外滩 Web 运行资源位于 `bund/runtime/`，Vite 可将它设为 `publicDir`，开发时直接读取，发布时只打包到构建产物。源文件与预览不进入游戏包。
