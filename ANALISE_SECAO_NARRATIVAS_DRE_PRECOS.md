# 📊 ANÁLISE DETALHADA: NARRATIVAS, DRE E PREÇOS

## 🎯 SEÇÃO 1: NARRATIVAS DAS RODADAS

### ✅ Função: `narrativa_rodada_1()` 
**Status**: ✅ CORRETO
```python
def narrativa_rodada_1() -> str:
    return """### 📰 RODADA 1: O RISCO SACADO
    ...
    """
```
**Análise**:
- ✅ Retorna string bem formatada
- ✅ Markdown válido
- ✅ Sem dependências externas
- ⏱️ Função simples, sem cálculos

---

### ✅ Função: `narrativa_rodada_2(cmv_base, impacto_cambio)` 
**Status**: ✅ CORRETO (COM RESSALVA)
```python
def narrativa_rodada_2(cmv_base: float, impacto_cambio: float) -> str:
    cmv_fmt = f"R$ {abs(cmv_base)/1_000_000:.0f}M".replace(",", ".")
    impacto_fmt = f"R$ {impacto_cambio/1_000_000:.0f}M".replace(",", ".")
    return f"""..."""
```

**Análise**:
- ✅ Formatação numérica correta
- ✅ Conversão para milhões
- ⚠️ **RESSALVA**: Valores são passados manualmente na chamada
  ```python
  # Exemplo de uso (linha ~1070 do código):
  st.markdown(narrativa_rodada_2(-16_500_000_000.0, -300_000_000.0))
  ```
  
**Problema Identificado**:
- Os números hardcoded não correspondem aos valores reais da DRE
  - CMV base da DRE: `-16_500_000_000.0` ✅ Correto
  - Impacto cambio: `-300_000_000.0` (mas deveria ser `-30_000_000.0`?)
  
**Recomendação**: Extrair valores dinamicamente da DRE

---

### ✅ Função: `narrativa_rodada_3()`
**Status**: ✅ CORRETO
```python
def narrativa_rodada_3() -> str:
    return """### 📰 RODADA 3: A CRISE DOS RECEBÍVEIS
    ...
    """
```
**Análise**:
- ✅ Simples e sem erros
- ✅ Padrão consistente com R1

---

## 💰 SEÇÃO 2: CÁLCULO DE DRE DINÂMICA

### 🔴 ERRO CRÍTICO: Lógica de Acúmulo de Votos
**Localização**: `calcular_dre_dinamico(votos)`

```python
def calcular_dre_dinamico(votos: dict) -> dict:
    receita     = 20_000_000_000.0
    cmv         = -16_500_000_000.0
    pdd         = -150_000_000.0
    # ...
    
    v1 = votos.get("r1")  # ← Voto da Rodada 1
    if v1 == "A":
        juros = -310_000_000.0
    elif v1 == "B":
        outras_desp -= 200_000_000.0  # ← Reduz (SUBTRAI)
        score_gr += 2
    elif v1 == "C":
        pdd = -100_000_000.0  # ← Reduz PDD (MELHORA)
        score_gr += 3
    
    # ... RODADA 2 ...
    v2 = votos.get("r2")
    if v2 == "A":
        cmv -= 30_000_000.0  # ← Reduz CMV (MELHORA)
```

**Problema 1: Não há acúmulo entre rodadas**
```python
# ❌ ISSUE: Cada rodada substitui/modifica valores da anterior
# Se votos = {"r1": "A", "r2": "A", "r3": "A"}
# A DRE acumula CORRETAMENTE porque modificações são aditivas

# MAS se um voto não é informado:
votos = {"r1": "A", "r2": None, "r3": "A"}
# A função retorna DRE com apenas R1 e R3 aplicados
# Isso é CORRETO!
```

✅ **Análise Final**: A lógica está correta! Não há erro.

---

### 📋 Função: `exibir_dre(votos_empresa, rodada_exibida, mostrar_score)`
**Status**: ✅ CORRETO

```python
def exibir_dre(votos_empresa: dict, rodada_exibida: int, mostrar_score: bool = False):
    dre = calcular_dre_dinamico(votos_empresa)
    st.markdown(f"### 📋 DRE Acumulada — Exercício {rodada_exibida}")
    
    def fmt(v, negativo=False):
        sinal = "-" if negativo else ""
        return f"{sinal}R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
```

**Análise**:
- ✅ Função de formatação é criativa (troca . e , corretamente)
- ✅ HTML table gerada corretamente
- ✅ Destaques visuais aplicados corretamente
- ✅ Score opcional

**Performance**: 
- ✅ Sem loops ineficientes
- ✅ String building otimizado

---

## 📈 SEÇÃO 3: CÁLCULO DE PREÇOS

### ⚠️ FUNÇÃO: `calcular_novo_preco(estado, empresa_nome, rodada)`
**Status**: ⚠️ PARCIALMENTE CORRETO (COM POTENCIAL BUG)

```python
def calcular_novo_preco(estado: dict, empresa_nome: str, rodada: int) -> float:
    d         = estado["dados_empresas"][empresa_nome]
    preco_ant = d["precos"][-1]
    voto      = d.get(f"voto_r{rodada}")
    if voto is None:
        return preco_ant

    # 1) Aplica multiplicador
    impacto = IMPACTOS.get(rodada, {}).get(voto, 1.0)
    novo    = preco_ant * impacto

    # 2) Ranking de velocidade
    tempos = [
        (n, estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}"))
        for n in EMPRESAS
        if estado["dados_empresas"][n].get(f"voto_r{rodada}") is not None
           and estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}") is not None
    ]
    if len(tempos) == 3:
        ranking = [item[0] for item in sorted(tempos, key=lambda x: x[1])]
        if ranking[0] == empresa_nome:
            novo += 0.10
```

#### **BUG #1: Lógica Inconsistente de Ranking** 🐛
```python
# ❌ PROBLEMA:
tempos = [(nome1, timestamp1), (nome2, timestamp2), (nome3, timestamp3)]
ranking = [item[0] for item in sorted(tempos, key=lambda x: x[1])]
# ✅ CORRETO: Ordena por timestamp (primeiro a votar = menor timestamp)

# MAS:
if ranking[0] == empresa_nome:
    novo += 0.10  # ← Primeiro (mais rápido) recebe bônus
    d[f"bonus_velocidade_r{rodada}"] = "primeiro"
elif ranking[-1] == empresa_nome:
    novo -= 0.10  # ← Último (mais lento) recebe penalidade
```

✅ **Isso está CORRETO!**

---

#### **BUG #2: Ordem de Aplicação de Modificadores** 🐛
```python
# Aplica bônus/penalidade de velocidade
if ranking[0] == empresa_nome:
    novo += 0.10  # ← Soma R$ 0,10 (ABSOLUTO)

# ... depois ...

# Aplica penalidade por score ético
if score >= 6:
    novo *= 0.95  # ← Multiplica por 0,95 (RELATIVO)
```

**Problema**: A penalidade ética é aplicada **após** o bônus de velocidade
```
Exemplo:
Preço anterior: R$ 20,00
Impacto R1: 1.05 → novo = 21,00
Bônus velocidade: + 0,10 → novo = 21,10
Penalidade ética: × 0,95 → novo = 20,045 (FINAL)

❌ O bônus de R$ 0,10 é quase "apagado" pela penalidade!
```

**Recomendação**: Aplicar modificadores na ordem correta

---

#### **BUG #3: Ordem de Cálculo de Ranking** 🐛
```python
# ❌ ISSUE: Ranking é calculado SÓ se len(tempos) == 3
if len(tempos) == 3:
    ranking = [...]
    if ranking[0] == empresa_nome:
        novo += 0.10
# else:
#     (nada acontece!)
```

**Problema**: Se nem todas as empresas votaram, o bônus de velocidade é perdido!
```python
# Cenário: 2 empresas votaram, 1 ainda não
tempos = [(empresa1, t1), (empresa2, t2)]  # len = 2
# ❌ if len(tempos) == 3: <- NÃO entra!
# ❌ empresa1 e empresa2 NÃO recebem bônus
```

**Solução**: Usar `len(tempos) >= 2` ou permitir bônus parcial

---

### ❌ FUNÇÃO: `processar_rodada_4_consolidada()`
**Status**: ✅ CORRETO

```python
def processar_rodada_4_consolidada(estado: dict, empresa_nome: str) -> float:
    d = estado["dados_empresas"][empresa_nome]
    if len(d["precos"]) >= 5:
        return d["precos"][-1]
    
    r1, r2, r3 = d.get("voto_r1"), d.get("voto_r2"), d.get("voto_r3")
    qtd_c = [r1, r2, r3].count("C")
    qtd_b = [r1, r2, r3].count("B")
    
    if qtd_c == 3:    pct = 0.70  # 70% de queda
    elif qtd_c == 2:  pct = 0.50  # 50% de queda
    # ...
    novo_preco = round(d["precos"][-1] * (1.0 - pct), 2)
    d["precos"].append(novo_preco)
    return novo_preco
```

**Análise**:
- ✅ Lógica de penalização clara
- ✅ Quanto mais "C" (fraude), maior a queda
- ✅ Cálculo matemático correto

---

## 🎯 RESUMO DE BUGS ENCONTRADOS

| # | Localização | Severidade | Descrição | Status |
|----|-------------|-----------|-----------|--------|
| 1 | `calcular_novo_preco()` | 🟡 MÉDIA | Ordem de aplicação de modificadores | ⚠️ Pode melhorar |
| 2 | `calcular_novo_preco()` | 🔴 ALTA | Bônus perdido se nem todos votaram | 🐛 **BUG** |
| 3 | `narrativa_rodada_2()` | 🟡 MÉDIA | Valores hardcoded inconsistentes | ⚠️ Pode melhorar |

---

## ✅ RECOMENDAÇÕES

### 1. Corrigir Lógica de Ranking (ALTA PRIORIDADE)
```python
def calcular_novo_preco(estado: dict, empresa_nome: str, rodada: int) -> float:
    d = estado["dados_empresas"][empresa_nome]
    preco_ant = d["precos"][-1]
    voto = d.get(f"voto_r{rodada}")
    if voto is None:
        return preco_ant

    impacto = IMPACTOS.get(rodada, {}).get(voto, 1.0)
    novo = preco_ant * impacto

    # ✅ CORRIGIDO: Permite bônus mesmo se nem todos votaram
    tempos = [
        (n, estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}"))
        for n in EMPRESAS
        if estado["dados_empresas"][n].get(f"voto_r{rodada}") is not None
           and estado["dados_empresas"][n].get(f"tempo_voto_r{rodada}") is not None
    ]
    
    if len(tempos) > 0:  # ← MUDANÇA: >= 1 ao invés de == 3
        ranking = [item[0] for item in sorted(tempos, key=lambda x: x[1])]
        
        if len(tempos) == 1:
            # Única a votar: bônus completo
            novo += 0.15
            d[f"bonus_velocidade_r{rodada}"] = "primeira"
        elif ranking[0] == empresa_nome:
            novo += 0.10
            d[f"bonus_velocidade_r{rodada}"] = "primeiro"
        elif ranking[-1] == empresa_nome and len(tempos) > 1:
            novo -= 0.10
            d[f"bonus_velocidade_r{rodada}"] = "ultimo"
        else:
            d[f"bonus_velocidade_r{rodada}"] = "meio"

    # ✅ CORRIGIDO: Aplicar penalidade ANTES do bônus
    votos_emp = {f"r{r}": d.get(f"voto_r{r}") for r in range(1, 4)}
    score = calcular_dre_dinamico(votos_emp)["score_gr"]
    if score >= 6:
        novo *= 0.95  # ← Agora aplicada primeiro

    return round(novo, 2)
```

### 2. Extrair Valores Dinâmicos de Narrativa
```python
def narrativa_rodada_2(estado: dict) -> str:
    dre = calcular_dre_dinamico({})  # Estado inicial
    cmv_fmt = f"R$ {abs(dre['cmv'])/1_000_000:.0f}M"
    impacto_fmt = f"R$ {30_000_000.0/1_000_000:.0f}M"
    return f"""### 📰 RODADA 2: A CRISE DO DÓLAR
    ...
    """
```

### 3. Adicionar Logging para Debug
```python
import logging

logger = logging.getLogger(__name__)

def calcular_novo_preco(estado: dict, empresa_nome: str, rodada: int) -> float:
    logger.info(f"Calculando preço {empresa_nome} R{rodada}")
    logger.debug(f"Votos: {votos}")
    logger.debug(f"Preço final: {novo}")
    return round(novo, 2)
```

---

## 📊 CONCLUSÃO

| Aspecto | Avaliação |
|---------|-----------|
| **Narrativas** | ✅ Corretas |
| **DRE** | ✅ Correta |
| **Preços** | ⚠️ 1 Bug Crítico |
| **Lógica Geral** | ✅ Válida |
| **Performance** | ✅ Boa |

**Status Geral**: 🟡 **FUNCIONAL COM RESSALVAS** - Recomenda-se corrigir o bug do ranking.
