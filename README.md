# CV Editor — AI-Powered LaTeX Resume Customizer

针对每个 JD 自动定制你的 LaTeX 简历，下载后直接上传 Overleaf 编译导出 PDF。

## 功能

- 上传 `.tex` 简历或直接粘贴 LaTeX 代码
- 粘贴目标岗位 JD，AI 自动完成关键词匹配、内容排序、描述优化
- 生成改动摘要，清楚知道改了什么
- 历史记录保留最近 5 次生成结果，可随时重新下载
- 支持 DeepSeek Chat / Reasoner 两个模型

## 使用方法

```bash
# 1. 安装依赖
pip install -r requirements_resume.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 DeepSeek API Key

# 3. 启动
streamlit run resume_app.py
```

也可以在侧边栏直接输入 API Key，无需配置文件。

## 使用流程

1. 左侧上传或粘贴你的基础 `.tex` 简历（建议保留一份母版）
2. 填写目标公司/岗位名称
3. 粘贴完整 JD
4. 点击「生成定制简历」→ 下载 `.tex`
5. 上传至 [Overleaf](https://overleaf.com) 编译 → 导出 PDF

## 注意事项

- AI 只调整已有内容，不会编造新经历
- 建议 Temperature 保持 0.1~0.3，避免过度改写
- API Key 请勿提交到代码仓库
