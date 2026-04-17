import streamlit as st
from openai import OpenAI
import os
import re
from datetime import datetime
from dotenv import load_dotenv

# 优先加载 ds_api.env，其次 .env
load_dotenv("ds_api.env")
load_dotenv(".env")

st.set_page_config(
    page_title="简历定制助手",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-title { font-size: 2rem; font-weight: 700; margin-bottom: 0.2rem; }
    .subtitle { color: #888; margin-bottom: 1.5rem; }
    .change-item { padding: 0.3rem 0; border-bottom: 1px solid #f0f0f0; }
    .stButton > button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# ── 侧边栏 ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 设置")

    api_key = st.text_input(
        "DeepSeek API Key",
        type="password",
        value=os.getenv("DEEPSEEK_API_KEY", ""),
        placeholder="sk-..."
    )

    model = st.selectbox(
        "模型",
        ["deepseek-chat", "deepseek-reasoner"],
        help="deepseek-chat 速度更快；deepseek-reasoner 推理更深入"
    )

    temperature = st.slider(
        "创意度（Temperature）",
        min_value=0.0, max_value=1.0, value=0.2, step=0.05,
        help="越低越保守，越高越有创意。建议保持 0.1~0.3"
    )

    st.divider()
    st.markdown("## 📋 基础简历")

    upload_mode = st.radio("上传方式", ["上传 .tex 文件", "直接粘贴 LaTeX"])

    base_resume = ""
    if upload_mode == "上传 .tex 文件":
        uploaded = st.file_uploader("选择 .tex 文件", type=["tex"])
        if uploaded:
            base_resume = uploaded.read().decode("utf-8")
            st.success(f"✅ 已加载：{uploaded.name}（{len(base_resume)} 字符）")
    else:
        base_resume = st.text_area(
            "粘贴 LaTeX 内容",
            height=320,
            placeholder=r"\documentclass{article} ..."
        )
        if base_resume:
            st.caption(f"已输入 {len(base_resume)} 字符")

    st.divider()
    st.markdown("## 💾 历史记录")
    if "history" not in st.session_state:
        st.session_state.history = []

    if st.session_state.history:
        for i, rec in enumerate(reversed(st.session_state.history[-5:])):
            with st.expander(f"#{len(st.session_state.history)-i}  {rec['company']}"):
                st.caption(rec["time"])
                st.download_button(
                    "⬇️ 重新下载",
                    data=rec["tex"].encode("utf-8"),
                    file_name=rec["filename"],
                    mime="text/plain",
                    key=f"hist_{i}"
                )
    else:
        st.caption("暂无历史记录")


# ── 主界面 ──────────────────────────────────────────────
st.markdown('<div class="main-title">📄 简历定制助手</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">粘贴 JD → AI 分析匹配 → 下载定制 .tex → 上传 Overleaf 编译</div>', unsafe_allow_html=True)

col_jd, col_result = st.columns([1, 1], gap="large")

with col_jd:
    st.subheader("📌 目标岗位信息")

    company_name = st.text_input("公司 / 岗位名称（用于文件命名）", placeholder="例如：字节跳动-数据分析师")

    jd_text = st.text_area(
        "粘贴招聘 JD",
        height=320,
        placeholder="粘贴完整的岗位描述，包括职责、要求、技能栈等..."
    )

    extra_inst = st.text_area(
        "额外指令（可选）",
        height=100,
        placeholder=(
            "例如：\n"
            "- 重点突出 Python 和机器学习经验\n"
            "- 将实习经历放到最前面\n"
            "- 摘要部分提到对该行业的热情"
        )
    )

    show_diff = st.checkbox("生成后显示改动摘要", value=True)

    generate_btn = st.button("🚀 生成定制简历", type="primary", use_container_width=True)


with col_result:
    st.subheader("✨ 定制结果")

    if generate_btn:
        if not api_key:
            st.error("⚠️ 请在左侧栏输入 DeepSeek API Key")
        elif not base_resume.strip():
            st.error("⚠️ 请上传或粘贴基础简历 LaTeX 代码")
        elif not jd_text.strip():
            st.error("⚠️ 请粘贴岗位 JD")
        else:
            with st.spinner("🤖 AI 正在分析 JD 并优化简历，请稍候..."):
                try:
                    client = OpenAI(
                        api_key=api_key,
                        base_url="https://api.deepseek.com"
                    )

                    system_prompt = """你是一名专业的求职简历优化专家，精通 LaTeX 排版。
你的任务是根据给定的岗位 JD，在**不虚构任何信息**的前提下，对候选人的 LaTeX 简历进行针对性优化。

优化策略：
1. **关键词匹配**：在已有内容中自然融入 JD 里出现的核心技能词、行业术语
2. **内容排序**：将与该岗位最相关的技能、项目、经历调整到靠前位置
3. **描述优化**：用更贴合岗位要求的动词和量化表述重写项目/工作经历的 bullet points
4. **摘要定制**：如有 Summary/Objective 部分，针对该岗位重写
5. **技能部分**：调整技能顺序，JD 中提到的技术栈优先展示

严格规则：
- 保持 LaTeX 语法完全正确，不破坏现有排版命令
- 不新增原始简历中没有的工作经历、学历、证书
- 只返回完整的 LaTeX 代码，不添加任何解释文字、markdown 代码块标记"""

                    user_parts = [
                        f"【目标岗位 JD】\n{jd_text}",
                    ]
                    if extra_inst.strip():
                        user_parts.append(f"【额外要求】\n{extra_inst}")
                    user_parts.append(f"【原始简历 LaTeX 代码】\n{base_resume}")
                    user_parts.append("请直接返回优化后的完整 LaTeX 代码：")
                    user_prompt = "\n\n".join(user_parts)

                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=temperature
                    )

                    raw = response.choices[0].message.content.strip()

                    # 清理 AI 可能包裹的 markdown 代码块
                    raw = re.sub(r"^```(?:latex|tex)?\n?", "", raw)
                    raw = re.sub(r"\n?```$", "", raw)
                    result_tex = raw.strip()

                    # 保存到历史
                    ts = datetime.now().strftime("%m-%d %H:%M")
                    label = company_name.strip() if company_name.strip() else "未命名岗位"
                    safe_name = re.sub(r'[\\/:*?"<>|]', "_", label)
                    filename = f"resume_{safe_name}_{datetime.now().strftime('%m%d_%H%M')}.tex"

                    st.session_state.history.append({
                        "company": label,
                        "time": ts,
                        "tex": result_tex,
                        "filename": filename
                    })
                    st.session_state["result_tex"] = result_tex
                    st.session_state["result_filename"] = filename

                    # 生成改动摘要
                    if show_diff:
                        with st.spinner("生成改动摘要..."):
                            diff_resp = client.chat.completions.create(
                                model="deepseek-chat",
                                messages=[
                                    {"role": "user", "content": (
                                        f"请对比以下两份简历的 LaTeX 代码，用 3~6 条中文简要说明做了哪些修改（每条一行，以 - 开头）。"
                                        f"\n\n【原始简历】\n{base_resume[:3000]}"
                                        f"\n\n【优化后简历】\n{result_tex[:3000]}"
                                    )}
                                ],
                                temperature=0.1
                            )
                            st.session_state["diff_summary"] = diff_resp.choices[0].message.content.strip()

                    st.success("✅ 生成成功！")
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ 生成失败：{str(e)}")

    # 展示结果
    if "result_tex" in st.session_state:
        result_tex = st.session_state["result_tex"]
        filename = st.session_state.get("result_filename", "resume_customized.tex")

        btn_col1, btn_col2 = st.columns([1, 1])
        with btn_col1:
            st.download_button(
                label="⬇️ 下载 .tex 文件",
                data=result_tex.encode("utf-8"),
                file_name=filename,
                mime="text/plain",
                use_container_width=True,
                type="primary"
            )
        with btn_col2:
            st.button(
                "📋 复制代码（手动）",
                use_container_width=True,
                help="点击下方代码框，Ctrl+A 全选后 Ctrl+C 复制"
            )

        st.info(
            "**粘贴到 Overleaf 步骤：**  \n"
            "① 展开下方「查看 LaTeX 代码」→ 全选复制  \n"
            "② Overleaf 项目里点击 `resume.tex`  \n"
            "③ Ctrl+A 全选原内容 → Ctrl+V 粘贴  \n"
            "④ 点击 **Recompile** → 下载 PDF ✅"
        )

        if show_diff and "diff_summary" in st.session_state:
            with st.expander("📝 改动摘要", expanded=True):
                st.markdown(st.session_state["diff_summary"])

        with st.expander("🔍 查看 LaTeX 代码（点击代码区 Ctrl+A 全选复制）", expanded=True):
            st.code(result_tex, language="latex")

        st.caption(f"文件名：`{filename}`  |  字符数：{len(result_tex)}")

    else:
        st.info("👈 填写左侧信息后，点击「生成定制简历」")
        st.markdown("""
**使用流程：**

1. 在左侧上传或粘贴你的基础 `.tex` 简历
2. 填写目标岗位名称
3. 粘贴招聘 JD（越完整越好）
4. 点击生成 → 下载 `.tex`
5. 上传至 Overleaf 编译即可 📤

**注意事项：**
- AI 只会调整已有内容，不会编造新经历
- 每次生成结果保存在左侧「历史记录」中
- 建议保存一份完整的「母版」简历，每次都基于它生成
        """)
