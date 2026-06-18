# Relatório de Auditoria: Simulador Nuclear OpenMC-PyNE
**Data:** 2026-04-14  
**Versão do Código:** V236.0 (simulation.py), V304 (tallies.py), V4.0 (pyne_bridge.py)

---

## 1. ERROS DE INTEGRAÇÃO OPENMC-PYNE

### 1.1 Conversão de Tallies para Materiais PyNE ⚠️ CRÍTICO

**Localização:** `pyne_bridge.py` linhas 301-331, `tallies.py` linhas 240-280

**Problema Identificado:**
```python
# pyne_bridge.py:324-325
power_dist[cell_name] = self.heating_eV_to_watts(
    float(row["mean"].sum()), sourcerate_ns
)
```

**Análise:**
- A função `heating_eV_to_watts()` converte corretamente: `score [eV/src] × source_rate [n/s] × EV_TO_J`
- **PORÉM**, não há verificação se o `sourcerate_ns` passado corresponde à normalização real usada no operador de depleção do OpenMC
- O `source_rate` é calculado em `simulation.py:804-812` como `flux × x_cm × y_cm`, mas esta é uma aproximação geométrica simplificada

**Risco:**
- Se a geometria real da fonte não for exatamente retangular com área `x × y`, o source_rate estará errado
- Não há fator de normalização baseado na potência total depositada vs potência esperada

**Recomendação:**
```python
# Adicionar validação pós-simulação
def validate_source_normalization(self, statepoint_file, expected_power_W):
    with openmc.StatePoint(statepoint_file) as sp:
        tally = sp.get_tally(name="kappa-fission")
        total_fission_energy = tally.sum()  # eV/src
        calculated_power = total_fission_energy * self._source_rate * EV_TO_J
        discrepancy = abs(calculated_power - expected_power_W) / expected_power_W
        if discrepancy > 0.05:  # 5% tolerância
            logger.warning(f"Discrepância de normalização: {discrepancy:.2%}")
```

### 1.2 Mapeamento de Composição Isotópica ⚠️ ALTO

**Localização:** `pyne_bridge.py` linhas 213-242 (`to_openmc_material`)

**Situação Atual:**
- O mapeamento de materiais PyNE → OpenMC está **CORRETO**
- Usa `nucname.name(nuc_id)` para conversão de IDs
- Preserva frações mássicas e densidade T-dependente

**Ponto de Atenção:**
```python
# Linha 231-237
for nuc_id, frac in pyne_mat.comp.items():
    if frac <= 0.0:
        continue
    try:
        mat.add_nuclide(nucname.name(nuc_id), float(frac), "wo")
    except Exception as exc:
        _logger.warning("add_nuclide(%s) falhou: %s", nuc_id, exc)
```

**Recomendação:**
- Adicionar log de advertência se >5% da massa total for perdida na conversão
- Validar soma das frações após conversão

---

## 2. PLACEHOLDERS E MOCKS IDENTIFICADOS

### 2.1 Espectro de Fluxo Fixo ⚠️ MÉDIO

**Localização:** `simulation.py` linhas 274-400 (`_build_energy_distribution`)

**Situação:**
- O espectro ORIGEN252 usa um **Mixture analítico** (Maxwell + 1/E + Watt) em vez de dados tabulares completos
- Isso é **INTENCIONAL** e documentado (linhas 302-359) para evitar erro de normalização trapz

**Código Problemático:**
```python
# Linhas 313-359: Construção via Mixture em vez de Tabular completo
if src_label == "ORIGEN252_JEFF30A" and weights:
    w_th   = float(weights.get("thermal",    0.80))
    w_epi  = float(weights.get("epithermal", 0.15))
    w_fast = float(weights.get("fast",       0.05))
    # ... construção analítica
```

**Justificativa Técnica (documentada):**
> "NÃO usar openmc.stats.Tabular com os 252 grupos — a normalização trapz(p, E) é dominada pelos bins epitérmicos (ΔE_epi/ΔE_th ~ 1.6e5) mesmo com w_th=0.92, resultando em <E>~5e4 eV (epitérmico puro) em vez de ~0.025 eV."

**Veredito:** ✅ **ACEITÁVEL** — workaround fisicamente fundamentado

### 2.2 Seções de Choque Mockadas ❌ NÃO ENCONTRADO

**Busca:** `grep -r "mock\|placeholder\|fake"` em todos os arquivos `.py`

**Resultado:** Nenhum mock de cross-section encontrado. O código usa bibliotecas ENDF/B-VIII.0, JEFF-3.3, TENDL reais.

### 2.3 Tempos de Irradiação/Resfriamento Estáticos ⚠️ BAIXO

**Localização:** `config.py` linhas 272-276

```python
DT_H_OUTPUT:       float = 12.0   # passo de saída de inventário [h]
DT_H_DEPLETION:    float = 6.0    # passo interno padrão [h]
TOTAL_TIME_H:      float = 48.0   # tempo total de irradiação [h]
COOLING_TIME_H:    float = 6.0    # tempo de resfriamento [h]
```

**Análise:**
- São valores **DEFAULT**, não hardcoded
- O parser (`parser.py`) lê valores do `Input-simulador.txt`
- Verificado em `maestro.py:1720-1722`:
  ```python
  cooling_time_h = float(
      sim_params.get("cooling_time_h", sim_params.get("tempo_resfriamento_h", SimulationDefaults.COOLING_TIME_H))
  )
  ```

**Veredito:** ✅ **CONFIGURÁVEL PELO USUÁRIO**

---

## 3. CONSISTÊNCIA FÍSICA DA NORMALIZAÇÃO

### 3.1 Cálculo do Source Rate ⚠️ CRÍTICO

**Localização:** `simulation.py` linhas 804-812

```python
def _calc_source_rate(self) -> Optional[float]:
    x    = float(self.sp.get("wafer_x_cm", self.sp.get("x", 1.69)))
    y    = float(self.sp.get("wafer_y_cm", self.sp.get("y", 1.69)))
    flux = float(self.sp.get("flux", self.sp.get("fluxo", 1e13)))
    sr   = flux * x * y  # ← PROBLEMA: assume fonte retangular uniforme
    if sr < 1.0:
        self.logger.error("source_rate=%.3e < 1 n/s", sr)
        return None
    return sr
```

**Problema Físico:**
1. Assume que o fluxo é uniforme sobre toda a área `x × y`
2. Não considera perfil espacial real da fonte (gaussiano? colimado?)
3. Se a fonte for menor que o wafer, o source_rate será **superestimado**
4. Se houver colimação ou blindagem parcial, o source_rate será **superestimado**

**Impacto na Ativação PyNE:**
```
Erro no source_rate → Erro linear na potência depositada → 
Erro linear na taxa de produção de Mo99 → 
Atividade final pode estar errada por fator 2-10×
```

**Solução Recomendada:**
```python
def _calc_source_rate(self) -> Optional[float]:
    # Opção 1: Usar potência total especificada pelo usuário (mais confiável)
    power_W = self.sp.get("power_total_W")
    if power_W and power_W > 0:
        # Inferir source_rate da potência usando kappa-fission médio
        # E_fission ≈ 200 MeV = 3.2e-11 J
        E_PER_FISSION_J = 3.204e-11
        n_fissions_per_s = power_W / E_PER_FISSION_J
        # Assumindo 1 fissão por nêutron absorvido no combustível
        # Fator de correção típico: 0.3-0.7 dependendo da geometria
        efficiency = float(self.sp.get("fission_efficiency", 0.5))
        return n_fissions_per_s / efficiency
    
    # Opção 2: Método atual (fallback)
    x    = float(self.sp.get("wafer_x_cm", self.sp.get("x", 1.69)))
    y    = float(self.sp.get("wafer_y_cm", self.sp.get("y", 1.69)))
    flux = float(self.sp.get("flux", self.sp.get("fluxo", 1e13)))
    
    # Fator de forma: corrige para fontes não-retangulares
    shape_factor = float(self.sp.get("source_shape_factor", 1.0))
    sr = flux * x * y * shape_factor
    
    if sr < 1.0:
        self.logger.error("source_rate=%.3e < 1 n/s", sr)
        return None
    return sr
```

### 3.2 Normalização do Operador de Depleção ✅ CORRETO

**Localização:** `simulation.py` linhas 146-161

```python
norm_mode = self.sp.get("_depletion_normalization", "source-rate")
try:
    op = openmc.deplete.IndependentOperator(
        openmc.Materials(self.materials),
        [flux * self._calc_source_rate() / flux if (flux := ...) else 1.0],
        chain_file=str(chain),
        normalization_mode=norm_mode,  # ← "source-rate" ou "fission-q"
    )
```

**Análise:**
- Modo `"source-rate"`: normaliza pela taxa de fonte especificada (correto para fixed-source)
- Modo `"fission-q"`: normaliza pela energia de fissão total (correto para burnup)
- Configurável via `DEPLETION_NORMALIZATION` no input

**Veredito:** ✅ **IMPLEMENTAÇÃO CORRETA**

### 3.3 Fator EV_TO_J ✅ CORRETO

**Localização:** `config.py` linha 44

```python
EV_TO_J: float = 1.602_176_634e-19   # J/eV (exato CODATA 2018)
```

**Uso consistente em:**
- `pyne_bridge.py:247`
- `tallies.py:130`
- `simulation.py:752, 760`

**Veredito:** ✅ **CONSTANTE FÍSICA CORRETA**

---

## 4. RESUMO DOS PROBLEMAS CRÍTICOS

| # | Problema | Severidade | Arquivo | Impacto Estimado |
|---|----------|------------|---------|------------------|
| 1 | Source rate assume fonte retangular uniforme | 🔴 CRÍTICO | simulation.py:804-812 | 2-10× erro na ativação |
| 2 | Sem validação de normalização pós-simulação | 🟠 ALTO | tallies.py, pyne_bridge.py | Erro sistemático não detectado |
| 3 | Perda silenciosa de nuclídeos na conversão PyNE→OpenMC | 🟡 MÉDIO | pyne_bridge.py:231-237 | <5% erro em composição |
| 4 | Espectro ORIGEN252 aproximado por Mixture | 🟢 BAIXO | simulation.py:313-359 | Intencional, documentado |

---

## 5. PLANO DE CORREÇÃO E IMPLEMENTAÇÃO PARA PRODUÇÃO

### Fase 1: Correções Críticas (Semana 1)

#### 5.1.1 Implementar Source Rate por Potência Total
**Arquivo:** `simulation.py`  
**Mudança:** Adicionar método `_calc_source_rate_from_power()`  
**Prioridade:** 🔴 CRÍTICO

```python
def _calc_source_rate_from_power(self, power_W: float) -> float:
    """Calcula source_rate a partir da potência total especificada."""
    E_PER_FISSION_J = 3.204e-11  # 200 MeV
    n_fissions_per_s = power_W / E_PER_FISSION_J
    efficiency = float(self.sp.get("fission_efficiency", 0.5))
    return n_fissions_per_s / efficiency
```

#### 5.1.2 Adicionar Validação de Normalização
**Arquivo:** `tallies.py`  
**Mudança:** Nova função `validate_normalization()`  
**Prioridade:** 🟠 ALTO

```python
def validate_normalization(statepoint_file, expected_power_W, source_rate):
    """Compara potência calculada vs esperada e alerta se discrepância >5%."""
    with openmc.StatePoint(statepoint_file) as sp:
        tally = sp.get_tally(name="kappa-fission")
        calculated_power = tally.sum() * source_rate * EV_TO_J
        discrepancy = abs(calculated_power - expected_power_W) / expected_power_W
        return discrepancy < 0.05
```

### Fase 2: Melhorias de Robustez (Semana 2)

#### 5.2.1 Validação de Conversão de Materiais
**Arquivo:** `pyne_bridge.py`  
**Mudança:** Adicionar checksum de massa após conversão  
**Prioridade:** 🟡 MÉDIO

```python
def to_openmc_material(self, name: str, ...) -> openmc.Material:
    # ... código existente ...
    total_frac = sum(frac for nuc_id, frac in pyne_mat.comp.items() if frac > 0)
    if abs(total_frac - 1.0) > 0.05:
        _logger.warning(f"Material {name}: perda de {1-total_frac:.2%} na conversão")
```

#### 5.2.2 Logging de Espectro Efetivo
**Arquivo:** `tallies.py`  
**Mudança:** Expandir output de `extract_spectrum_weighted_yield()`  
**Prioridade:** 🟢 BAIXO

### Fase 3: Documentação e Testes (Semana 3)

#### 5.3.1 Criar Suite de Testes de Normalização
**Arquivo:** `tests/test_normalization.py` (novo)

```python
def test_source_rate_rectangular():
    """Testa source_rate para fonte retangular conhecida."""
    pass

def test_source_rate_from_power():
    """Testa cálculo de source_rate a partir de potência."""
    pass

def test_normalization_validation():
    """Testa detecção de erro de normalização."""
    pass
```

#### 5.3.2 Atualizar Input-simulador.txt Template
**Arquivo:** `Input-simulador.txt.template`

Adicionar campos:
```
# Normalização da fonte (escolha UM):
FLUXO = 1e13              # n/cm²/s (método tradicional)
POTENCIA_TOTAL_W = 1000   # W (método recomendado, mais preciso)
FATOR_EFICIENCIA_FISSAO = 0.5  # fração de nêutrons que causam fissão
FATOR_FORMAFonte = 1.0    # 1.0=retangular, 0.785=circular, etc.
```

### Fase 4: Validação Experimental (Semana 4)

#### 5.4.1 Benchmark com Dados Conhecidos
- Comparar resultados com simulações publicadas de produção de Mo99
- Validar atividade específica de Mo99 (Ci/g) contra literatura
- Meta: concordância dentro de ±15%

#### 5.4.2 Sensibilidade a Parâmetros de Normalização
- Variar `fission_efficiency` de 0.3 a 0.7
- Quantificar impacto na atividade final de Mo99
- Documentar faixa de incerteza

---

## 6. CHECKLIST PRÉ-PRODUÇÃO

- [ ] Implementar cálculo de source_rate por potência total
- [ ] Adicionar validação de normalização pós-simulação
- [ ] Criar testes unitários para normalização
- [ ] Atualizar template de input com novos parâmetros
- [ ] Documentar procedimento de calibração de eficiência de fissão
- [ ] Realizar benchmark com dados experimentais publicados
- [ ] Revisar logs de advertência de conversão de materiais
- [ ] Atualizar changelog para V237.0

---

## 7. CONCLUSÃO

O simulador apresenta **boa arquitetura geral** com integração OpenMC-PyNE funcional, mas possui **vulnerabilidade crítica na normalização do source_rate** que pode causar erros de 2-10× nos resultados de ativação. 

As correções propostas nas Fases 1-2 são **essenciais antes de qualquer uso em produção**. As melhorias das Fases 3-4 aumentarão a confiança e rastreabilidade dos resultados.

**Status para Produção:** 🟡 **CONDICIONAL** — requer correções da Fase 1 antes de liberação.
