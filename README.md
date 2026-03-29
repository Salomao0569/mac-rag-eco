# MAC RAG Ecocardiografia 💓

RAG ultraespecífica em **ecocardiografia**, operando sobre diretrizes de DIC-SBC, ASE, EACVI, BSE.

Gerado automaticamente pelo **RAG Factory** a partir de `mac-rag-cardiology`.

## Setup

1. Copie seu `.env` com as API keys:
   ```
   OPENAI_API_KEY=...
   TAVILY_API_KEY=...
   OPENROUTER_API_KEY=...  # opcional
   DASHSCOPE_API_KEY=...   # opcional
   ```

2. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Coloque as diretrizes nas pastas:
   - `guidelines_xml/` — XMLs do SciELO (JATS)
   - `guidelines_html/` — JSONs extraídos via Playwright
   - `guidelines_pdf/` — PDFs para extração direta

4. Execute o pipeline de ingestão:
   ```bash
   python parse.py        # Parsing → chunks.json
   python enrich.py       # Enriquecimento contextual
   python index.py        # Indexação no ChromaDB
   ```

5. Inicie a interface:
   ```bash
   streamlit run app.py
   ```

## Arquitetura

- **Busca híbrida**: Semântica (ChromaDB + e5-base) + BM25 + RRF + FlashRank reranking
- **Multi-agente**: Coordenador + RAG Agent + PubMed Agent + Tavily Agent (via Agno)
- **Consulta**: Diarização → Extração → SOAP → Consultor RAG-powered
- **Scores**: Cálculo automático a partir do CartaoClinico
- **Alertas**: Regras de decisão clínica configuráveis

## Customização

Edite os arquivos gerados para adaptar ao seu domínio:
- `coordinator_prompt.md` — Prompt do coordenador
- `prompts/rag_agent.md` — Prompt do agente RAG
- `prompts/extractor.md` — Prompt do extrator de dados
- `core/auto_scores.py` — Scores clínicos
- `core/alerts.py` — Alertas clínicos
- `core/schemas.py` — Schema do CartaoClinico
