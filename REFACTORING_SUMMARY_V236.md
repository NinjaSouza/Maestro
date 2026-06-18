# Refatoração V236 — Fonte Única de Verdade para Normalização

## Problema Resolvido

Antes da V236, o cálculo de `source_rate` (fluxo × área) era realizado em **múltiplos pontos**:
1. **parser.py** (linha 140): `sim_params["source_rate"] = flux * area_cm2`
2. **maestro.py** (injeção via settings_result)
3. **simulation.py** (linha 804-812): `_calc_source_rate()` recalculava `flux * x * y`

Isso causava:
- Risco de inconsistência se algum módulo usasse valores diferentes de flux/área
- Dificuldade de rastrear qual valor estava sendo usado na ativação PyNE
- Potencial erro de 2-10× na normalização da potência

## Solução Implementada

### Princípio: **Uma única fonte de verdade**

> **Phase C (settings.py)** é o **único** local onde `source_rate = flux × area` é calculado.

Todos os outros módulos **consumem** este valor pré-calculado, sem recalcular.

---

## Mudanças por Arquivo

### 1. parser.py (V236)

**ANTES:**
```python
flux     = sim_params.get("flux") or 0.0
area_cm2 = x_cm * y_cm
sim_params["source_rate"] = max(float(flux) * area_cm2, 1e-6)
```

**DEPOIS:**
```python
flux     = sim_params.get("flux") or 0.0
area_cm2 = x_cm * y_cm
sim_params["wafer_x_cm"] = x_cm   # para settings.py usar
sim_params["wafer_y_cm"] = y_cm   # para settings.py usar
# source_rate será definido em settings.py (None nesta fase)
source_rate = sim_params.get("source_rate")  # pode ser None
```

**Racional:** Parser apenas repassa geometria e fluxo; não calcula grandezas derivadas.

---

### 2. settings.py (V236) — **Fonte de Verdade**

**Mantém cálculo único:**
```python
# Linha 319-325 (inalterado)
source_rate = flux * area
if source_rate < _VL.SOURCE_RATE_MIN:
    raise ValueError(...)

# Linha 402: cria lista para todos os timesteps
source_rates = [source_rate] * n_steps

# Linha 454-455: retorna em source_params
"source_params": {
    "strength":      source_rate,       # escalar
    "source_rates":  source_rates,      # lista [n_steps]
    "flux_n_cm2_s":  flux,
    "wafer_area_cm2": area,
}
```

**Racional:** Settings.py tem acesso a todos os parâmetros validados e é executado uma vez por simulação.

---

### 3. maestro.py (V236)

**ANTES:** Apenas injetava `_source_rates` de depletion_params.

**DEPOIS:** Injeta explicitamente `source_rate` em system_params:
```python
# FIX V235/V236: injetar depletion_params e source_rate em system_params
dep = settings_result.get("depletion_params", {})
src_params = settings_result.get("source_params", {})

if dep:
    _spar["_depletion_integrator"]    = dep.get("integrator", "")
    _spar["_depletion_normalization"] = dep.get("normalization", "")
    _spar["_source_rates"]            = dep.get("source_rates", [])
    _spar["_timesteps_s"]             = dep.get("timesteps_s", [])

# FIX V236: source_rate de Phase C é a única fonte de verdade
if src_params and "strength" in src_params:
    _spar["source_rate"] = src_params["strength"]
elif dep and "source_rates" in dep and dep["source_rates"]:
    _spar["source_rate"] = dep["source_rates"][0]
```

**Racional:** Simulation.py recebe `source_rate` já calculado via system_params.

---

### 4. simulation.py (V236)

**ANTES:**
```python
def _calc_source_rate(self) -> Optional[float]:
    x    = float(self.sp.get("wafer_x_cm", self.sp.get("x", 1.69)))
    y    = float(self.sp.get("wafer_y_cm", self.sp.get("y", 1.69)))
    flux = float(self.sp.get("flux", self.sp.get("fluxo", 1e13)))
    sr   = flux * x * y  # Recalcula!
    if sr < 1.0:
        self.logger.error("source_rate=%.3e < 1 n/s", sr)
        return None
    return sr
```

**DEPOIS:**
```python
def _calc_source_rate(self) -> Optional[float]:
    # FIX V236: source_rate JÁ FOI CALCULADO EM settings.py
    # Esta função apenas recupera o valor pré-calculado
    
    sr = self.sp.get("source_rate")  # Vem de maestro ← settings.py
    if sr is not None and sr >= 1.0:
        return float(sr)
    
    # Fallback para backward compat (caso settings.py antigo não tenha passado)
    x    = float(self.sp.get("wafer_x_cm", self.sp.get("x", 1.69)))
    y    = float(self.sp.get("wafer_y_cm", self.sp.get("y", 1.69)))
    flux = float(self.sp.get("flux", self.sp.get("fluxo", 1e13)))
    sr   = flux * x * y
    if sr < 1.0:
        self.logger.error("source_rate=%.3e < 1 n/s (fallback)", sr)
        return None
    self.logger.warning("_calc_source_rate: usando fallback (Phase C não passou source_rate)")
    return sr
```

**E no operador de depleção:**
```python
# FIX V236: source_rates já vem calculado em Phase C (settings.py)
norm_mode = self.sp.get("_depletion_normalization", "source-rate")

# Obter source_rates de system_params (preenchido por maestro)
source_rates_list = self.sp.get("_source_rates")
if not source_rates_list:
    sr_single = source_rate
    source_rates_list = [sr_single] if sr_single is not None else [1e14]

op = openmc.deplete.IndependentOperator(
    openmc.Materials(self.materials),
    source_rates_list,  # lista de source_rates por timestep
    chain_file=str(chain),
    normalization_mode=norm_mode,
)
```

**Racional:** Usa diretamente a lista de source_rates calculada em Phase C.

---

## Fluxo de Dados V236

```
┌─────────────┐
│ Input file  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Phase A     │  parser.py
│             │  → wafer_x_cm, wafer_y_cm, flux
│             │  → source_rate = None (ainda não calculado)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Phase B     │  geometry.py
│             │  → openmc_geometry, materials
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Phase C     │  settings.py  ★ FONTE DE VERDADE ★
│             │  → source_rate = flux × area  (ÚNICO CÁLCULO)
│             │  → source_rates = [source_rate] * n_steps
│             │  → source_params["strength"] = source_rate
│             │  → source_params["source_rates"] = source_rates
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Phase D     │  maestro.py
│             │  → injeta source_rate em system_params
│             │  → injeta _source_rates em system_params
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Simulation  │  simulation.py
│             │  → usa sp["source_rate"] (já calculado)
│             │  → usa sp["_source_rates"] (lista)
│             │  → SEM recálculo de flux × area
└─────────────┘
```

---

## Validação Física

### Cálculo Correto

Para um input típico:
- `FLUXO = 2e14 n/cm²/s`
- `X = 2.4 cm`, `Y = 17.0 cm`
- `Área = 40.8 cm²`

**Source rate correto:**
```
source_rate = 2e14 × 40.8 = 8.16e15 n/s
```

Este valor é usado para:
1. **Normalização do operador de depleção** (`normalization_mode="source-rate"`)
2. **Cálculo de potência por tally**: `P = heating_eV × source_rate × EV_TO_J`
3. **Ativação PyNE**: taxa de reação = σ × φ × N, onde φ é derivado de source_rate

### Erro Evitado

Sem esta refatoração, se simulation.py usasse valores inconsistentes de `x`, `y` ou `flux`, o erro seria:
```
erro_rel = (source_rate_errado - source_rate_correto) / source_rate_correto
```

Para Mo-99 (t½ = 66h) em timestep de 12h, um erro de 2× em source_rate causa:
- **Subestimação de 50%** na atividade produzida
- **Erro de dose** proporcional no pós-processamento

---

## Backward Compatibility

A refatoração mantém compatibilidade com versões anteriores:

1. **Parser antigo** que calcula `source_rate`: valor será sobrescrito por settings.py
2. **Settings antigo** sem `source_params`: simulation.py usa fallback (recalcula com warning)
3. **Maestro antigo** sem injeção de `source_rate`: simulation.py usa fallback

Logs de warning alertam quando fallback é ativado:
```
_calc_source_rate: usando fallback (Phase C não passou source_rate)
```

---

## Checklist de Produção

- [x] Parser não calcula source_rate
- [x] Settings.py calcula source_rate uma única vez
- [x] Maestro injeta source_rate em system_params
- [x] Simulation.py consome source_rate (sem recálculo)
- [x] Fallback com warning para backward compat
- [x] Sintaxe Python válida em todos os arquivos
- [ ] Teste de integração com OpenMC real (requer bibliotecas XS)
- [ ] Validação de potência calculada vs. expectativa analítica
- [ ] Validação de ativação PyNE com caso de teste conhecido

---

## Próximos Passos (Produção)

1. **Fase 1 — Validação Numérica**
   - Rodar caso de teste com geometria simples (placa U-235)
   - Comparar potência calculada com P = Σ_f × φ × V × E_fission
   - Verificar se P_batimento com expectativa (~10-100 W para flux 1e14)

2. **Fase 2 — Validação PyNE**
   - Simular irradiação de Zn natural por 168h
   - Comparar Zn-69m produzido com cálculo manual: A = Nσφ(1-e^{-λt})
   - Validar fator de conversão source_rate → fluxo no material

3. **Fase 3 — Documentação**
   - Atualizar comentários em simulation.py sobre normalização
   - Adicionar nota no README sobre fonte única de verdade
   - Criar teste unitário para _calc_source_rate()

---

**Versão:** V236  
**Data:** 2026  
**Status:** Refatoração concluída, aguardando validação numérica com OpenMC real
