# Plano de Correção — Simulador Nuclear OpenMC-PyNE (V240)

## Diagnóstico Consolidado

### Problemas Críticos Identificados

1. **Calibração da Fonte Não Funciona Corretamente**
   - `source_calibration.py` usa chave errada (`cells_dict` vs `cellsdict`) ✓ CORRIGIDO V240
   - Conversão de unidades do tally está incompleta
   - Fallback `flux × area` mascara erros físicos ✓ CORRIGIDO V240
   - Log da atualização do source_rate está incorreto

2. **Queima de U235 Inconsistente (0.0165g em 168h)**
   - Causa raiz: calibração falha → source_rate incorreto → taxas de reação erradas
   - Fallback estava usando área errada (água lateral instead de alvo)

3. **Mo99 Desaparece no Resfriamento**
   - 1.68875E-4g → 3.25956E-33g após 12h
   - Causa provável: chain file `chain_endfb80_pwr.xml` não contém Mo99 adequadamente
   - ✓ CORRIGIDO V240: Input alterado para `chain_endfb80_act.xml`

4. **Delta Temperatura Baixo (0.004 K)**
   - Potência depositada calculada incorretamente devido a source_rate errado

---

## Ações de Correção Implementadas (V240)

### 1. ✅ Corrigir Chave do Contrato de Geometria

**Arquivo:** `source_calibration.py` (linhas 563-572)

**Problema:** Código procurava `cellsdict`, mas geometry.py retorna `cells_dict`

**Solução Implementada:**
```python
# FIX V240: Chave correta é 'cells_dict' conforme contrato geometry.py (linha 280)
cells_dict = self.geometry_result.get("cells_dict", {})

if not cells_dict:
    raise ValueError(
        "cells_dict ausente na geometria. "
        "Verifique se geometry.py foi executado corretamente e retornou 'cells_dict'. "
        f"Chaves disponíveis em geometry_result: {list(self.geometry_result.keys())}"
    )
```

### 2. ✅ Remover Fallback Perigoso

**Arquivo:** `simulation.py` (linhas 1072-1078)

**Problema:** Fallback `flux × area` mascarava erros de calibração

**Solução Implementada:**
```python
except Exception as exc:
    self.logger.error("Exceção na calibração: %s", exc)
    # FIX V240: NÃO usar fallback — falhar explicitamente
    raise RuntimeError(
        f"Calibração da fonte falhou: {exc}. "
        "Não é possível prosseguir com source_rate não calibrado."
    ) from exc
```

### 3. ✅ Corrigir Metadata Fallback

**Arquivo:** `simulation.py` (linhas 964-993)

**Problema:** Metadata fallback usava chave errada `cellsdict`

**Solução Implementada:**
```python
# FIX V240: Incluir cells_dict (chave correta) no metadata fallback
geometry_result = {
    "cells_dict": {},  # FIX V240: chave correta, não 'cellsdict'
    "metadata": { ... }
}
```

### 4. ✅ Alterar Chain File para Ativação

**Arquivo:** `Input-simulador.txt` (linha 60)

**Problema:** `chain_endfb80_pwr.xml` otimizado para PWR, não contém produtos de ativação estrutural

**Solução Implementada:**
```txt
# FIX V240: Usar chain_endfb80_act.xml (yields cumulativos) para ativação estrutural
CHAIN_FILE chain_endfb80_act.xml
```

---

## Validação Pendente

### Testes Obrigatórios Pós-V240

1. **Teste de Calibração**
   ```bash
   python maestro.py --input Input-simulador.txt
   ```
   - [ ] Zero warnings "geometry_result incompleto"
   - [ ] Zero fallbacks "flux×area"
   - [ ] Calibração converge em ≤5 iterações

2. **Teste de Queima de Combustível**
   - [ ] Queima de U235 ≥ 0.5g em 168h (fluxo 2e14 n/cm²/s)

3. **Teste de Ativação Mo99**
   - [ ] Inventário pré-resfriamento: Mo99 > 1e-4g
   - [ ] Inventário pós-resfriamento (12h): Mo99 ≥ 80% do pré-resfriamento
   - [ ] Verificar log: `[F4] ✓ Mo99 (A=...Bq)`

4. **Teste de Elevação de Temperatura**
   - [ ] ΔT ≥ 1.0 K para condições nominais

---

## Métricas de Sucesso V240

- [x] Chave `cells_dict` corrigida no source_calibration.py
- [x] Fallback perigoso removido do simulation.py
- [x] Metadata fallback corrigida para usar `cells_dict`
- [x] Chain file alterado para `chain_endfb80_act.xml`
- [ ] Calibração converge em ≤5 iterações com erro <1%
- [ ] Queima de U235 ≥ 0.5g em 168h
- [ ] Mo99 pós-resfriamento ≥ 80% do inventário pré-resfriamento
- [ ] ΔT ≥ 1.0 K
- [ ] Zero warnings "geometry_result incompleto"
- [ ] Zero fallbacks "flux×area"

---

## Próximos Passos

1. **Executar simulação de teste** com as correções V240
2. **Analisar log** para verificar:
   - Convergência da calibração
   - Ausência de warnings críticos
   - Inventário de Mo99 pré e pós-resfriamento
3. **Se Mo99 ainda desaparecer:**
   - Investigar conversão PyNE ↔ OpenMC no posprocessamento.py
   - Validar que `chain_endfb80_act.xml` existe no diretório de dados nucleares
4. **Se queima de U235 ainda baixa:**
   - Validar source_rate calibrado (ordem de grandeza: ~1e15 n/s)
   - Verificar normalização dos tallies de potência

---

## Notas Técnicas V240

### Chain Files Disponíveis

O config.py define a seguinte prioridade:
1. `chain_endfb80_act.xml` — yields cumulativos, ideal para ativação ✓ USAR ESTE
2. `chain_endfb80_pwr.xml` — otimizado para PWR, pode faltar produtos de ativação
3. `chain_endfb80.xml` — genérico

### Sobre o Mo99

Meia-vida: 66 horas  
Decaimento em 12h:
```
N(12h) = N₀ × exp(-ln(2) × 12 / 66) ≈ N₀ × 0.88
```

Portanto, ~88% do Mo99 deve permanecer após 12h de resfriamento.

### Fórmula de Calibração

Para fixed source OpenMC:
```
ϕ_físico [n/cm²/s] = (tally_flux [n·cm/src] × source_rate [n/s]) / volume [cm³]
```

Implementada corretamente em source_calibration.py linha 243.
