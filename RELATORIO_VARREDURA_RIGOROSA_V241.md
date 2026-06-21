# RELATÓRIO DE VARREDURA RIGOROSA - SIMULADOR NUCLEAR
**Data:** 2026-06-21  
**Versão do Código:** V241 (pós-correções)  
**Foco:** Integração OpenMC 0.15.3 ↔ PyNE, Placeholders/Mocks, Consistência Física

---

## 1. ERROS DE INTEGRAÇÃO OPENMC-PyNE

### 1.1 Mapeamento de Nuclídeos: OpenMC ↔ PyNE ✅ CORRIGIDO

**Arquivo:** `posprocessamento.py` (linhas 670-723)

**Problema Identificado:**
```python
# CÓDIGO ANTERIOR (ERRADO):
base = re.sub(r"_m\d+$", "", nuc_str)  # Remove sufixos metaestáveis!
return pynenucname.id(base)
```

**Impacto:**
- `Tc99_m1` (meia-vida 6.01h) era mapeado para `Tc99` (meia-vida 2.1×10⁵ anos)
- Perda completa da atividade do metaestável
- Distribuição errada de decaimento: `Tc99_m1 → Tc99` não era modelado

**Correção Aplicada:**
```python
# Tentativa 1: Conversão direta
try:
    return pynenucname.id(nuc_str)
except Exception:
    pass

# Tentativa 2: Normalizar formato (remover hífen se presente)
normalized = nuc_str.replace("-", "")
try:
    return pynenucname.id(normalized)
except Exception:
    pass

# ⚠️ NÃO REMOVER sufixos _m! Metaestáveis são nuclídeos distintos no PyNE
return None
```

**Veredito:** ✅ **CORRIGIDO** - Metaestáveis agora preservados corretamente.

---

### 1.2 Conversão de Inventário: OpenMC → PyNE Material ✅ CORRIGIDO

**Arquivo:** `simulation.py` (linhas 777-838)

**Problema Crítico Identificado:**
```python
comp = {}
for nuc, dens in om.get_nuclide_atom_densities().items():
    comp[_pync.id(nuc)] = dens  # dens é [atom/b-cm], NÃO fração!
pyne_mats[om.id] = _PyNEMat(comp, mass=1.0)  # mass=1.0 fallback perigoso
```

**Impacto:**
- `get_nuclide_atom_densities()` retorna `[atom/barn·cm]` = `[10²⁴ atom/cm³]`
- PyNE `Material.__init__` espera **frações mássicas** (soma = 1.0)
- Usar densidades absolutas como frações cria composição fisicamente absurda

**Correção Aplicada:**
```python
atom_densities = om.get_nuclide_atom_densities()
total_atom_dens = sum(atom_densities.values())

comp_mass_frac: Dict[int, float] = {}
total_mass_g = 0.0

for nuc_str, atom_dens in atom_densities.items():
    pyne_id = _pync.id(nuc_str)
    atomic_mass = _pynucdata.atomic_mass(pyne_id)
    mass_dens = atom_dens * 1e24 * atomic_mass / _AVOGADRO
    comp_mass_frac[pyne_id] = mass_dens
    total_mass_g += mass_dens

final_comp = {nid: m / total_mass_g for nid, m in comp_mass_frac.items()}
om_mass = om.get_mass() if hasattr(om, "get_mass") else total_mass_g
pyne_mats[om.id] = _PyNEMat(final_comp, mass=om_mass)
```

**Veredito:** ✅ **CORRIGIDO** - Conversão dimensionalmente consistente.

---

## 2. PLACEHOLDERS E MOCKS

### 2.1 Espectro ORIGEN252 ⚠️ DOCUMENTADO
- **Arquivo:** `parser.py` (linhas 516-525)
- Valores hardcoded sem referência explícita
- Classificação: Aproximação analítica aceitável

### 2.2 Massas Atômicas Fallback ⚠️ MELHORÁVEL
- **Arquivo:** `output.py` (linhas 146-172)
- Usa número de massa A quando falha (erro ~0.1%)
- Último fallback 1.0 só para strings inválidas

### 2.3 Energias de Decaimento ⚠️ WORKAROUND
- **Arquivo:** `posprocessamento.py` (linhas 518-524)
- Workaround para bug PyNE 0.7.7
- Migrar para PyNE ≥ 0.8 quando disponível

---

## 3. CONSISTÊNCIA FÍSICA

### 3.1 Source Rate Inicial ✅ CORRETO
- `source_rate = flux × area` dimensionalmente correto

### 3.2 Área da Fonte ⚠️ QUESTIONÁVEL
- Fonte cobre apenas wafer, ignora água lateral
- Pode causar viés sistemático no espectro

### 3.3 Conversão de Fluxo ✅ CORRETO
- `flux_physical = (tally × source_rate) / volume`
- Dimensionalmente consistente [n/cm²/s]

### 3.4 Calibração 🔴 CRÍTICO NÃO RESOLVIDO
- Falha consistentemente com erro "setting an array element with a sequence"
- Usa fallback silencioso (`source_rate_initial`)
- **Resultados provisórios até resolução**

---

## 4. RESUMO

| Item | Status | Prioridade |
|------|--------|------------|
| Mapeamento Nuclídeos | ✅ Corrigido | - |
| Conversão OpenMC→PyNE | ✅ Corrigido | - |
| Calibração de Fonte | 🔴 Falhando | URGENTE |
| Espectro ORIGEN | ⚠️ Documentado | Baixa |
| Geometria da Fonte | ⚠️ Questionável | Média |

**Conclusão:** Correções críticas aplicadas, mas calibração falhando invalida consistência física dos resultados.

