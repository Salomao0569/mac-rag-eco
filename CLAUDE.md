# CLAUDE.md - MAC RAG Eco

Este arquivo fornece instruções para Claude Code ao trabalhar neste repositório.

## Visão Geral do Projeto

**MAC RAG Eco** - Sistema RAG (Retrieval-Augmented Generation) para ecocardiografia baseado em diretrizes brasileiras e internacionais.

**Stack**: Agno + Streamlit + ChromaDB + SentenceTransformer (local embeddings)

## Comandos de Desenvolvimento

```bash
# Iniciar aplicação
streamlit run app.py --server.port 8501

# Verificar GPU/CUDA
python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"
```

## Arquitetura

```
Frontend (Streamlit app.py)
    |
    v
Agno Agent (core/agent.py)
    |
    v
ChromaDB (chroma_db/) - 19.772 chunks
    |-- Embeddings: intfloat/multilingual-e5-base (local)
    |-- Sociedades: DIC-SBC, ASE, ESC, AHA/ACC
```

## Indexador - Pipeline de Diretrizes

O projeto possui um **agente Indexador** para adicionar novas diretrizes ao corpus.

### Documentação Completa
- **Local**: [INDEXADOR.md](INDEXADOR.md)
- **Notion**: https://www.notion.so/3321ed0a252b81538650e4ed0803ffa7

### Comandos Rápidos

```bash
# Pipeline completo (nova diretriz)
python parse_dic_sbc.py --enrich --index

# Apenas re-indexar (chunks já enriquecidos)
python index.py --skip-enrich

# Reiniciar app após indexação (OBRIGATÓRIO)
taskkill //F //IM streamlit.exe && start streamlit run app.py
```

### Pré-requisitos GPU (RTX 5070 Ti / Blackwell sm_120)

```bash
# CUDA 12.8+ obrigatório
pip install --pre torch --force-reinstall --index-url https://download.pytorch.org/whl/nightly/cu128
```

### Adicionar Nova Diretriz

1. Colocar PDF/TXT em `guidelines_dic_sbc/`
2. Registrar em `parse_dic_sbc.py` → `DIC_GUIDELINES`
3. Executar: `python parse_dic_sbc.py --enrich --index`
4. Reiniciar Streamlit

## Arquivos Principais

| Arquivo | Propósito |
|---------|-----------|
| `app.py` | Interface Streamlit principal |
| `core/agent.py` | Agente Agno com RAG |
| `core/config.py` | Configuração ChromaDB + device detection |
| `prompts/single_agent.md` | System prompt do agente |
| `parse_dic_sbc.py` | Parser de PDFs/TXTs → chunks |
| `index.py` | Indexação ChromaDB com GPU |
| `enrich.py` | Enriquecimento semântico (GPT-4o-mini) |
| `INDEXADOR.md` | Roadmap completo do pipeline |

## Corpus Atual

| Sociedade | Chunks | Diretrizes |
|-----------|--------|------------|
| AHA/ACC | 1.636 | ACHD 2018 |
| ASE | 12.633 | Guidelines 2015-2025 |
| DIC-SBC | 3.829 | 8 posicionamentos |
| ESC | 1.674 | ACHD 2020 |
| **TOTAL** | **19.772** | |

## Troubleshooting

### ChromaDB "collection not found" após re-indexar
```bash
taskkill //F //IM streamlit.exe
start streamlit run app.py
```
**Causa**: Singleton `_collection` em `core/config.py` cacheia referência antiga.

### CUDA error: no kernel image available
```bash
pip install --pre torch --force-reinstall --index-url https://download.pytorch.org/whl/nightly/cu128
```
**Causa**: RTX 5070 Ti (sm_120) precisa CUDA 12.8+.

## Agente de Benchmark - Open Evidence vs ECO RAG

Sistema de avaliação comparativa para medir qualidade das respostas do ECO RAG contra Open Evidence.

### Documentação Completa
- **Metodologia**: [docs/AGENT-BENCHMARK.md](docs/AGENT-BENCHMARK.md)
- **Resultados**: [docs/BENCHMARK-OPEN-EVIDENCE-VS-ECO-RAG.md](docs/BENCHMARK-OPEN-EVIDENCE-VS-ECO-RAG.md)
- **Notion**: https://www.notion.so/Benckmarcks-3321ed0a252b801fb244d8f197bc14b8

### Metodologia de Avaliação

| Parâmetro | Peso |
|-----------|:----:|
| Completude | 20% |
| Atualização (diretrizes recentes) | 20% |
| Precisão | 20% |
| Praticidade Clínica | 15% |
| Formato DIC (prova) | 15% |
| Referências | 10% |

**Fórmula:** `Nota = (P1×0.20) + (P2×0.20) + (P3×0.20) + (P4×0.15) + (P5×0.15) + (P6×0.10)`

### Fluxo de Trabalho

1. **Executar teste**: Perguntar mesmo tema nos dois sistemas
2. **Avaliar**: Pontuar 6 parâmetros (0-10) para cada sistema
3. **Registrar**: Atualizar `BENCHMARK-OPEN-EVIDENCE-VS-ECO-RAG.md`
4. **Tasks**: Criar ações de melhoria para gaps identificados
5. **Implementar**: Adicionar diretrizes faltantes ao ECO RAG
6. **Re-testar**: Validar melhoria

### Status Atual (2026-03-29)

| Métrica | Valor |
|---------|:-----:|
| Testes realizados | 5 |
| Média Open Evidence | 9.0 |
| Média ECO RAG | 6.5 |
| Média ECO RAG (excl. congênitas) | 8.1 |
| Tasks pendentes | 22 |

### Gaps Críticos Identificados

- **ACHD (Cardiopatias Congênitas)**: ECO RAG = 0 em Tetralogia de Fallot
- **Diretrizes faltantes**: ESC 2020 ACHD, AHA/ACC 2018 ACHD, ESC 2021 VHD

## Links Úteis

- **Notion**: https://www.notion.so/RAG-FACTORY-3311ed0a252b80d2a5b6cc4dee8c638a
- **Indexador (Notion)**: https://www.notion.so/3321ed0a252b81538650e4ed0803ffa7
- **Benchmarks (Notion)**: https://www.notion.so/Benckmarcks-3321ed0a252b801fb244d8f197bc14b8
