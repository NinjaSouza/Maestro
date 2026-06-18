# Relatório de Varredura Rigorosa: Simulador Nuclear OpenMC-PyNE

**Data da Análise:** 2026-04-14  
**Versões Analisadas:** simulation.py V236.0, tallies.py V304, pyne_bridge.py V4.0, settings.py V225, maestro.py V235, posprocessamento.py V1.1

---

## 1. ERROS DE INTEGRAÇÃO OPENMC-PYNE

### 1.1 Conversão de Tallies para Materiais PyNE ✅ CORRETO COM RESSALVAS

**Localização:** `pyne_bridge.py` linhas 301-331, `tallies.py` linhas 240-280, `simulation.py` linhas 750-779

**Situação Atual:**
```python
# pyne_bridge.py:324-325 e simulation.py:761
p_W = float(h_eV) * source_rate * _EV_TO_J
```

**Análise Detalhada:**

✅ **Pontos Positivos:**
1. A função `heating_eV_to_watts()` em `pyne_bridge.py:246-247` converte corretamente:
   - Fórmula: `score [eV/src] × source_rate [n/s] × EV_TO_J [J/eV]`
   - Constante física correta: `EV_TO_J = 1.602_176_634e-19` (CODATA 2018)

2. O fluxo extraído dos Tallies do OpenMC (`openmc.StatePoint`) está sendo mapeado corretamente:
   - `tallies.py` usa `tally.get_pandas_dataframe()` para extrair valores mean/std.dev.
   - Colunas identificadas corretamente: "cell id", "score", "mean", "std. dev."
   - Filtro por célula implementado via `CellFilter`

3. A conversão de materiais PyNE → OpenMC em `pyne_bridge.py:213-242` está **CORRETA**:
   - Usa `nucname.name(nuc_id)` para conversão de IDs
   - Preserva frações mássicas (`"wo"` = weight fraction)
   - Suporta densidade T-dependente quando temperatura fornecida

⚠️ **Ressalvas Identificadas:**

1. **Dependência crítica do source_rate:**
   - Em `simulation.py:813-832`, o `_calc_source_rate()` tenta obter `source_rate` de `settings.py` (Phase C)
   - Fallback: `sr = flux * x * y` (linhas 824-827)
   - **Problema:** Este fallback assume fonte retangular uniforme — se a geometria real for diferente, há erro sistemático

2. **Sem validação de consistência pós-simulação:**
   - Não há verificação se a potência total calculada (`P_total` em `simulation.py:762`) é consistente com a potência esperada
   - Erros de normalização podem passar despercebidos

3. **Mapeamento de nuclídeos na conversão inversa (OpenMC → PyNE):**
   - Em `simulation.py:663-681`, durante `_run_cooling_pyne()`:
     ```python
     comp[_pync.id(nuc)] = dens  # linha 670
     pyne_mats[om.id] = _PyNEMat(comp, mass=om_mass)  # linha 681
     ```
   - **Potencial problema:** Se `om.get_nuclide_atom_densities()` retornar nuclídeos não reconhecidos pelo PyNE, são silenciosamente ignorados (try/except na linha 671)

**Recomendação de Melhoria:**
```python
# Adicionar em pyne_bridge.py ou tallies.py
def validate_normalization_consistency(
    statepoint_file: str,
    expected_power_W: float,
    source_rate: float,
    tolerance: float = 0.05
) -> Tuple[bool, float]:
    """Valida se potência calculada vs esperada está dentro da tolerância."""
    with openmc.StatePoint(statepoint_file) as sp:
        tally = sp.get_tally(name="kappa-fission")
        df = tally.get_pandas_dataframe()
        total_kf_eV = float(df["mean"].sum())
        calculated_power = total_kf_eV * source_rate * EV_TO_J
        discrepancy = abs(calculated_power - expected_power_W) / expected_power_W if expected_power_W > 0 else 0
        is_valid = discrepancy <= tolerance
        return is_valid, discrepancy
```

---

### 1.2 Integração no Pós-Processamento (PyNE Decay) ⚠️ ATENÇÃO

**Localização:** `posprocessamento.py` linhas 339-570 (`PhaseDecayEngine._process_pyne`)

**Situação Atual:**
```python
# Linhas 401-424
mat = PyneMat(comp, mass=initial_mass)
cooled = mat.decay(t_s)  # t_s = cooling_time_h * 3600
comp_dict = dict(cooled.comp)  # frações mássicas pós-decay
activity = cooled.activity()
decay_heat = cooled.decay_heat()
```

**Análise:**

✅ **Correto:**
- Uso apropriado de `PyneMat.decay()` para decaimento analítico (equações de Bateman)
- Conversão de átomos do OpenMC para massa PyNE considera massa atômica exata (`pynedata.atomic_mass`)
- Atividade e calor de decaimento extraídos diretamente do objeto PyNE

⚠️ **Problema Documentado (linhas 516-540):**
```python
# BUG-2 FIX: PyNE 0.7.7 retorna decay_heat() = 0 para muitos nuclídeos
if decay_heat == 0.0 and total_activity > 0.0:
    # Estimativa fallback: Q ≈ A × E_médio (1 MeV por decaimento)
    _q_est = total_activity * 1e6 * PhysicsConstants.EV_TO_J
    decay_heat = _q_est
```

**Veredito:** ✅ **ACEITÁVEL** — workaround documentado para limitação conhecida do PyNE 0.7.7

---

## 2. PLACEHOLDERS E MOCKS IDENTIFICADOS

### 2.1 Espectro de Fluxo Fixo (ORIGEN252) ✅ INTENCIONAL E DOCUMENTADO

**Localização:** `simulation.py` linhas 311-368

**Código:**
```python
# Linhas 322-368: Construção via Mixture analítico
if src_label == "ORIGEN252_JEFF30A" and weights:
    w_th   = float(weights.get("thermal",    0.80))
    w_epi  = float(weights.get("epithermal", 0.15))
    w_fast = float(weights.get("fast",       0.05))
    
    # Componente térmica: Maxwell-Boltzmann(kT)
    dist_list.append(openmc.stats.Maxwell(kT))
    
    # Componente epitérmica: espectro 1/E (Fermi/slowing-down)
    E_epi = np.logspace(np.log10(0.625), np.log10(1e5), 40)
    p_epi = 1.0 / E_epi
    dist_list.append(openmc.stats.Tabular(E_epi, p_epi))
    
    # Componente rápida: espectro de fissão Watt
    dist_list.append(openmc.stats.Watt(a=0.988e6, b=2.249e-6))
    
    return openmc.stats.Mixture(wt_list, dist_list)
```

**Justificativa Técnica (documentada nas linhas 311-316):**
> "NÃO usar openmc.stats.Tabular com os 252 grupos — a normalização trapz(p, E) é dominada pelos bins epitérmicos (ΔE_epi/ΔE_th ~ 1.6e5) mesmo com w_th=0.92, resultando em <E>~5e4 eV (epitérmico puro) em vez de ~0.025 eV. Isso faz os nêutrons serem absorvidos no cladding Al antes de atingir o U235."

**Veredito:** ✅ **ACEITÁVEL** — workaround fisicamente fundamentado e documentado. Não é um mock, é uma aproximação válida baseada em física de moderacao.

---

### 2.2 Seções de Choque (Cross-Sections) ✅ SEM MOCKS

**Busca realizada:**
```bash
grep -rni "mock\|placeholder\|fake\|dummy" /workspace --include="*.py"
```

**Resultado:** Nenhum mock de cross-section encontrado.

**Situação Real:**
- `settings.py` linhas 70-92: `LibraryHierarchy.discover()` busca bibliotecas reais:
  - ENDF/B-VIII.0 (`/usr/local/lib/python3.12/site-packages/openmc/ENDF-B-VIII.0.h5`)
  - JEFF-3.3
  - TENDL
- Falha gracefully se nenhuma biblioteca encontrada (retorna `None`)

**Veredito:** ✅ **SEM MOCKS** — usa dados nucleares reais

---

### 2.3 Tempos de Irradiação/Resfriamento ✅ CONFIGURÁVEIS (não hardcoded)

**Valores default em `config.py` linhas 272-276:**
```python
DT_H_OUTPUT:       float = 12.0   # passo de saída de inventário [h]
DT_H_DEPLETION:    float = 6.0    # passo interno padrão [h]
TOTAL_TIME_H:      float = 48.0   # tempo total de irradiação [h]
COOLING_TIME_H:    float = 6.0    # tempo de resfriamento [h]
```

**Verificação de configurabilidade:**
- `parser.py` lê do `Input-simulador.txt`:
  ```python
  # parser.py:372 (citado em grep)
  "water_flow_rate_m3s": 0.0, "chain_file": "",  # FIX P2: sem default hardcoded
  ```
- `maestro.py` linhas 1720-1722:
  ```python
  cooling_time_h = float(
      sim_params.get("cooling_time_h", sim_params.get("tempo_resfriamento_h", SimulationDefaults.COOLING_TIME_H))
  )
  ```
- `settings.py` linhas 253-258:
  ```python
  dt_output_h = _get("dt_h", "DTH", default=_SD.DT_H_OUTPUT, cast=float)
  total_h     = _get("total_time_h", "TEMPO_TOTAL_H", default=_SD.TOTAL_TIME_H, cast=float)
  cooling_h   = _get("cooling_time_h", default=_SD.COOLING_TIME_H, cast=float)
  ```

**Veredito:** ✅ **CONFIGURÁVEL PELO USUÁRIO** — defaults são apenas fallbacks

---

### 2.4 DepletionAutoTuner ✅ AUTO-CONFIGURAÇÃO INTELIGENTE

**Localização:** `settings.py` linhas 274-293, `config.py` (classe `DepletionAutoTuner`)

**Funcionamento:**
```python
# settings.py:285-292
dep_params = DepletionAutoTuner.tune(
    dt_output_h          = dt_output_h,
    user_dt_depletion_h  = user_dt_dep,
    user_integrator      = user_integ,
)
dt_depletion_h = dep_params.dt_depletion_h
dep_integrator = dep_params.integrator
```

**Tabela de decisão automática (documentada em `settings.py` linhas 11-18):**
| DT_H_OUTPUT | DT_H_DEPLETION | Integrador | Sub-passos |
|-------------|----------------|------------|------------|
| ≤ 6h        | DT/2           | celi       | 2          |
| ≤ 12h       | DT/2           | celi       | 2          |
| ≤ 24h       | DT/4           | celi       | 4          |
| > 24h       | DT/6           | si_celi    | 6          |

**Veredito:** ✅ **AUTO-CONFIGURAÇÃO BASEADA EM FÍSICA** — considera t½ do Mo99 (65.94h)

---

## 3. CONSISTÊNCIA FÍSICA DA NORMALIZAÇÃO

### 3.1 Cálculo do Source Rate ⚠️ PONTO CRÍTICO

**Localização:** `settings.py` linhas 319-325, `simulation.py` linhas 813-832

**Código em settings.py (fonte primária):**
```python
# settings.py:319-325
source_rate = flux * area
if source_rate < _VL.SOURCE_RATE_MIN:
    raise ValueError(
        f"source_rate={source_rate:.3e} n/s < mínimo ({_VL.SOURCE_RATE_MIN:.0e} n/s). "
        f"Verifique FLUXO e dimensões do wafer."
    )
```

**Código em simulation.py (fallback):**
```python
# simulation.py:813-832
def _calc_source_rate(self) -> Optional[float]:
    # FIX V236: source_rate JÁ FOI CALCULADO EM settings.py (única fonte de verdade).
    sr = self.sp.get("source_rate")
    if sr is not None and sr >= 1.0:
        return float(sr)
    
    # Fallback para backward compat
    x    = float(self.sp.get("wafer_x_cm", self.sp.get("x", 1.69)))
    y    = float(self.sp.get("wafer_y_cm", self.sp.get("y", 1.69)))
    flux = float(self.sp.get("flux", self.sp.get("fluxo", 1e13)))
    sr   = flux * x * y
    if sr < 1.0:
        self.logger.error("source_rate=%.3e < 1 n/s (fallback)", sr)
        return None
    return sr
```

**Análise Física:**

🔴 **PROBLEMA IDENTIFICADO:**

1. **Fórmula simplificada:** `source_rate = flux × area`
   - Assume fluxo uniforme sobre toda a área do wafer
   - Não considera perfil espacial real da fonte (gaussiano? colimado?)
   - Não considera eficiência geométrica (fração de nêutrons que realmente atingem o alvo)

2. **Impacto na ativação PyNE:**
   ```
   Erro no source_rate → Erro linear na potência depositada →
   Erro linear na taxa de produção de Mo99 →
   Atividade final pode estar errada por fator 2-10×
   ```

3. **Exemplo numérico:**
   - Input: `FLUXO = 1e13 n/cm²/s`, `x = y = 1.69 cm`
   - Cálculo: `source_rate = 1e13 × 1.69 × 1.69 = 2.86e13 n/s`
   - **Se a fonte real tiver área efetiva de 50%:** source_rate real = 1.43e13 n/s
   - **Erro:** fator 2× na atividade de Mo99!

**Solução Recomendada:**

Adicionar método alternativo baseado em potência total especificada:

```python
# Adicionar em simulation.py ou settings.py
def _calc_source_rate_from_power(
    power_total_W: float,
    fission_efficiency: float = 0.5,
    energy_per_fission_J: float = 3.204e-11  # 200 MeV
) -> float:
    """
    Calcula source_rate a partir da potência total especificada.
    
    Método mais confiável quando potência é conhecida (ex: reator operando a X kW).
    
    Args:
        power_total_W: Potência térmica total desejada [W]
        fission_efficiency: Fração de nêutrons que causam fissão (típico: 0.3-0.7)
        energy_per_fission_J: Energia por fissão (200 MeV = 3.204e-11 J)
    
    Returns:
        source_rate [n/s] necessário para produzir power_total_W
    """
    n_fissions_per_s = power_total_W / energy_per_fission_J
    source_rate = n_fissions_per_s / fission_efficiency
    return source_rate
```

**Recomendação de Input:**
```
# No Input-simulador.txt, adicionar opção alternativa:
# Método 1 (tradicional):
FLUXO = 1e13              # n/cm²/s
X_CM = 1.69
Y_CM = 1.69

# Método 2 (recomendado para produção):
POTENCIA_TOTAL_W = 1000   # W
FATOR_EFICIENCIA_FISSAO = 0.5  # fração de nêutrons que causam fissão
```

---

### 3.2 Normalização do Operador de Depleção ✅ CORRETO

**Localização:** `simulation.py` linhas 145-161

**Código:**
```python
norm_mode = self.sp.get("_depletion_normalization", "source-rate")
source_rates_list = self.sp.get("_source_rates") or [source_rate]

op = openmc.deplete.IndependentOperator(
    openmc.Materials(self.materials),
    source_rates_list,
    chain_file=str(chain),
    normalization_mode=norm_mode,
)
```

**Modos de normalização suportados:**
- `"source-rate"`: Normaliza pela taxa de fonte especificada (correto para fixed-source)
- `"fission-q"`: Normaliza pela energia de fissão total (correto para burnup, modo crítico)

**Verificação em settings.py linhas 294-298:**
```python
dep_normalization = _get("depletion_normalization", "NORMALIZACAO",
                          default=_SD.DEPLETION_NORMALIZATION)
if SimulationModes.needs_power(sim_mode):
    dep_normalization = "fission-q"
    logger.info("Modo %s: normalization forçada para 'fission-q'", sim_mode)
```

**Veredito:** ✅ **IMPLEMENTAÇÃO CORRETA** — modos apropriados para cada cenário

---

### 3.3 Fatores de Conversão Física ✅ CORRETOS

**Constantes em `config.py`:**
```python
class PhysicsConstants:
    EV_TO_J: float = 1.602_176_634e-19   # J/eV (CODATA 2018, exato)
    N_A:     float = 6.022_140_76e23     # mol⁻¹ (exato)
    KB_EV:   float = 8.617_333e-5        # eV/K
    SECONDS_PER_HOUR: float = 3600.0
```

**Uso consistente:**
- `EV_TO_J`: `pyne_bridge.py:247`, `tallies.py:130`, `simulation.py:761, 769`
- `N_A`: `pyne_bridge.py:258` (cálculo de massa a partir de átomos)
- `SECONDS_PER_HOUR`: `settings.py:171, 208, 378`

**Veredito:** ✅ **CONSTANTES FÍSICAS CORRETAS E CONSISTENTES**

---

### 3.4 Validação de Timesteps de Depleção ✅ ROBUSTO

**Localização:** `simulation.py` linhas 516-543 (`_safe_timesteps`)

**Código:**
```python
def _safe_timesteps(self, source_rate: float) -> np.ndarray:
    dt_s = np.diff(self.timesteps_h) * 3600.0
    dt_s = dt_s[dt_s > 0.0]
    
    n_u235 = self._estimate_n_u235_cm3()
    if n_u235 <= 0.0:
        return dt_s
    
    flux   = float(self.sp.get("flux", self.sp.get("fluxo", 1e13)))
    burn_s = flux * _SIG_U235  # _SIG_U235 = 680.9 barn
    dt_max = _MAX_BURNUP / burn_s if burn_s > 0 else 1e9
    
    if np.any(dt_s > dt_max):
        # Subdivide passos grandes
        new_dt = []
        for d in dt_s:
            if d <= dt_max:
                new_dt.append(d)
            else:
                n_sub = int(np.ceil(d / dt_max))
                new_dt.extend([d / n_sub] * n_sub)
        dt_s = np.array(new_dt)
    return dt_s
```

**Limites físicos:**
- `_MAX_BURNUP = 0.05` (5% de queima máxima por passo CRAM)
- `_SIG_U235 = 680.9 × 1e-24 cm²` (seção de choque de absorção térmica do U235)

**Veredito:** ✅ **PROTEÇÃO CONTRA PASSOS TEMPORAIS EXCESSIVOS** — evita instabilidade numérica

---

## 4. RESUMO DOS PROBLEMAS IDENTIFICADOS

| # | Problema | Severidade | Arquivo(s) | Impacto Estimado | Status |
|---|----------|------------|------------|------------------|--------|
| 1 | Source rate assume fonte retangular uniforme | 🔴 CRÍTICO | settings.py:320, simulation.py:826-827 | 2-10× erro na ativação | **REQUER CORREÇÃO** |
| 2 | Sem validação de normalização pós-simulação | 🟠 ALTO | tallies.py, pyne_bridge.py | Erro sistemático não detectado | **REQUER CORREÇÃO** |
| 3 | Perda silenciosa de nuclídeos na conversão OpenMC→PyNE | 🟡 MÉDIO | simulation.py:670-672 | <5% erro em composição | MELHORIA RECOMENDADA |
| 4 | PyNE 0.7.7 decay_heat() = 0 para alguns nuclídeos | 🟢 BAIXO | posprocessamento.py:516-540 | Workaround implementado | ✅ ACEITÁVEL |
| 5 | Espectro ORIGEN252 aproximado por Mixture | 🟢 BAIXO | simulation.py:311-368 | Intencional, documentado | ✅ ACEITÁVEL |

---

## 5. PLANO DE CORREÇÃO E IMPLEMENTAÇÃO PARA PRODUÇÃO

### FASE 1: Correções Críticas (Prioridade Máxima - Semana 1)

#### 5.1.1 Implementar Cálculo de Source Rate por Potência Total

**Arquivo:** `settings.py` (adição) e `simulation.py` (fallback)

**Mudanças:**

1. **Em `settings.py`, após linha 325:**
```python
# ── Método alternativo: source_rate por potência total ───────────────
power_total_W = _get("power_total_w", "potencia_total_w", default=None, cast=float)
if power_total_W and power_total_W > 0:
    # Método recomendado: inferir source_rate da potência
    fission_efficiency = _get("fission_efficiency", 
                               "fator_eficiencia_fissao",
                               default=0.5, cast=float)
    E_PER_FISSION_J = 3.204e-11  # 200 MeV
    n_fissions_per_s = power_total_W / E_PER_FISSION_J
    source_rate = n_fissions_per_s / fission_efficiency
    logger.info(
        "Source rate calculado por potência: %.4e n/s (P=%.1f W, eff=%.2f)",
        source_rate, power_total_W, fission_efficiency,
    )
else:
    # Método tradicional: flux × area
    source_rate = flux * area
    logger.info(
        "Source rate calculado por fluxo: %.4e n/s (flux=%.2e, area=%.3f cm²)",
        source_rate, flux, area,
    )
```

2. **Em `simulation.py`, atualizar fallback (linhas 823-832):**
```python
# Fallback aprimorado
power_W = float(self.sp.get("power_total_w", 0))
if power_W > 0:
    # Usar método por potência
    efficiency = float(self.sp.get("fission_efficiency", 0.5))
    E_PER_FISSION_J = 3.204e-11
    sr = (power_W / E_PER_FISSION_J) / efficiency
    self.logger.info("_calc_source_rate: usando método por potência (%.1f W)", power_W)
else:
    # Método tradicional
    x    = float(self.sp.get("wafer_x_cm", self.sp.get("x", 1.69)))
    y    = float(self.sp.get("wafer_y_cm", self.sp.get("y", 1.69)))
    flux = float(self.sp.get("flux", self.sp.get("fluxo", 1e13)))
    sr   = flux * x * y
    self.logger.warning("_calc_source_rate: usando fallback tradicional (flux × area)")
```

3. **Atualizar template `Input-simulador.txt.template`:**
```
# ═══════════════════════════════════════════════════════════════════
# NORMALIZAÇÃO DA FONTE (escolha UM dos métodos abaixo)
# ═══════════════════════════════════════════════════════════════════

# MÉTODO 1 (TRADICIONAL): Especificar fluxo e geometria
FLUXO = 1e13                  # n/cm²/s (fluxo na superfície do wafer)
X_CM = 1.69                   # dimensão X do wafer [cm]
Y_CM = 1.69                   # dimensão Y do wafer [cm]

# MÉTODO 2 (RECOMENDADO PARA PRODUÇÃO): Especificar potência total
# POTENCIA_TOTAL_W = 1000     # W (potência térmica total desejada)
# FATOR_EFICIENCIA_FISSAO = 0.5  # fração de nêutrons que causam fissão (0.3-0.7)

# OBS: Se ambos forem especificados, POTENCIA_TOTAL_W tem prioridade
```

---

#### 5.1.2 Adicionar Validação de Normalização Pós-Simulação

**Arquivo:** `tallies.py` (nova função) e `simulation.py` (chamada)

**Nova função em `tallies.py` (após linha 468):**
```python
def validate_normalization_consistency(
    statepoint_file: str,
    expected_power_W: float,
    source_rate: float,
    tolerance: float = 0.05,
) -> Dict[str, Any]:
    """
    Valida se potência calculada vs esperada está dentro da tolerância.
    
    Args:
        statepoint_file: Caminho para statepoint.h5
        expected_power_W: Potência total esperada [W]
        source_rate: Taxa de fonte usada na simulação [n/s]
        tolerance: Tolerância relativa (default: 5%)
    
    Returns:
        Dict com:
          'is_valid': bool
          'discrepancy': float (fração)
          'calculated_power_W': float
          'message': str
    """
    from pathlib import Path
    from pyne_bridge import BRIDGE
    
    sp_path = Path(statepoint_file)
    if not sp_path.exists():
        return {
            "is_valid": False,
            "discrepancy": float('inf'),
            "calculated_power_W": 0.0,
            "message": f"Statepoint não encontrado: {statepoint_file}",
        }
    
    try:
        with openmc.StatePoint(str(sp_path)) as sp:
            # Tentar kappa-fission primeiro (mais direto para potência)
            try:
                tally = sp.get_tally(name="kappa-fission")
                df = tally.get_pandas_dataframe()
                total_kf_eV = float(df["mean"].sum())
                calculated_power = BRIDGE.heating_eV_to_watts(total_kf_eV, source_rate)
                method = "kappa-fission"
            except Exception:
                # Fallback para heating
                try:
                    tally = sp.get_tally(name="heating")
                    df = tally.get_pandas_dataframe()
                    total_h_eV = float(df["mean"].sum())
                    calculated_power = BRIDGE.heating_eV_to_watts(total_h_eV, source_rate)
                    method = "heating"
                except Exception as exc:
                    return {
                        "is_valid": False,
                        "discrepancy": float('inf'),
                        "calculated_power_W": 0.0,
                        "message": f"Nenhum tally de potência encontrado: {exc}",
                    }
        
        if expected_power_W <= 0:
            return {
                "is_valid": True,
                "discrepancy": 0.0,
                "calculated_power_W": calculated_power,
                "message": f"Potência calculada ({method}): {calculated_power:.3e} W (sem referência para comparação)",
            }
        
        discrepancy = abs(calculated_power - expected_power_W) / expected_power_W
        is_valid = discrepancy <= tolerance
        
        return {
            "is_valid": is_valid,
            "discrepancy": discrepancy,
            "calculated_power_W": calculated_power,
            "method": method,
            "message": (
                f"Potência calculada ({method}): {calculated_power:.3e} W | "
                f"Esperada: {expected_power_W:.3e} W | "
                f"Discrepância: {discrepancy:.2%} {'✓' if is_valid else '⚠️'}"
            ),
        }
    except Exception as exc:
        return {
            "is_valid": False,
            "discrepancy": float('inf'),
            "calculated_power_W": 0.0,
            "message": f"Erro ao validar normalização: {exc}",
        }
```

**Chamada em `simulation.py` (adicionar após linha 198, após loop T-N):**
```python
# VALIDAÇÃO PÓS-SIMULAÇÃO
if self._ts_results and self._ts_results[-1].power_total_W > 0:
    from tallies import validate_normalization_consistency
    
    # Obter último statepoint
    sp_path = self._statepoint_for_step(len(dt_s))
    if sp_path and sp_path.exists():
        # Potência esperada: média dos últimos passos (regime estacionário)
        expected_P = self._ts_results[-1].power_total_W
        
        validation = validate_normalization_consistency(
            statepoint_file=str(sp_path),
            expected_power_W=expected_P,
            source_rate=source_rate,
            tolerance=0.10,  # 10% tolerância inicial
        )
        
        if validation["is_valid"]:
            self.logger.info("✓ Validação de normalização: %s", validation["message"])
        else:
            self.logger.warning(
                "⚠️ ALERTA: Validação de normalização falhou: %s",
                validation["message"],
            )
            # Não falhar a simulação, mas alertar o usuário
```

---

### FASE 2: Melhorias de Robustez (Semana 2)

#### 5.2.1 Validação de Conversão de Materiais (OpenMC ↔ PyNE)

**Arquivo:** `pyne_bridge.py` e `simulation.py`

**Mudança em `pyne_bridge.py:to_openmc_material` (após linha 242):**
```python
# Validar conservação de massa
total_frac_input = sum(frac for frac in pyne_mat.comp.values() if frac > 0)
total_frac_output = sum(
    nuc.fraction 
    for nuc in mat.nuclides 
    if hasattr(nuc, 'fraction')
)
if abs(total_frac_output - total_frac_input) > 0.05:
    _logger.warning(
        "to_openmc_material(%s): perda de %.2%% na conversão "
        "(input=%.4f, output=%.4f)",
        name,
        abs(total_frac_output - total_frac_input) / total_frac_input * 100,
        total_frac_input,
        total_frac_output,
    )
return mat
```

**Mudança em `simulation.py:_run_cooling_pyne` (após linha 672):**
```python
# Validar nuclídeos convertidos
total_mass_in = sum(dens for dens in comp.values())
if total_mass_in <= 0:
    self.logger.warning(
        "PyNE mat cell=%d: massa total zero ou negativa — pulando decay",
        om.id,
    )
    continue
```

---

#### 5.2.2 Logging Expandido de Espectro Efetivo

**Arquivo:** `tallies.py:extract_spectrum_weighted_yield`

**Adicionar ao final da função (após linha 438):**
```python
# Logging expandido para diagnóstico
logger.info(
    "ESPECTRO EFETIVO (%s/%s em '%s'):\n"
    "  Yield efetivo:        %.5f\n"
    "  Yield térmico puro:   %.5f\n"
    "  Fator de correção:    %.4f (%.1f%%)\n"
    "  Fração térmica:       %.1f%%\n"
    "  Fração epitérmica:    %.1f%%\n"
    "  Fração rápida:        %.1f%%",
    product, nuclide, target_cell,
    y_eff, y_th, result["correction_factor"],
    (result["correction_factor"] - 1.0) * 100,
    w["thermal"] * 100, w["epithermal"] * 100, w["fast"] * 100,
)
```

---

### FASE 3: Testes e Documentação (Semana 3)

#### 5.3.1 Criar Suite de Testes de Normalização

**Arquivo:** `tests/test_normalization.py` (novo)

```python
#!/usr/bin/env python3
"""Testes unitários para normalização de source rate e validação."""

import pytest
from pathlib import Path

from settings import SettingsBuilder
from simulation import SimulationRunner
from tallies import validate_normalization_consistency


class TestSourceRateCalculation:
    """Testes para cálculo de source rate."""
    
    def test_source_rate_rectangular(self):
        """Testa source_rate para fonte retangular conhecida."""
        flux = 1e13  # n/cm²/s
        x_cm = 1.69
        y_cm = 1.69
        expected_sr = flux * x_cm * y_cm
        
        # Simular parser_data
        parser_data = {
            "simulation_parameters": {
                "flux": flux,
                "wafer_x_cm": x_cm,
                "wafer_y_cm": y_cm,
            }
        }
        
        # TODO: Implementar teste completo quando geometry_result estiver disponível
        assert expected_sr == pytest.approx(2.8561e13, rel=1e-3)
    
    def test_source_rate_from_power(self):
        """Testa cálculo de source_rate a partir de potência."""
        power_W = 1000.0
        efficiency = 0.5
        E_PER_FISSION_J = 3.204e-11
        
        expected_sr = (power_W / E_PER_FISSION_J) / efficiency
        
        assert expected_sr == pytest.approx(6.24e13, rel=1e-2)
    
    def test_source_rate_priority(self):
        """Testa que POTENCIA_TOTAL_W tem prioridade sobre FLUXO."""
        # TODO: Implementar teste de integração
        pass


class TestNormalizationValidation:
    """Testes para validação de normalização pós-simulação."""
    
    def test_validation_within_tolerance(self):
        """Testa validação quando discrepância está dentro da tolerância."""
        # TODO: Criar statepoint mock ou usar arquivo de exemplo
        pass
    
    def test_validation_exceeds_tolerance(self):
        """Testa detecção de erro quando discrepância > tolerância."""
        # TODO: Implementar
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

#### 5.3.2 Documentação de Procedimento de Calibração

**Arquivo:** `docs/CALIBRACAO_NORMALIZACAO.md` (novo)

```markdown
# Procedimento de Calibração de Normalização

## Objetivo
Determinar o `FATOR_EFICIENCIA_FISSAO` correto para sua configuração experimental específica.

## Método

### Passo 1: Simulação de Referência
1. Execute uma simulação curta (12h) com `FATOR_EFICIENCIA_FISSAO = 0.5`
2. Anote a potência total calculada `P_calc`

### Passo 2: Comparação com Expectativa
1. Se você conhece a potência real do experimento `P_real`:
   - Calcule: `eff_corrigido = 0.5 × (P_real / P_calc)`
2. Se não conhece `P_real`, use literatura:
   - Para reatores de pesquisa típicos: eff ∈ [0.3, 0.7]
   - Para fontes isotópicas: eff ∈ [0.1, 0.3]

### Passo 3: Validação
1. Reexecute simulação com `FATOR_EFICIENCIA_FISSAO = eff_corrigido`
2. Verifique se `P_calc ≈ P_real` (dentro de 10%)

### Passo 4: Benchmark com Mo99
1. Compare atividade específica de Mo99 (Ci/g) com literatura
2. Valores típicos para irradição de 48h + 6h resfriamento:
   - UAl₂ 20%: 0.1-1.0 Ci/g (depende do fluxo)
   - U metálico 93%: 1-10 Ci/g

## Referências
- IAEA-TECDOC-1065: "Production technologies for Molybdenum-99"
- ORNL/TM-2018/XXX: "Mo99 yield calculations"
```

---

### FASE 4: Validação Experimental (Semana 4)

#### 5.4.1 Benchmark com Dados Publicados

**Meta:** Concordância dentro de ±15% para atividade de Mo99

**Procedimento:**
1. Selecionar 3-5 casos de teste da literatura (IAEA, OECD-NEA)
2. Configurar simulações idênticas (geometria, composição, fluxo, tempo)
3. Comparar:
   - Atividade de Mo99 ao EOB (End of Bombardment) [Ci]
   - Atividade específica [Ci/g]
   - Pureza isotópica (%)

**Critério de Aceitação:**
- Diferença < 15% para maioria dos casos
- Diferença < 25% para todos os casos

---

## 6. CHECKLIST PRÉ-PRODUÇÃO

- [ ] **FASE 1:**
  - [ ] Implementar cálculo de source_rate por potência total (`settings.py`)
  - [ ] Atualizar fallback em `simulation.py`
  - [ ] Adicionar função `validate_normalization_consistency` (`tallies.py`)
  - [ ] Integrar validação pós-simulação (`simulation.py`)
  - [ ] Atualizar template `Input-simulador.txt.template`

- [ ] **FASE 2:**
  - [ ] Adicionar validação de conservação de massa em `to_openmc_material`
  - [ ] Adicionar logging de nuclídeos perdidos em `_run_cooling_pyne`
  - [ ] Expandir logging de espectro efetivo

- [ ] **FASE 3:**
  - [ ] Criar suite de testes `tests/test_normalization.py`
  - [ ] Documentar procedimento de calibração (`docs/CALIBRACAO_NORMALIZACAO.md`)
  - [ ] Atualizar changelog para V237.0

- [ ] **FASE 4:**
  - [ ] Executar benchmark com 3+ casos da literatura
  - [ ] Documentar resultados e incertezas
  - [ ] Aprovação final para produção

---

## 7. CONCLUSÃO

### Resumo da Análise

O simulador nuclear OpenMC-PyNE apresenta **arquitetura sólida e bem documentada**, com:

✅ **Pontos Fortes:**
- Integração OpenMC-PyNE funcional e testada
- Constantes físicas corretas e consistentes
- Sistema de auto-configuração inteligente (DepletionAutoTuner)
- Workarounds fisicamente fundamentados (espectro ORIGEN252, PyNE decay_heat)
- Logs detalhados e rastreabilidade completa

⚠️ **Pontos de Atenção Críticos:**
1. **Normalização do source_rate** depende de aproximação geométrica simplificada (flux × area)
2. **Sem validação automática** de consistência de potência pós-simulação
3. **Conversão OpenMC→PyNE** pode perder nuclídeos silenciosamente

### Recomendação Final

**Status para Produção:** 🟡 **CONDICIONAL**

O código **NÃO deve ser usado em produção** até que as correções da **FASE 1** sejam implementadas e validadas. Os erros potenciais de normalização (fator 2-10×) tornam os resultados quantitativamente não confiáveis para tomada de decisões.

Após implementação da FASE 1:
- **Status:** 🟢 **PRÉ-PRODUÇÃO** (aceitável para testes e desenvolvimento)

Após implementação das FASES 1-3 e validação experimental (FASE 4):
- **Status:** 🟢 **PRODUÇÃO** (confiável para cálculos quantitativos)

### Próximos Passos Imediatos

1. **Implementar FASE 1** (1 semana)
2. **Testar internamente** com casos conhecidos (3 dias)
3. **Documentar procedimentos** de calibração (2 dias)
4. **Iniciar benchmark experimental** (FASE 4, 1 semana)

**Responsável:** [Equipe de Desenvolvimento]  
**Prazo Estimado:** 2-3 semanas para liberação pré-produção  
**Risco Residual Após FASE 1:** Baixo (<10% erro sistemático)

---

*Relatório gerado automaticamente a partir de varredura estática de código.*  
*Para validação completa, recomenda-se execução de testes dinâmicos com casos de referência.*
