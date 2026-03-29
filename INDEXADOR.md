# INDEXADOR - Roadmap de Download e Indexação

Pipeline completo para adicionar novas diretrizes ao MAC RAG Eco.

---

## ✅ Status do Benchmark (Atualizado 2026-03-29)

> Ref: [docs/BENCHMARK-OPEN-EVIDENCE-VS-ECO-RAG.md](docs/BENCHMARK-OPEN-EVIDENCE-VS-ECO-RAG.md)

| Prioridade | Diretriz | Impacto | Status |
|:----------:|----------|---------|:------:|
| ~~**CRÍTICA**~~ | ESC ACHD 2020 | ~~ECO RAG = 0 em ToF~~ | ✅ Resolvido |
| ~~**CRÍTICA**~~ | AHA/ACC ACHD 2018 | ~~ECO RAG = 0 em ToF~~ | ✅ Resolvido |
| Alta | ACC/AHA ACHD 2025 | CIV nota 7.4 → meta 10 | Pendente |
| Alta | ESC/EACTS VHD 2021 | EA nota 7.8 → meta 10 | Pendente |
| Alta | ACC/AHA VHD 2020 | EA nota 7.8 → meta 10 | Pendente |

**Status Benchmark:** OE 9.0 vs ECO RAG **8.2** (5 testes) ✅ Melhoria de 6.5 → 8.2

---

## Visão Geral

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  1. DOWNLOAD    │───▶│  2. PARSE       │───▶│  3. ENRICH      │───▶│  4. INDEX       │
│  (PDF/TXT)      │    │  (chunks.json)  │    │  (GPT-4o-mini)  │    │  (ChromaDB+GPU) │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 1. Download de Diretrizes

### Fontes Prioritárias (por hierarquia)
1. **DIC-SBC** (brasileiro) - Arquivos Brasileiros de Cardiologia
2. **ASE** (americano) - JASE / asecho.org
3. **EACVI** (europeu) - European Heart Journal
4. **ESC** (europeu) - escardio.org
5. **AHA/ACC** (americano) - Circulation / JACC

### Formatos Aceitos
| Formato | Parser | Notas |
|---------|--------|-------|
| `.pdf` | `parse_single_pdf()` | PyMuPDF (fitz) |
| `.txt` | `parse_single_txt()` | Texto puro ou JSON com campo `markdown` |

### Diretório de Guidelines
```
guidelines_dic_sbc/
├── 01_Indicacoes_Eco_Adultos_2019.pdf
├── 02_Eco_Fetal_Pediatrica_CC_2020.pdf
├── 03_Strain_Miocardico_2023.pdf
├── ...
├── 09_ESC_ACHD_2020.pdf
└── 10_AHA_ACC_ACHD_2018_full.txt
```

### Registrar Nova Diretriz
Adicionar entrada em `parse_dic_sbc.py` → `DIC_GUIDELINES`:

```python
'XX_Nome_Diretriz_ANO.pdf': {
    'title': 'Título Completo da Diretriz',
    'society': 'DIC-SBC',  # ou ESC, AHA/ACC, ASE, EACVI
    'topic': 'Tópico Principal',
    'year': '2024',
    'doi': '10.xxxx/xxxxx',
},
```

---

## 2. Parse (Chunking)

### Comando
```bash
python parse_dic_sbc.py
```

### O que acontece
1. Lê cada arquivo listado em `DIC_GUIDELINES`
2. Extrai texto (PDF via PyMuPDF, TXT direto ou JSON→markdown)
3. Detecta seções por headings (regex `_HEADING_RE`)
4. Divide em chunks de até 1500 caracteres
5. Salva em `chunks_dic_sbc.json`

### Metadados por Chunk
```json
{
  "text": "Conteúdo do chunk...",
  "metadata": {
    "diretriz": "Título da Diretriz",
    "sociedade": "DIC-SBC",
    "topico": "Strain Miocárdico",
    "ano": "2023",
    "doi": "10.36660/abc.20230646",
    "secao": "Indicações Clínicas",
    "hierarquia": "Indicações Clínicas",
    "tipo": "texto",
    "parte": 1,
    "idioma": "pt"
  }
}
```

---

## 3. Enrich (Contexto Semântico)

### Comando
```bash
python parse_dic_sbc.py --enrich
```

### O que acontece
1. Envia cada chunk para GPT-4o-mini
2. Gera contexto adicional (sinônimos, termos relacionados)
3. Cria chunks compostos para tabelas/recomendações
4. Salva em `chunks_all_enriched.json`

### Custo Estimado
- ~$0.01-0.02 por 100 chunks (GPT-4o-mini)
- 1000 chunks ≈ $0.15

---

## 4. Index (ChromaDB + GPU)

### Pré-requisitos GPU (RTX 5070 Ti / Blackwell sm_120)
```bash
# Instalar PyTorch com CUDA 12.8+
pip install --pre torch --force-reinstall --index-url https://download.pytorch.org/whl/nightly/cu128
```

### Verificar CUDA
```python
import torch
print(torch.cuda.is_available())  # True
print(torch.version.cuda)          # 12.8
print(torch.cuda.get_device_name(0))  # NVIDIA GeForce RTX 5070 Ti
```

### Comando Completo (Parse + Enrich + Index)
```bash
python parse_dic_sbc.py --enrich --index
```

### Apenas Re-indexar (chunks já enriquecidos)
```bash
python index.py --skip-enrich
```

### Configuração de Device
```bash
# Forçar CPU (fallback)
set INDEX_DEVICE=cpu
python index.py --skip-enrich

# GPU automático (padrão)
python index.py --skip-enrich
```

### Verificar GPU (OBRIGATÓRIO antes de indexar)
```bash
python -c "
from sentence_transformers import SentenceTransformer
import torch
print('CUDA:', torch.cuda.is_available())
print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')
model = SentenceTransformer('intfloat/multilingual-e5-base')
print('Modelo device:', model.device)  # DEVE ser cuda:0
"
```

**Saída esperada:**
```
CUDA: True
Device: NVIDIA GeForce RTX 5070 Ti
Modelo device: cuda:0
```

⚠️ Se `Modelo device: cpu`, reinstale PyTorch: `pip install --pre torch --force-reinstall --index-url https://download.pytorch.org/whl/nightly/cu128`

### Performance
| Device | 20k chunks | Notas |
|--------|------------|-------|
| RTX 5070 Ti (GPU) | ~2 min | cu128 obrigatório |
| CPU | ~30 min | Fallback universal |

**Nota:** A velocidade aparente (~10-30 batches/s) é limitada pelo ChromaDB (inserção), não pelos embeddings. Os embeddings GPU rodam a ~500+ textos/s.

---

## 5. Pós-Indexação

### Reiniciar Streamlit (obrigatório)
```bash
# Matar processos antigos
taskkill //F //IM streamlit.exe
taskkill //F //IM python.exe

# Reiniciar
streamlit run app.py --server.port 8501
```

**Por quê?** O singleton `_collection` em `core/config.py` cacheia a referência antiga do ChromaDB.

### Verificar Corpus
```python
from core.config import get_collection
coll = get_collection()
print(f"Total: {coll.count()} chunks")
```

### Testar Retrieval
```python
results = coll.query(
    query_texts=["query: comunicação interatrial CIA"],
    n_results=5
)
for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
    print(f"[{meta['sociedade']}] {meta['diretriz'][:50]}...")
```

---

## Troubleshooting

### Erro: `CUDA error: no kernel image available`
**Causa:** PyTorch incompatível com GPU (sm_120 precisa CUDA 12.8+)
```bash
pip install --pre torch --force-reinstall --index-url https://download.pytorch.org/whl/nightly/cu128
```

### Erro: `Collection does not exist`
**Causa:** Streamlit usando cache antigo após re-indexação
```bash
taskkill //F //IM streamlit.exe
start streamlit run app.py
```

### Erro: `ChromaDB corrupted`
**Causa:** Indexação interrompida
```bash
rmdir /s /q chroma_db
python index.py --skip-enrich
```

### Arquivo .txt produz poucos chunks
**Causa:** Arquivo é JSON com campo `markdown`
**Solução:** `parse_single_txt()` já detecta automaticamente (adicionado 2026-03-29)

---

## Corpus Atual (2026-03-29)

| Sociedade | Chunks | Diretrizes |
|-----------|--------|------------|
| AHA/ACC | 1.636 | ACHD 2018 |
| ASE | 12.633 | Guidelines 2015-2025 |
| DIC-SBC | 3.829 | 8 posicionamentos |
| ESC | 1.674 | ACHD 2020 |
| **TOTAL** | **19.772** | |

---

## Roadmap Futuro

### Pendências do Benchmark (Prioridade Alta)

> Identificadas durante benchmark Open Evidence vs ECO RAG (2026-03-29)
> Ref: [docs/BENCHMARK-OPEN-EVIDENCE-VS-ECO-RAG.md](docs/BENCHMARK-OPEN-EVIDENCE-VS-ECO-RAG.md)

#### Cardiopatias Congênitas (ACHD) - ✅ GAP RESOLVIDO (2026-03-29)

> **Correção aplicada:** Prompt modificado para distinguir "pediatria" (fora do escopo) de "ACHD" (dentro do escopo).
> **Resultado:** ECO RAG agora responde sobre Tetralogia de Fallot com nota 8.4/10.

| Diretriz | Fonte | Ano | Teste | Status |
|----------|-------|:---:|-------|:------:|
| Guidelines for the Management of Adults With Congenital Heart Disease | ESC | 2020 | Teste 2 (ToF) | ✅ Indexado |
| Guidelines for the Management of Adults With Congenital Heart Disease | AHA/ACC | 2018 | Teste 2 (ToF) | ✅ Indexado |
| Expert Consensus: Management of Infants and Neonates With Tetralogy of Fallot | AATS | 2022 | Teste 2 (ToF) | Pendente |
| 2025 ACC/AHA/HRS/ISACHD/SCAI Guideline for ACHD | ACC/AHA | 2025 | Teste 1 (CIV) | Pendente |

#### Valvopatias - Atualização Necessária
| Diretriz | Fonte | Ano | Teste | Prioridade |
|----------|-------|:---:|-------|:----------:|
| Guidelines for the Management of Valvular Heart Disease | ESC/EACTS | 2021 | Teste 3 (EA) | Alta |
| Guidelines for the Management of Valvular Heart Disease | ACC/AHA | 2020 | Teste 3 (EA) | Alta |

### Pendentes (Lista Original)
- [ ] ASE Strain 2024 Update
- [ ] EACVI Heart Failure 2023
- [ ] BSE Minimum Dataset 2024

### Automação Planejada
- [ ] Script de download automático via DOI
- [ ] Validação de qualidade dos chunks
- [ ] Dashboard de métricas do corpus
- [ ] CI/CD para indexação incremental

---

## Comandos Rápidos

```bash
# Pipeline completo (nova diretriz)
python parse_dic_sbc.py --enrich --index

# Apenas re-indexar
python index.py --skip-enrich

# Verificar GPU
python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"

# Reiniciar app
taskkill //F //IM streamlit.exe && start streamlit run app.py
```
