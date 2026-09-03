# RAGForge

## 项目简介

RAGForge 是一个面向企业报告的 RAG（检索增强生成）问答项目，串联 PDF/Markdown 文档处理、文本分块、向量检索、可选的 LLM 重排序和结构化问答。

## 启动方式

### 环境要求

- Python 3.11
- DashScope API

### 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e . -r requirements.txt
```

### 配置 API 密钥

复制 `env` 为 `.env`，并填写至少一个 DashScope API 密钥：

```dotenv
DASHSCOPE_API_KEY=your_dashscope_api_key
```

### 启动 Streamlit

仓库已包含预生成的分块数据和 FAISS 索引，安装依赖并配置密钥后运行：

```bash
streamlit run app_streamlit.py
```

### 命令行运行

```bash
python src/pipeline.py
cd data/stock_data
python ../../main.py process-questions --config max
```

## 项目结构

```text
RAGForge/
├── app_streamlit.py             # Streamlit 界面
├── main.py                      # Click 命令行入口
├── src/
│   ├── pipeline.py              # 流程编排与配置
│   ├── pdf_parsing.py           # Docling PDF 解析
│   ├── pdf_mineru.py            # MinerU PDF 转 Markdown
│   ├── text_splitter.py         # 文本分块
│   ├── ingestion.py             # FAISS / BM25 建库
│   ├── retrieval.py             # 检索
│   ├── reranking.py             # 重排序
│   ├── questions_processing.py  # 问题路由与答案生成
│   ├── api_requests.py          # 多模型 API 封装
│   ├── prompts.py               # Prompt 与输出 Schema
│   └── tables_serialization.py  # 表格序列化
├── data/stock_data/             # 数据集及处理产物
├── docs/                        # 模块说明
├── requirements.txt
└── env                          # 环境变量模板
```

