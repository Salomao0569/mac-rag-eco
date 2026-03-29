# Benchmark: Open Evidence vs ECO RAG

> Comparativo sistemático entre Open Evidence e ECO RAG para decisão clínica em cardiologia.
> Foco: Preparação para prova DIC 2026.

---

## Metodologia

| Parâmetro | Descrição | Peso |
|-----------|-----------|------|
| **Completude** | Abrangência do conteúdo, detalhes anatômicos/fisiológicos | 20% |
| **Atualização** | Uso de diretrizes mais recentes (2024-2025) | 20% |
| **Precisão** | Correção das informações, ausência de erros | 20% |
| **Praticidade Clínica** | Formato escaneável, tabelas, aplicabilidade direta | 15% |
| **Formato DIC** | Adequação para estudo de prova (classe/NE, valores de corte) | 15% |
| **Referências** | Qualidade e quantidade das citações | 10% |

**Escala:** 0-10 (0 = ausente/incorreto, 5 = adequado, 10 = excelente)

---

## Teste 1: Comunicação Interventricular (CIV)

**Data:** 2026-03-29
**Pergunta:** "Fale sobre comunicação interventricular"

### Notas por Parâmetro

| Parâmetro | Open Evidence | ECO RAG | Observações |
|-----------|:-------------:|:-------:|-------------|
| Completude | **9** | 6 | OE: classificação 4 tipos com %, história natural, técnicas cirúrgicas. ECO: básico |
| Atualização | **10** | 7 | OE: diretriz **2025 AHA/ACC/HRS**. ECO: apenas ESC 2020 + AHA 2018 |
| Precisão | **9** | 8 | Ambos corretos. OE mais detalhado |
| Praticidade Clínica | 6 | **9** | ECO: tabelas estruturadas, formato consulta rápida |
| Formato DIC | 7 | **8** | ECO: classe + NE em tabela. OE: texto corrido |
| Referências | **10** | 6 | OE: 9 refs com autores/journal. ECO: 2 refs genéricas |

### Cálculo da Nota Final

| Sistema | Cálculo | **Nota Final** |
|---------|---------|:--------------:|
| **Open Evidence** | (9×0.20)+(10×0.20)+(9×0.20)+(6×0.15)+(7×0.15)+(10×0.10) | **8.55** |
| **ECO RAG** | (6×0.20)+(7×0.20)+(8×0.20)+(9×0.15)+(8×0.15)+(6×0.10) | **7.35** |

### Resumo Teste 1

| | Open Evidence | ECO RAG |
|---|:---:|:---:|
| **NOTA FINAL** | **8.6/10** | **7.4/10** |
| Vencedor | ✅ | |
| Melhor para | Estudo profundo, atualização | Consulta rápida, prática |

---

## Teste 2: Tetralogia de Fallot (TF)

**Data:** 2026-03-29
**Pergunta:** "Fale sobre tetralogia de Fallot"

> ✅ **Re-testado 2026-03-29** após correção do prompt ACHD.

### Notas por Parâmetro

| Parâmetro | Open Evidence | ECO RAG | Observações |
|-----------|:-------------:|:-------:|-------------|
| Completude | **10** | 8 | OE: 4 anomalias, fisiopatologia, crises hipercianóticas, cirurgia. ECO: epidemiologia, etiologia, clínica, eco, manejo |
| Atualização | **9** | 8 | OE: AATS 2022, refs até 2025. ECO: **ESC ACHD 2020** + ASE 2014 |
| Precisão | **10** | 9 | Ambos excelentes. ECO com valores específicos de IP e VD |
| Praticidade Clínica | **8** | 9 | ECO: tabela de follow-up estruturada, indicações claras |
| Formato DIC | **8** | **9** | ECO: indicações com Classe/NE, valores de corte (IP >40ms, VDi >150mL/m²) |
| Referências | **10** | 7 | OE: 10 refs (NEJM, Lancet, JACC). ECO: 2 refs (ESC 2020, ASE 2014) |

### Cálculo da Nota Final

| Sistema | Cálculo | **Nota Final** |
|---------|---------|:--------------:|
| **Open Evidence** | (10×0.20)+(9×0.20)+(10×0.20)+(8×0.15)+(8×0.15)+(10×0.10) | **9.20** |
| **ECO RAG** | (8×0.20)+(8×0.20)+(9×0.20)+(9×0.15)+(9×0.15)+(7×0.10) | **8.40** |

### Resumo Teste 2

| | Open Evidence | ECO RAG |
|---|:---:|:---:|
| **NOTA FINAL** | **9.2/10** | **8.4/10** 🏆 |
| Vencedor | ✅ | |
| Observação | Resposta exemplar | ✅ **GAP CRÍTICO RESOLVIDO!** |

### Análise (Atualizada)

**Correção bem-sucedida!** O ECO RAG agora responde sobre Tetralogia de Fallot com:
- Epidemiologia: 10% das cardiopatias congênitas
- 4 componentes anatômicos
- Indicações de intervenção (Classe I, NE B)
- Valores de corte: IP >40ms, duração QRS >180ms, VDi >150mL/m²
- Tabela de follow-up estruturada
- Referências ESC ACHD 2020 + ASE 2014

**O que foi corrigido:** Prompt modificado para distinguir entre "pediatria" (fora do escopo) e "ACHD - Cardiopatia Congênita do Adulto" (dentro do escopo).

---

## Teste 3: Estenose Aórtica (EA)

**Data:** 2026-03-29
**Pergunta:** "Fale sobre estenose aórtica"

### Notas por Parâmetro

| Parâmetro | Open Evidence | ECO RAG | Observações |
|-----------|:-------------:|:-------:|-------------|
| Completude | **9** | 8 | OE: fisiopatologia detalhada (2 fases), estágios A-D. ECO: cobre principais tópicos |
| Atualização | **10** | 6 | OE: JAMA 2024, Lancet 2024, JACC 2023. ECO: PMID 28385280 (~2017) |
| Precisão | **9** | 8 | Ambos corretos. OE com dados de mortalidade 10 anos |
| Praticidade Clínica | 7 | **10** | ECO: tabelas excelentes (gravidade, TAVI vs SAVR, follow-up) |
| Formato DIC | 7 | **9** | ECO: valores de corte em tabela, classes de indicação. OE: texto corrido |
| Referências | **10** | 5 | OE: 5 refs (JAMA, JACC, Lancet). ECO: 1 ref (PMID) |

### Cálculo da Nota Final

| Sistema | Cálculo | **Nota Final** |
|---------|---------|:--------------:|
| **Open Evidence** | (9×0.20)+(10×0.20)+(9×0.20)+(7×0.15)+(7×0.15)+(10×0.10) | **8.70** |
| **ECO RAG** | (8×0.20)+(6×0.20)+(8×0.20)+(10×0.15)+(9×0.15)+(5×0.10) | **7.75** |

### Resumo Teste 3

| | Open Evidence | ECO RAG |
|---|:---:|:---:|
| **NOTA FINAL** | **8.7/10** | **7.8/10** |
| Vencedor | ✅ | |
| Destaque | Atualização 2024, figuras JAMA | Tabelas práticas (TAVI vs SAVR) |

### Análise

**ECO RAG melhorou significativamente** neste teste de valvopatia:
- Tabelas de gravidade, TAVI vs SAVR, e follow-up são excelentes para prática clínica
- Gap identificado: referências desatualizadas (2017 vs 2024)

**Diretriz faltante:** ESC 2021 Guidelines for Valvular Heart Disease

---

## Teste 4: Insuficiência Mitral (IM)

**Data:** 2026-03-29
**Pergunta:** "Fale sobre insuficiência mitral"

### Notas por Parâmetro

| Parâmetro | Open Evidence | ECO RAG | Observações |
|-----------|:-------------:|:-------:|-------------|
| Completude | **10** | 8 | OE: Carpentier, primária vs secundária, TEER, prognóstico. ECO: bom, menos detalhado |
| Atualização | **9** | 8 | OE: NEJM 2020, JACC 2023, JAMA 2021. ECO: ESC VHD 2021 ✓ |
| Precisão | **10** | 8 | Ambos corretos. OE com dados de mortalidade (6.3%/ano) |
| Praticidade Clínica | 7 | **10** | ECO: 4 tabelas excelentes (gravidade, indicações, reparo vs substituição, follow-up) |
| Formato DIC | 8 | **9** | ECO: classe/NE em tabela, valores EROA/VR/FR. OE: mais texto |
| Referências | **10** | 7 | OE: 6 refs (NEJM, Lancet, JACC, JAMA). ECO: 1 ref (ESC 2021) |

### Cálculo da Nota Final

| Sistema | Cálculo | **Nota Final** |
|---------|---------|:--------------:|
| **Open Evidence** | (10×0.20)+(9×0.20)+(10×0.20)+(7×0.15)+(8×0.15)+(10×0.10) | **9.05** |
| **ECO RAG** | (8×0.20)+(8×0.20)+(8×0.20)+(10×0.15)+(9×0.15)+(7×0.10) | **8.35** |

### Resumo Teste 4

| | Open Evidence | ECO RAG |
|---|:---:|:---:|
| **NOTA FINAL** | **9.1/10** | **8.4/10** 🏆 |
| Vencedor | ✅ | |
| Destaque | Carpentier, TEER, figuras ACC | **Melhor nota ECO RAG!** Tabelas completas |

### Análise

**Melhor performance do ECO RAG até agora!** Diferença de apenas 0.7 pontos.

Pontos fortes ECO RAG:
- Tabela de gravidade com EROA, Volume Regurgitante, Fração Regurgitante, Vena Contracta
- Tabela de indicações com Classe + NE
- Tabela Reparo vs Substituição
- Referência atualizada (ESC VHD 2021)

⚠️ **Bug técnico:** ChromaDB collection error durante o teste (não afetou resposta)

---

## Teste 5: Disfunção Diastólica

**Data:** 2026-03-29
**Pergunta:** "Fale sobre disfunção diastólica"

### Notas por Parâmetro

| Parâmetro | Open Evidence | ECO RAG | Observações |
|-----------|:-------------:|:-------:|-------------|
| Completude | **10** | 8 | OE: fisiopatologia 3 componentes, tratamento extenso (SGLT2i). ECO: foco diagnóstico |
| Atualização | **10** | 9 | Ambos com **ASE 2025**! OE também tem JACC 2023 |
| Precisão | **10** | 9 | Ambos excelentes. Valores corretos |
| Praticidade Clínica | 7 | **10** | ECO: tabela perfeita por graus, algoritmo passo-a-passo |
| Formato DIC | 8 | **10** | ECO: tabela ideal para memorizar (E/A, e', E/e', LAVI) |
| Referências | **10** | 7 | OE: 13 refs. ECO: ASE 2025 |

### Cálculo da Nota Final

| Sistema | Cálculo | **Nota Final** |
|---------|---------|:--------------:|
| **Open Evidence** | (10×0.20)+(10×0.20)+(10×0.20)+(7×0.15)+(8×0.15)+(10×0.10) | **9.25** |
| **ECO RAG** | (8×0.20)+(9×0.20)+(9×0.20)+(10×0.15)+(10×0.15)+(7×0.10) | **8.90** |

### Resumo Teste 5

| | Open Evidence | ECO RAG |
|---|:---:|:---:|
| **NOTA FINAL** | **9.3/10** | **8.9/10** 🏆🏆 |
| Vencedor | ✅ | |
| Destaque | Tratamento completo, 13 refs | **MELHOR NOTA ECO RAG!** Tabela perfeita + ASE 2025 |

### Análise

**Melhor performance do ECO RAG!** Diferença de apenas **0.35 pontos**.

Destaques ECO RAG:
- Tabela de classificação por graus excelente (E/A, e', E/e', LAVI)
- Algoritmo de classificação passo-a-passo
- **Referência atualizada: ASE 2025!** (primeira vez que ECO RAG empata em atualização)
- Formato ideal para prova DIC

Este é o tema mais forte do ECO RAG - função diastólica é core business de ecocardiografia.

---

## Resumo Geral (Atualizado 2026-03-29)

| Teste | Tema | Open Evidence | ECO RAG | Vencedor |
|:-----:|------|:-------------:|:-------:|:--------:|
| 1 | CIV | **8.6** | 7.4 | OE |
| 2 | Tetralogia de Fallot | **9.2** | 8.4 🏆 | OE |
| 3 | Estenose Aórtica | **8.7** | 7.8 | OE |
| 4 | Insuficiência Mitral | **9.1** | 8.4 🏆 | OE |
| 5 | Disfunção Diastólica | **9.3** | 8.9 🏆🏆 | OE |

### Médias Acumuladas

| Sistema | Média | Testes |
|---------|:-----:|:------:|
| Open Evidence | **9.0** | 5 |
| ECO RAG | **8.2** | 5 |

> ✅ **Melhoria:** ECO RAG subiu de 6.5 → **8.2** após correção do prompt ACHD!

---

## Observações Gerais

### Open Evidence
- **Força:** Atualização (2025), profundidade, referências acadêmicas
- **Fraqueza:** Formato extenso, menos prático para consulta rápida

### ECO RAG
- **Força:** Tabelas estruturadas, praticidade clínica, formato escaneável
- **Fraqueza:** Diretrizes desatualizadas (falta 2025), menos referências
- ~~**⚠️ GAP CRÍTICO:** Não possui conteúdo sobre **cardiopatias congênitas (ACHD)**~~ ✅ **RESOLVIDO 2026-03-29**

---

## Diretrizes Faltantes no ECO RAG

> Diretrizes identificadas durante os testes que precisam ser adicionadas ao banco de dados.

### Cardiopatias Congênitas (ACHD)
| Diretriz | Fonte | Ano | Identificado em |
|----------|-------|:---:|-----------------|
| Guidelines for the Management of Adults With Congenital Heart Disease | ESC | 2020 | Teste 2 (TF) |
| Guidelines for the Management of Adults With Congenital Heart Disease | AHA/ACC | 2018 | Teste 2 (TF) |
| Expert Consensus: Management of Infants and Neonates With Tetralogy of Fallot | AATS | 2022 | Teste 2 (TF) |
| 2025 ACC/AHA/HRS/ISACHD/SCAI Guideline for ACHD | ACC/AHA | 2025 | Teste 1 (CIV) |

### Valvopatias
| Diretriz | Fonte | Ano | Identificado em |
|----------|-------|:---:|-----------------|
| Guidelines for the Management of Valvular Heart Disease | ESC/EACTS | 2021 | Teste 3 (EA) |
| Guidelines for the Management of Valvular Heart Disease | ACC/AHA | 2020 | Teste 3 (EA) |

### Outros
| Diretriz | Fonte | Ano | Identificado em |
|----------|-------|:---:|-----------------|
| *Aguardando testes* | | | |

---

## Tasks de Melhoria ECO RAG

> Ações para elevar a nota do ECO RAG para 10/10 em cada tema testado.

### Teste 1: CIV (Nota: 7.4 → Meta: 10)

| Task | Prioridade | Status |
|------|:----------:|:------:|
| Adicionar 2025 ACC/AHA/HRS/ISACHD/SCAI Guideline for ACHD | Alta | [ ] |
| Incluir classificação anatômica dos 4 tipos de CIV | Alta | [ ] |
| Adicionar dados de história natural e fechamento espontâneo | Média | [ ] |
| Incluir indicações de fechamento transcateter vs cirúrgico | Alta | [ ] |

### Teste 2: Tetralogia de Fallot (Nota: ~~0.0~~ 8.4 → Meta: 10) ✅ GAP RESOLVIDO

| Task | Prioridade | Status |
|------|:----------:|:------:|
| ~~**CRÍTICO:** Adicionar conteúdo de cardiopatias congênitas~~ | ~~Alta~~ | [x] ✅ |
| ~~Baixar ESC 2020 Guidelines for ACHD~~ | ~~Alta~~ | [x] ✅ Já indexado |
| ~~Baixar AHA/ACC 2018 Guidelines for ACHD~~ | ~~Alta~~ | [x] ✅ Já indexado |
| Baixar AATS 2022 Expert Consensus on ToF | Média | [ ] |
| ~~Remover filtro "validado para adultos" que bloqueia ACHD~~ | ~~Alta~~ | [x] ✅ Prompt corrigido |
| Incluir timing cirúrgico, complicações, arritmias | Média | [ ] |
| Adicionar mais referências (NEJM, Lancet) | Média | [ ] |

### Teste 3: Estenose Aórtica (Nota: 7.8 → Meta: 10)

| Task | Prioridade | Status |
|------|:----------:|:------:|
| Atualizar referências (PMID 28385280 → ESC 2021, ACC/AHA 2020) | Alta | [ ] |
| Adicionar classificação por estágios (A, B, C, D) | Média | [ ] |
| Incluir dados de mortalidade TAVI vs SAVR 10 anos | Média | [ ] |
| Adicionar figuras/algoritmos de manejo | Baixa | [ ] |

### Teste 4: Insuficiência Mitral (Nota: 8.4 → Meta: 10)

| Task | Prioridade | Status |
|------|:----------:|:------:|
| Adicionar classificação de Carpentier | Alta | [ ] |
| Incluir TEER (MitraClip) - indicações e critérios | Alta | [ ] |
| Adicionar dados de prognóstico (mortalidade 6.3%/ano) | Média | [ ] |
| Incluir mais referências (NEJM, Lancet, JAMA) | Média | [ ] |

### Teste 5: Disfunção Diastólica (Nota: 8.9 → Meta: 10)

| Task | Prioridade | Status |
|------|:----------:|:------:|
| Expandir seção de tratamento (SGLT2i, diuréticos) | Alta | [ ] |
| Adicionar diferenciação ICFEp vs disfunção diastólica isolada | Média | [ ] |
| Incluir mais referências (JACC 2023, AFP 2025) | Média | [ ] |
| Adicionar fisiopatologia dos 3 componentes | Baixa | [ ] |

---

## Próximos Testes Sugeridos

- [x] ~~Estenose aórtica~~ ✅ Teste 3
- [x] ~~Insuficiência mitral~~ ✅ Teste 4 🏆
- [x] ~~Tetralogia de Fallot~~ ✅ Teste 2
- [ ] Coarctação da aorta (congênito - provável gap)
- [x] ~~Disfunção diastólica~~ ✅ Teste 5 🏆🏆
- [ ] Hipertensão pulmonar
- [ ] Endocardite infecciosa

---

*Última atualização: 2026-03-29*
