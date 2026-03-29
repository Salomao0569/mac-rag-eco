# Agente de Benchmark: Open Evidence vs ECO RAG

> Sistema automatizado para avaliação comparativa de sistemas RAG médicos com foco em preparação para prova DIC 2026.

---

## Objetivo

Avaliar e comparar respostas do **Open Evidence** e **ECO RAG** em temas de cardiologia, identificando gaps e gerando tasks de melhoria para que o ECO RAG alcance nota máxima (10/10) em cada tema testado.

---

## Metodologia de Avaliação

### Parâmetros e Pesos

| # | Parâmetro | Descrição | Peso |
|:-:|-----------|-----------|:----:|
| 1 | **Completude** | Abrangência do conteúdo, detalhes anatômicos/fisiológicos, cobertura de subtipos | 20% |
| 2 | **Atualização** | Uso de diretrizes mais recentes (2024-2025), guidelines atuais | 20% |
| 3 | **Precisão** | Correção das informações, ausência de erros, dados de prognóstico | 20% |
| 4 | **Praticidade Clínica** | Formato escaneável, tabelas úteis, aplicabilidade direta no dia-a-dia | 15% |
| 5 | **Formato DIC** | Adequação para estudo de prova (classe/NE, valores de corte memorizáveis) | 15% |
| 6 | **Referências** | Qualidade e quantidade das citações (JACC, NEJM, Lancet, etc.) | 10% |

### Escala de Notas

| Nota | Significado |
|:----:|-------------|
| 0 | Ausente ou recusou responder |
| 1-3 | Incorreto ou muito incompleto |
| 4-5 | Parcialmente correto, gaps significativos |
| 6-7 | Adequado, mas com espaço para melhoria |
| 8-9 | Bom a excelente |
| 10 | Perfeito, referência gold standard |

### Fórmula de Cálculo

```
Nota Final = (P1×0.20) + (P2×0.20) + (P3×0.20) + (P4×0.15) + (P5×0.15) + (P6×0.10)
```

Onde P1-P6 são as notas de cada parâmetro (0-10).

---

## Fluxo de Trabalho

### Fase 1: Execução do Teste

```mermaid
graph LR
    A[Escolher Tema] --> B[Perguntar no Open Evidence]
    B --> C[Perguntar no ECO RAG]
    C --> D[Coletar Respostas]
    D --> E[Avaliar Parâmetros]
```

1. **Escolher tema** da lista de próximos testes
2. **Formular pergunta** padronizada: "Fale sobre [TEMA]"
3. **Executar** nos dois sistemas
4. **Copiar** respostas completas

### Fase 2: Avaliação

Para cada sistema, avaliar os 6 parâmetros (0-10):

```markdown
| Parâmetro | Open Evidence | ECO RAG | Observações |
|-----------|:-------------:|:-------:|-------------|
| Completude | X | Y | [detalhe] |
| Atualização | X | Y | [detalhe] |
| Precisão | X | Y | [detalhe] |
| Praticidade Clínica | X | Y | [detalhe] |
| Formato DIC | X | Y | [detalhe] |
| Referências | X | Y | [detalhe] |
```

### Fase 3: Cálculo e Registro

1. Calcular nota final de cada sistema
2. Registrar no arquivo `BENCHMARK-OPEN-EVIDENCE-VS-ECO-RAG.md`
3. Atualizar médias acumuladas
4. Identificar gaps

### Fase 4: Geração de Tasks de Melhoria

**Para cada teste onde ECO RAG < 10, criar tasks:**

```markdown
## Tasks de Melhoria - [TEMA]

### Gap 1: [Descrição do gap]
- [ ] **Ação:** [O que fazer]
- [ ] **Diretriz:** [Qual documento adicionar]
- [ ] **Prioridade:** Alta/Média/Baixa

### Gap 2: [Descrição]
...
```

---

## Template de Teste

```markdown
## Teste N: [TEMA]

**Data:** YYYY-MM-DD
**Pergunta:** "[pergunta exata]"

### Resposta Open Evidence
> [Colar resposta ou resumo dos pontos principais]

### Resposta ECO RAG
> [Colar resposta ou resumo dos pontos principais]

### Notas por Parâmetro

| Parâmetro | Open Evidence | ECO RAG | Observações |
|-----------|:-------------:|:-------:|-------------|
| Completude | | | |
| Atualização | | | |
| Precisão | | | |
| Praticidade Clínica | | | |
| Formato DIC | | | |
| Referências | | | |

### Cálculo da Nota Final

| Sistema | **Nota Final** |
|---------|:--------------:|
| Open Evidence | X.XX/10 |
| ECO RAG | X.XX/10 |

### Tasks de Melhoria ECO RAG

- [ ] Task 1
- [ ] Task 2
- [ ] Task 3
```

---

## Categorias de Temas

### Prioridade Alta (Cobrados na DIC)

| Categoria | Temas | Status |
|-----------|-------|:------:|
| **Valvopatias** | Estenose aórtica, Insuficiência mitral, Estenose mitral, Insuficiência aórtica | Parcial |
| **Função Ventricular** | Disfunção diastólica, ICFEp, ICFEr, Strain | Parcial |
| **Cardiopatias Congênitas** | CIV, CIA, ToF, Coarctação, Ebstein | Gap crítico |
| **Cardiomiopatias** | HCM, DCM, ARVC, Amiloidose | Pendente |
| **Pericárdio** | Tamponamento, Constrição, Derrame | Pendente |

### Prioridade Média

| Categoria | Temas |
|-----------|-------|
| **Massas Cardíacas** | Tumores, Trombos, Vegetações |
| **Aorta** | Dissecção, Aneurisma, Coarctação |
| **Hipertensão Pulmonar** | Classificação, Diagnóstico eco |

---

## Métricas de Sucesso

### Meta por Fase

| Fase | Meta ECO RAG | Prazo |
|------|:------------:|-------|
| Inicial | Média ≥6.0 | Atual |
| Intermediária | Média ≥8.0 | +2 semanas |
| Final | Média ≥9.0 | +1 mês |
| Gold Standard | Todos ≥9.5 | +2 meses |

### KPIs

- **Taxa de resposta:** % de temas que ECO RAG consegue responder (não-zero)
- **Gap médio:** Diferença média entre OE e ECO RAG
- **Taxa de atualização:** % de respostas com diretrizes 2024-2025
- **Score praticidade:** Média do parâmetro "Praticidade Clínica"

---

## Ações de Melhoria Padrão

### Quando ECO RAG = 0 (não respondeu)

1. Verificar se o tema existe no banco de dados
2. Identificar diretrizes faltantes
3. Baixar e processar PDFs das diretrizes
4. Re-indexar no ChromaDB
5. Re-testar

### Quando ECO RAG < 7 (resposta fraca)

1. Verificar qualidade dos chunks indexados
2. Adicionar mais fontes (guidelines adicionais)
3. Melhorar prompt do sistema
4. Adicionar tabelas estruturadas ao prompt
5. Re-testar

### Quando ECO RAG 7-9 (bom mas não excelente)

1. Adicionar diretrizes mais recentes
2. Enriquecer com dados de prognóstico
3. Melhorar formatação das tabelas
4. Adicionar mais referências ao contexto
5. Re-testar

---

## Histórico de Benchmarks

| Data | Testes | Média OE | Média ECO | Gap |
|------|:------:|:--------:|:---------:|:---:|
| 2026-03-29 | 5 | 9.0 | 6.5 | 2.5 |

---

## Links Relacionados

- [BENCHMARK-OPEN-EVIDENCE-VS-ECO-RAG.md](BENCHMARK-OPEN-EVIDENCE-VS-ECO-RAG.md) - Resultados detalhados
- [Notion - Benchmarks](https://www.notion.so/Benckmarcks-3321ed0a252b801fb244d8f197bc14b8) - Dashboard visual

---

*Última atualização: 2026-03-29*
