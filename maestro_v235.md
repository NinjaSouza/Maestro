
==========================================================================================
  NOVO RUN — 2026-06-21 15:40:53
==========================================================================================
2026-06-21 15:40:53,321 - __main__       - INFO     - ==========================================================================================
2026-06-21 15:40:53,321 - __main__       - INFO     - MAESTRO V237 — PIPELINE OPENMC  A→B→C→D→E[→F][→G]
2026-06-21 15:40:53,321 - __main__       - INFO     - ==========================================================================================
2026-06-21 15:40:53,321 - __main__       - INFO     - PHASE A — PARSER
2026-06-21 15:40:53,326 - parser         - INFO     - ORIGEN252: w_th=0.9200 w_epi=0.0800 w_fast=0.0000 (canal irradiação IEA-R1)
2026-06-21 15:40:53,326 - __main__       - INFO     -   OK versão=V220  camadas=3  modo=ACTIVATION  partículas=1000
2026-06-21 15:40:53,326 - __main__       - INFO     - PHASE B — GEOMETRY
2026-06-21 15:40:53,329 - geometry       - INFO     - water_reflector: S(a,b) 'c_H_in_H2O' habilitado
2026-06-21 15:40:53,329 - geometry       - INFO     - _build_geometry: 3 camadas wafer + 3 células de água (front=5.0cm, back=5.0cm, lateral=10.0cm)
2026-06-21 15:40:53,329 - __main__       - INFO     -   OK materiais=4  células=3  wafer=(2.400 × 17.000)cm
2026-06-21 15:40:53,329 - __main__       - INFO     - PHASE C — SETTINGS
2026-06-21 15:40:53,331 - settings       - INFO     - DepletionAutoTuner [grossa, auto-tune]: DT_output=24.0h → DT_dep=6.0h × 4 sub-passos, integrador=celi
2026-06-21 15:40:53,331 - settings       - INFO     - ✓ ENDF-B-VIII.0 → /home/souza/nuclear_data/endf_b_viii_0_hdf5/cross_sections.xml
2026-06-21 15:40:53,331 - settings       - INFO     - ✓ TENDL-2021 → /home/souza/nuclear_data/hdf5_lib_tendl2021/cross_sections.xml
2026-06-21 15:40:53,331 - settings       - INFO     - ✓ TENDL-2015 → /home/souza/nuclear_data/hdf5_lib_tendl2015/cross_sections.xml
2026-06-21 15:40:53,331 - settings       - WARNING  - ✗ ENDF-B-VII.1 não encontrado: /home/souza/nuclear_data/endfb71_hdf5/cross_sections.xml
2026-06-21 15:40:53,331 - settings       - INFO     - ✓ JEFF-3.3 → /home/souza/nuclear_data/jeff33_hdf5/cross_sections.xml
2026-06-21 15:40:53,331 - settings       - INFO     - Biblioteca primária: ENDF-B-VIII.0
2026-06-21 15:40:53,331 - settings       - INFO     - ✓ Chain file (input): chain_endfb80_pwr.xml
2026-06-21 15:40:53,331 - settings       - INFO     - source_rate_initial=8.1600e+15 n/s (flux×area, será calibrado em Phase D)
2026-06-21 15:40:53,332 - settings       - INFO     - temperature: method=interpolation  default=294.0 K
2026-06-21 15:40:53,332 - settings       - INFO     - Sub-stepping ativo: 28 passos internos (Δt=6.0h) → 7 pontos output
2026-06-21 15:40:53,332 - __main__       - INFO     -   OK v=V225  n_passos=28  dt_output=24.0h  dt_depletion=6.0h  integrador=celi  normalization=source-rate
2026-06-21 15:40:53,332 - __main__       - INFO     -   biblioteca=ENDF-B-VIII.0  chain=chain_endfb80_pwr.xml  source_rate=8.1600e+15 n/s
2026-06-21 15:40:53,332 - __main__       - INFO     - PHASE D — SIMULATION
2026-06-21 15:40:53,430 - SimulationRunner - INFO     - ========================================================================
2026-06-21 15:40:53,431 - SimulationRunner - INFO     - SimulationRunner V238
2026-06-21 15:40:53,431 - SimulationRunner - INFO     - ========================================================================
2026-06-21 15:40:53,435 - SimulationRunner - INFO     - Iniciando calibração da fonte...
2026-06-21 15:40:53,435 - SimulationRunner - INFO     -   flux_target=2.0000e+14 n/cm²/s
2026-06-21 15:40:53,435 - SimulationRunner - INFO     -   wafer_dims=2.400 × 17.000 cm
2026-06-21 15:40:53,435 - SimulationRunner - INFO     -   water_lateral=10.0 cm
2026-06-21 15:40:53,435 - source_calibration - INFO     - SourceCalibrator V239 initialized: flux_target=2.0000e+14 n/cm²/s, target_area=40.8000 cm², source_area=40.8000 cm², source_rate_initial=8.1600e+15 n/s
2026-06-21 15:40:53,435 - source_calibration - INFO     - Calibração iteração 1/10: source_rate=8.1600e+15 n/s
2026-06-21 15:40:53,436 - source_calibration - INFO     - Região de calibração: 'CAMADA_1' (id=1)
2026-06-21 15:40:53,436 - source_calibration - INFO     - Tally de calibração criado: 'flux_calibration' na célula 'CAMADA_1', volume estimado=1.2240 cm³
2026-06-21 15:40:55,889 - source_calibration - ERROR    - Erro ao ler statepoint da calibração: setting an array element with a sequence.
2026-06-21 15:40:55,890 - source_calibration - ERROR    - Fluxo medido zero ou NaN — abortando calibração
2026-06-21 15:40:55,890 - SimulationRunner - ERROR    - Calibração falhou: Fluxo medido zero/NaN na iteração 1 — usando fallback
2026-06-21 15:40:55,890 - SimulationRunner - INFO     - source_rate_calibrated=8.1600e+15 n/s  |  flux_target=2.00e+14  x=2.400cm  y=17.000cm
2026-06-21 15:40:55,890 - SimulationRunner - INFO     - ORIGEN252 Mixture: Maxwell(kT=0.0285eV)×0.92 + 1/E_epi×0.08 + Watt×0.00
2026-06-21 15:40:55,890 - SimulationRunner - INFO     - Tallies: 6 células: ['CAMADA_1(id=1)', 'CAMADA_2(id=2)', 'CAMADA_3(id=3)', 'water_front(id=4)', 'water_back(id=5)', 'water_lateral(id=6)']
2026-06-21 15:40:56,603 - SimulationRunner - INFO     - Integrador de depleção: CELIIntegrator (n_passos=7) — [PRODUÇÃO: CELI mínimo]
2026-06-21 15:42:11,869 - __main__       - INFO     -   OK h5=depletion_results.h5  camadas_com_potência=0  timesteps_integrados=7
2026-06-21 15:42:11,870 - __main__       - INFO     - PHASE E — OUTPUT
2026-06-21 15:42:11,926 - ChainFileReader - INFO     - 3561 isótopos carregados do chain file
2026-06-21 15:42:12,685 - __main__       - INFO     -   OK arquivos=10  dir=pipeline_results
2026-06-21 15:42:12,685 - __main__       - INFO     - PHASE F — T-N LOOP (Picard)
2026-06-21 15:42:12,688 - __main__       - INFO     -   [TN iter 1/20]  L2=0.0000K  Linf=0.0000K  max_diff@initialization  
2026-06-21 15:42:12,688 - SimulationRunner - INFO     - ========================================================================
2026-06-21 15:42:12,688 - SimulationRunner - INFO     - SimulationRunner V238
2026-06-21 15:42:12,688 - SimulationRunner - INFO     - ========================================================================
2026-06-21 15:42:12,688 - SimulationRunner - INFO     - Iniciando calibração da fonte...
2026-06-21 15:42:12,688 - SimulationRunner - INFO     -   flux_target=2.0000e+14 n/cm²/s
2026-06-21 15:42:12,688 - SimulationRunner - INFO     -   wafer_dims=2.400 × 17.000 cm
2026-06-21 15:42:12,688 - SimulationRunner - INFO     -   water_lateral=10.0 cm
2026-06-21 15:42:12,688 - source_calibration - INFO     - SourceCalibrator V239 initialized: flux_target=2.0000e+14 n/cm²/s, target_area=40.8000 cm², source_area=40.8000 cm², source_rate_initial=8.1600e+15 n/s
2026-06-21 15:42:12,688 - source_calibration - INFO     - Calibração iteração 1/10: source_rate=8.1600e+15 n/s
2026-06-21 15:42:12,689 - source_calibration - INFO     - Região de calibração: 'CAMADA_1' (id=1)
2026-06-21 15:42:12,689 - source_calibration - INFO     - Tally de calibração criado: 'flux_calibration' na célula 'CAMADA_1', volume estimado=1.2240 cm³
2026-06-21 15:42:14,384 - source_calibration - ERROR    - Erro ao ler statepoint da calibração: setting an array element with a sequence.
2026-06-21 15:42:14,385 - source_calibration - ERROR    - Fluxo medido zero ou NaN — abortando calibração
2026-06-21 15:42:14,385 - SimulationRunner - ERROR    - Calibração falhou: Fluxo medido zero/NaN na iteração 1 — usando fallback
2026-06-21 15:42:14,385 - SimulationRunner - INFO     - source_rate_calibrated=8.1600e+15 n/s  |  flux_target=2.00e+14  x=2.400cm  y=17.000cm
2026-06-21 15:42:14,385 - SimulationRunner - INFO     - ORIGEN252 Mixture: Maxwell(kT=0.0285eV)×0.92 + 1/E_epi×0.08 + Watt×0.00
2026-06-21 15:42:14,385 - SimulationRunner - INFO     - Tallies: 6 células: ['CAMADA_1(id=1)', 'CAMADA_2(id=2)', 'CAMADA_3(id=3)', 'water_front(id=4)', 'water_back(id=5)', 'water_lateral(id=6)']
2026-06-21 15:42:15,108 - SimulationRunner - INFO     - Integrador de depleção: CELIIntegrator (n_passos=7) — [PRODUÇÃO: CELI mínimo]
2026-06-21 15:43:17,927 - __main__       - INFO     -   [TN iter 2/20]  L2=0.0000K  Linf=0.0000K  max_diff@CAMADA_1  *** CONVERGED ***
2026-06-21 15:43:17,927 - __main__       - INFO     -   OK iterações=2  convergiu=SIM
2026-06-21 15:43:17,927 - __main__       - INFO     - PHASE G — POSPROCESSAMENTO (cooling=12.0h  ativo=True)
2026-06-21 15:43:17,957 - PostProcessor  - INFO     - 
2026-06-21 15:43:17,957 - PostProcessor  - INFO     - ================================================================================
2026-06-21 15:43:17,957 - PostProcessor  - INFO     - ▶️ PHASE G: POSPROCESSAMENTO V1.1
2026-06-21 15:43:17,957 - PostProcessor  - INFO     - ================================================================================
2026-06-21 15:43:17,957 - PostProcessor  - INFO     - Parâmetros: cooling=12.0h flux=2.00e+14 area=40.8000 cm² chain=chain_endfb80_pwr.xml
2026-06-21 15:43:17,957 - PostProcessor  - INFO     - ── F1: PyNE decay processor
2026-06-21 15:43:17,957 - PostProcessor  - INFO     - [FinalInventory] Lendo pipeline_results/temp/depletion_results.h5
2026-06-21 15:43:18,035 - PostProcessor  - INFO     -  [h5py] Material 1 (row=0, vol=1.224e+00 cm³): 1092 nuclídeos com átomos > 0  total_atoms=7.356e+22
2026-06-21 15:43:18,036 - PostProcessor  - INFO     -  [h5py] Material 2 (row=1, vol=3.754e+00 cm³): 1527 nuclídeos com átomos > 0  total_atoms=6.602e+23
2026-06-21 15:43:18,036 - PostProcessor  - INFO     -  [h5py] Material 3 (row=2, vol=1.224e+00 cm³): 1228 nuclídeos com átomos > 0  total_atoms=7.356e+22
2026-06-21 15:43:18,041 - PostProcessor  - INFO     - [F1] PyNE.decay() cooling=12.00h
2026-06-21 15:43:18,093 - PostProcessor  - INFO     - [F1-diag] cooled.activity(): 869 total | 629 > 0 | 235 == 0 | amostra={'10010000': 0.0, '10020000': 0.0, '10030000': 1.165123554267133e-08}
2026-06-21 15:43:18,094 - PostProcessor  - INFO     - [F1] Massa: pré=3.2980e+00 g  pós=3.2980e+00 g  ratio=1.000000  (conservação OK)
2026-06-21 15:43:18,094 - PostProcessor  - INFO     - [F1] ✓ PyNE decay: 629 nuclídeos A_total=3.466e-03 Ci Q=0.0000 W
2026-06-21 15:43:18,094 - PostProcessor  - INFO     - [F1] PyNE.decay() cooling=12.00h
2026-06-21 15:43:18,108 - PostProcessor  - INFO     - [F1-diag] cooled.activity(): 877 total | 646 > 0 | 221 == 0 | amostra={'10010000': 0.0, '10020000': 0.0, '10030000': 8.494064423219395e-08}
2026-06-21 15:43:18,109 - PostProcessor  - INFO     - [F1] Massa: pré=3.7518e+01 g  pós=3.7518e+01 g  ratio=0.999989  (conservação OK)
2026-06-21 15:43:18,109 - PostProcessor  - INFO     - [F1] ✓ PyNE decay: 646 nuclídeos A_total=9.403e+02 Ci Q=0.0000 W
2026-06-21 15:43:18,109 - PostProcessor  - INFO     - [F1] PyNE.decay() cooling=12.00h
2026-06-21 15:43:18,117 - PostProcessor  - INFO     - [F1-diag] cooled.activity(): 887 total | 648 > 0 | 232 == 0 | amostra={'10010000': 0.0, '10020000': 0.0, '10030000': 9.991944115191532e-09}
2026-06-21 15:43:18,118 - PostProcessor  - INFO     - [F1] Massa: pré=3.2980e+00 g  pós=3.2980e+00 g  ratio=1.000000  (conservação OK)
2026-06-21 15:43:18,118 - PostProcessor  - INFO     - [F1] ✓ PyNE decay: 648 nuclídeos A_total=6.675e-03 Ci Q=0.0000 W
2026-06-21 15:43:18,118 - PostProcessor  - INFO     - F1 concluído: 3 camadas A_total=9.403e+02 Ci Q_decay=0.0000 W
2026-06-21 15:43:18,118 - PostProcessor  - INFO     - ── F2: TemperatureHistoryBuilder
2026-06-21 15:43:18,118 - PostProcessor  - INFO     - [F2] TempHistoryBuilder: T_water=313.1K flow=0.0030m³/s R_th=0.0001K/W
2026-06-21 15:43:18,118 - PostProcessor  - INFO     - [F2] Construindo T(t) de pipeline_results/temp/depletion_results.h5
2026-06-21 15:43:18,722 - PostProcessor  - INFO     - [F2] 8 timesteps de irradiação lidos (t_final=168.0h)
2026-06-21 15:43:18,722 - PostProcessor  - INFO     - [F2] ✓ T(t): 8 pts irradiação 20 pts resfriamento
2026-06-21 15:43:18,724 - PostProcessor  - INFO     - ── F3: PhotonDoseEstimator
2026-06-21 15:43:18,725 - PostProcessor  - INFO     - [F3] PhotonDoseEstimator: distância=1.00m
2026-06-21 15:43:18,829 - PostProcessor  - INFO     - [F3] ✓ Dose estimada em 11 pontos (t=0: 1205175.345 µSv/h)
2026-06-21 15:43:18,829 - PostProcessor  - INFO     - ── F4: NotableDaughterDetector
2026-06-21 15:43:18,829 - PostProcessor  - INFO     - [F4] ✓ Mo99 (A=2.646e+12 Bq) — SPECT diagnóstico
2026-06-21 15:43:18,829 - PostProcessor  - INFO     - [F4] ✓ I131 (A=7.604e+11 Bq) — Terapia tireóide
2026-06-21 15:43:18,829 - PostProcessor  - INFO     - [F4] ✓ Y90 (A=9.520e+08 Bq) — Radioimunoterapia
2026-06-21 15:43:18,829 - PostProcessor  - INFO     - ── F5: StructuralActivationSolver
2026-06-21 15:43:18,830 - PostProcessor  - INFO     - [F5] chainsolve CAMADA_1: φ=2.00e+14 n/cm²/s t=168.0h T=300K
2026-06-21 15:47:27,173 - PostProcessor  - INFO     - [F5] ✓ CAMADA_1: 1293 nuclídeos ativados A=5.156e+14 Bq
2026-06-21 15:47:27,193 - PostProcessor  - INFO     - [F5] Pulando CAMADA_2: combustível já depletado pelo OpenMC
2026-06-21 15:47:27,195 - PostProcessor  - INFO     - [F5] chainsolve CAMADA_3: φ=2.00e+14 n/cm²/s t=168.0h T=300K
2026-06-21 15:51:41,339 - PostProcessor  - INFO     - [F5] ✓ CAMADA_3: 1289 nuclídeos ativados A=5.156e+14 Bq
2026-06-21 15:51:41,358 - PostProcessor  - INFO     - ── Exportando CSVs
2026-06-21 15:51:41,366 - PostProcessor  - INFO     -  ✓ inventario_resfriado.csv (2633 linhas)
2026-06-21 15:51:41,367 - PostProcessor  - INFO     -  ✓ temperatura_historico.csv (28 linhas)
2026-06-21 15:51:41,367 - PostProcessor  - INFO     -  ✓ dose_fotonica_pós_shutdown.csv (11 linhas)
2026-06-21 15:51:41,367 - PostProcessor  - INFO     -  ✓ radioisotopos_interesse.csv (3 linhas)
2026-06-21 15:51:41,371 - PostProcessor  - INFO     -  ✓ ativacao_estrutural.csv (2582 linhas)
2026-06-21 15:51:41,371 - PostProcessor  - INFO     - [CSV] 5 arquivos exportados em pipeline_results/posprocessamento
2026-06-21 15:51:41,371 - PostProcessor  - INFO     - POSPROCESSAMENTO OK: 503.41s 5 csvs 0 erros
2026-06-21 15:51:41,371 - PostProcessor  - INFO     - ================================================================================
2026-06-21 15:51:41,372 - __main__       - INFO     -   OK cooling=12.0h  csvs=5
2026-06-21 15:51:41,372 - __main__       - INFO     - ==========================================================================================
2026-06-21 15:51:41,372 - __main__       - INFO     - SUCESSO  v=V237  fases=6  duração=648.05s  dir=pipeline_results  integrador=celi  chain=chain_endfb80_pwr.xml
2026-06-21 15:51:41,372 - __main__       - INFO     - ==========================================================================================

==========================================================================================
  NOVO RUN — 2026-06-21 17:01:00
==========================================================================================
2026-06-21 17:01:00,116 - __main__       - INFO     - ==========================================================================================
2026-06-21 17:01:00,116 - __main__       - INFO     - MAESTRO V237 — PIPELINE OPENMC  A→B→C→D→E[→F][→G]
2026-06-21 17:01:00,117 - __main__       - INFO     - ==========================================================================================
2026-06-21 17:01:00,117 - __main__       - INFO     - PHASE A — PARSER
2026-06-21 17:01:00,122 - parser         - INFO     - ORIGEN252: w_th=0.9200 w_epi=0.0800 w_fast=0.0000 (canal irradiação IEA-R1)
2026-06-21 17:01:00,122 - __main__       - INFO     -   OK versão=V220  camadas=3  modo=ACTIVATION  partículas=1000
2026-06-21 17:01:00,122 - __main__       - INFO     - PHASE B — GEOMETRY
2026-06-21 17:01:00,125 - geometry       - INFO     - water_reflector: S(a,b) 'c_H_in_H2O' habilitado
2026-06-21 17:01:00,126 - geometry       - INFO     - _build_geometry: 3 camadas wafer + 3 células de água (front=5.0cm, back=5.0cm, lateral=10.0cm)
2026-06-21 17:01:00,126 - __main__       - INFO     -   OK materiais=4  células=3  wafer=(2.400 × 17.000)cm
2026-06-21 17:01:00,126 - __main__       - INFO     - PHASE C — SETTINGS
2026-06-21 17:01:00,128 - settings       - INFO     - DepletionAutoTuner [grossa, auto-tune]: DT_output=24.0h → DT_dep=6.0h × 4 sub-passos, integrador=celi
2026-06-21 17:01:00,128 - settings       - INFO     - ✓ ENDF-B-VIII.0 → /home/souza/nuclear_data/endf_b_viii_0_hdf5/cross_sections.xml
2026-06-21 17:01:00,128 - settings       - INFO     - ✓ TENDL-2021 → /home/souza/nuclear_data/hdf5_lib_tendl2021/cross_sections.xml
2026-06-21 17:01:00,128 - settings       - INFO     - ✓ TENDL-2015 → /home/souza/nuclear_data/hdf5_lib_tendl2015/cross_sections.xml
2026-06-21 17:01:00,128 - settings       - WARNING  - ✗ ENDF-B-VII.1 não encontrado: /home/souza/nuclear_data/endfb71_hdf5/cross_sections.xml
2026-06-21 17:01:00,128 - settings       - INFO     - ✓ JEFF-3.3 → /home/souza/nuclear_data/jeff33_hdf5/cross_sections.xml
2026-06-21 17:01:00,128 - settings       - INFO     - Biblioteca primária: ENDF-B-VIII.0
2026-06-21 17:01:00,128 - settings       - INFO     - ✓ Chain file (input): chain_endfb80_pwr.xml
2026-06-21 17:01:00,128 - settings       - INFO     - source_rate_initial=8.1600e+15 n/s (flux×area, será calibrado em Phase D)
2026-06-21 17:01:00,128 - settings       - INFO     - temperature: method=interpolation  default=294.0 K
2026-06-21 17:01:00,128 - settings       - INFO     - Sub-stepping ativo: 28 passos internos (Δt=6.0h) → 7 pontos output
2026-06-21 17:01:00,128 - __main__       - INFO     -   OK v=V225  n_passos=28  dt_output=24.0h  dt_depletion=6.0h  integrador=celi  normalization=source-rate
2026-06-21 17:01:00,128 - __main__       - INFO     -   biblioteca=ENDF-B-VIII.0  chain=chain_endfb80_pwr.xml  source_rate=8.1600e+15 n/s
2026-06-21 17:01:00,128 - __main__       - INFO     - PHASE D — SIMULATION
2026-06-21 17:01:00,228 - SimulationRunner - INFO     - ========================================================================
2026-06-21 17:01:00,228 - SimulationRunner - INFO     - SimulationRunner V238
2026-06-21 17:01:00,228 - SimulationRunner - INFO     - ========================================================================
2026-06-21 17:01:00,232 - SimulationRunner - INFO     - Iniciando calibração da fonte...
2026-06-21 17:01:00,232 - SimulationRunner - INFO     -   flux_target=2.0000e+14 n/cm²/s
2026-06-21 17:01:00,232 - SimulationRunner - INFO     -   wafer_dims=2.400 × 17.000 cm
2026-06-21 17:01:00,232 - SimulationRunner - INFO     -   water_lateral=10.0 cm
2026-06-21 17:01:00,232 - source_calibration - INFO     - SourceCalibrator V239 initialized: flux_target=2.0000e+14 n/cm²/s, target_area=40.8000 cm², source_area=40.8000 cm², source_rate_initial=8.1600e+15 n/s
2026-06-21 17:01:00,232 - source_calibration - INFO     - Calibração iteração 1/10: source_rate=8.1600e+15 n/s
2026-06-21 17:01:00,233 - source_calibration - INFO     - Região de calibração: 'CAMADA_1' (id=1)
2026-06-21 17:01:00,233 - source_calibration - INFO     - Tally de calibração criado: 'flux_calibration' na célula 'CAMADA_1', volume estimado=1.2240 cm³
2026-06-21 17:01:02,635 - source_calibration - ERROR    - Erro ao ler statepoint da calibração: setting an array element with a sequence.
2026-06-21 17:01:02,635 - source_calibration - ERROR    - Fluxo medido zero ou NaN — abortando calibração
2026-06-21 17:01:02,635 - SimulationRunner - ERROR    - Calibração falhou: Fluxo medido zero/NaN na iteração 1 — usando fallback
2026-06-21 17:01:02,635 - SimulationRunner - INFO     - source_rate_calibrated=8.1600e+15 n/s  |  flux_target=2.00e+14  x=2.400cm  y=17.000cm
2026-06-21 17:01:02,635 - SimulationRunner - INFO     - ORIGEN252 Mixture: Maxwell(kT=0.0285eV)×0.92 + 1/E_epi×0.08 + Watt×0.00
2026-06-21 17:01:02,636 - SimulationRunner - INFO     - Tallies: 6 células: ['CAMADA_1(id=1)', 'CAMADA_2(id=2)', 'CAMADA_3(id=3)', 'water_front(id=4)', 'water_back(id=5)', 'water_lateral(id=6)']
2026-06-21 17:01:03,331 - SimulationRunner - INFO     - Integrador de depleção: CELIIntegrator (n_passos=7) — [PRODUÇÃO: CELI mínimo]
2026-06-21 17:02:18,659 - __main__       - INFO     -   OK h5=depletion_results.h5  camadas_com_potência=0  timesteps_integrados=7
2026-06-21 17:02:18,659 - __main__       - INFO     - PHASE E — OUTPUT
2026-06-21 17:02:18,714 - ChainFileReader - INFO     - 3561 isótopos carregados do chain file
2026-06-21 17:02:19,498 - __main__       - INFO     -   OK arquivos=10  dir=pipeline_results
2026-06-21 17:02:19,498 - __main__       - INFO     - PHASE F — T-N LOOP (Picard)
2026-06-21 17:02:19,501 - __main__       - INFO     -   [TN iter 1/20]  L2=0.0000K  Linf=0.0000K  max_diff@initialization  
2026-06-21 17:02:19,501 - SimulationRunner - INFO     - ========================================================================
2026-06-21 17:02:19,501 - SimulationRunner - INFO     - SimulationRunner V238
2026-06-21 17:02:19,501 - SimulationRunner - INFO     - ========================================================================
2026-06-21 17:02:19,501 - SimulationRunner - INFO     - Iniciando calibração da fonte...
2026-06-21 17:02:19,501 - SimulationRunner - INFO     -   flux_target=2.0000e+14 n/cm²/s
2026-06-21 17:02:19,501 - SimulationRunner - INFO     -   wafer_dims=2.400 × 17.000 cm
2026-06-21 17:02:19,501 - SimulationRunner - INFO     -   water_lateral=10.0 cm
2026-06-21 17:02:19,501 - source_calibration - INFO     - SourceCalibrator V239 initialized: flux_target=2.0000e+14 n/cm²/s, target_area=40.8000 cm², source_area=40.8000 cm², source_rate_initial=8.1600e+15 n/s
2026-06-21 17:02:19,501 - source_calibration - INFO     - Calibração iteração 1/10: source_rate=8.1600e+15 n/s
2026-06-21 17:02:19,502 - source_calibration - INFO     - Região de calibração: 'CAMADA_1' (id=1)
2026-06-21 17:02:19,502 - source_calibration - INFO     - Tally de calibração criado: 'flux_calibration' na célula 'CAMADA_1', volume estimado=1.2240 cm³
2026-06-21 17:02:21,395 - source_calibration - ERROR    - Erro ao ler statepoint da calibração: setting an array element with a sequence.
2026-06-21 17:02:21,395 - source_calibration - ERROR    - Fluxo medido zero ou NaN — abortando calibração
2026-06-21 17:02:21,395 - SimulationRunner - ERROR    - Calibração falhou: Fluxo medido zero/NaN na iteração 1 — usando fallback
2026-06-21 17:02:21,395 - SimulationRunner - INFO     - source_rate_calibrated=8.1600e+15 n/s  |  flux_target=2.00e+14  x=2.400cm  y=17.000cm
2026-06-21 17:02:21,395 - SimulationRunner - INFO     - ORIGEN252 Mixture: Maxwell(kT=0.0285eV)×0.92 + 1/E_epi×0.08 + Watt×0.00
2026-06-21 17:02:21,395 - SimulationRunner - INFO     - Tallies: 6 células: ['CAMADA_1(id=1)', 'CAMADA_2(id=2)', 'CAMADA_3(id=3)', 'water_front(id=4)', 'water_back(id=5)', 'water_lateral(id=6)']
2026-06-21 17:02:22,140 - SimulationRunner - INFO     - Integrador de depleção: CELIIntegrator (n_passos=7) — [PRODUÇÃO: CELI mínimo]
2026-06-21 17:03:24,531 - __main__       - INFO     -   [TN iter 2/20]  L2=0.0000K  Linf=0.0000K  max_diff@CAMADA_1  *** CONVERGED ***
2026-06-21 17:03:24,532 - __main__       - INFO     -   OK iterações=2  convergiu=SIM
2026-06-21 17:03:24,532 - __main__       - INFO     - PHASE G — POSPROCESSAMENTO (cooling=12.0h  ativo=True)
2026-06-21 17:03:24,560 - PostProcessor  - INFO     - 
2026-06-21 17:03:24,560 - PostProcessor  - INFO     - ================================================================================
2026-06-21 17:03:24,560 - PostProcessor  - INFO     - ▶️ PHASE G: POSPROCESSAMENTO V1.1
2026-06-21 17:03:24,560 - PostProcessor  - INFO     - ================================================================================
2026-06-21 17:03:24,560 - PostProcessor  - INFO     - Parâmetros: cooling=12.0h flux=2.00e+14 area=40.8000 cm² chain=chain_endfb80_pwr.xml
2026-06-21 17:03:24,560 - PostProcessor  - INFO     - ── F1: PyNE decay processor
2026-06-21 17:03:24,560 - PostProcessor  - INFO     - [FinalInventory] Lendo pipeline_results/temp/depletion_results.h5
2026-06-21 17:03:24,632 - PostProcessor  - INFO     -  [h5py] Material 1 (row=0, vol=1.224e+00 cm³): 1091 nuclídeos com átomos > 0  total_atoms=7.356e+22
2026-06-21 17:03:24,633 - PostProcessor  - INFO     -  [h5py] Material 2 (row=1, vol=3.754e+00 cm³): 1522 nuclídeos com átomos > 0  total_atoms=6.602e+23
2026-06-21 17:03:24,633 - PostProcessor  - INFO     -  [h5py] Material 3 (row=2, vol=1.224e+00 cm³): 1225 nuclídeos com átomos > 0  total_atoms=7.356e+22
2026-06-21 17:03:24,637 - PostProcessor  - INFO     - [F1] PyNE.decay() cooling=12.00h
2026-06-21 17:03:24,685 - PostProcessor  - INFO     - [F1-diag] cooled.activity(): 872 total | 632 > 0 | 235 == 0 | amostra={'10010000': 0.0, '10020000': 0.0, '10030000': 1.165123554267134e-08}
2026-06-21 17:03:24,686 - PostProcessor  - INFO     - [F1] Massa: pré=3.2980e+00 g  pós=3.2980e+00 g  ratio=1.000000  (conservação OK)
2026-06-21 17:03:24,686 - PostProcessor  - INFO     - [F1] ✓ PyNE decay: 632 nuclídeos A_total=3.466e-03 Ci Q=0.0000 W
2026-06-21 17:03:24,687 - PostProcessor  - INFO     - [F1] PyNE.decay() cooling=12.00h
2026-06-21 17:03:24,696 - PostProcessor  - INFO     - [F1-diag] cooled.activity(): 871 total | 641 > 0 | 220 == 0 | amostra={'10010000': 0.0, '10020000': 0.0, '10030000': 8.494064423219378e-08}
2026-06-21 17:03:24,697 - PostProcessor  - INFO     - [F1] Massa: pré=3.7518e+01 g  pós=3.7518e+01 g  ratio=0.999989  (conservação OK)
2026-06-21 17:03:24,697 - PostProcessor  - INFO     - [F1] ✓ PyNE decay: 641 nuclídeos A_total=9.403e+02 Ci Q=0.0000 W
2026-06-21 17:03:24,697 - PostProcessor  - INFO     - [F1] PyNE.decay() cooling=12.00h
2026-06-21 17:03:24,702 - PostProcessor  - INFO     - [F1-diag] cooled.activity(): 879 total | 640 > 0 | 232 == 0 | amostra={'10010000': 0.0, '10020000': 0.0, '10030000': 9.991944115191532e-09}
2026-06-21 17:03:24,703 - PostProcessor  - INFO     - [F1] Massa: pré=3.2980e+00 g  pós=3.2980e+00 g  ratio=1.000000  (conservação OK)
2026-06-21 17:03:24,703 - PostProcessor  - INFO     - [F1] ✓ PyNE decay: 640 nuclídeos A_total=6.675e-03 Ci Q=0.0000 W
2026-06-21 17:03:24,704 - PostProcessor  - INFO     - F1 concluído: 3 camadas A_total=9.403e+02 Ci Q_decay=0.0000 W
2026-06-21 17:03:24,704 - PostProcessor  - INFO     - ── F2: TemperatureHistoryBuilder
2026-06-21 17:03:24,704 - PostProcessor  - INFO     - [F2] TempHistoryBuilder: T_water=313.1K flow=0.0030m³/s R_th=0.0001K/W
2026-06-21 17:03:24,704 - PostProcessor  - INFO     - [F2] Construindo T(t) de pipeline_results/temp/depletion_results.h5
2026-06-21 17:03:25,282 - PostProcessor  - INFO     - [F2] 8 timesteps de irradiação lidos (t_final=168.0h)
2026-06-21 17:03:25,282 - PostProcessor  - INFO     - [F2] ✓ T(t): 8 pts irradiação 20 pts resfriamento
2026-06-21 17:03:25,283 - PostProcessor  - INFO     - ── F3: PhotonDoseEstimator
2026-06-21 17:03:25,283 - PostProcessor  - INFO     - [F3] PhotonDoseEstimator: distância=1.00m
2026-06-21 17:03:25,377 - PostProcessor  - INFO     - [F3] ✓ Dose estimada em 11 pontos (t=0: 1205175.345 µSv/h)
2026-06-21 17:03:25,377 - PostProcessor  - INFO     - ── F4: NotableDaughterDetector
2026-06-21 17:03:25,377 - PostProcessor  - INFO     - [F4] ✓ Mo99 (A=2.646e+12 Bq) — SPECT diagnóstico
2026-06-21 17:03:25,377 - PostProcessor  - INFO     - [F4] ✓ I131 (A=7.604e+11 Bq) — Terapia tireóide
2026-06-21 17:03:25,377 - PostProcessor  - INFO     - [F4] ✓ Y90 (A=9.520e+08 Bq) — Radioimunoterapia
2026-06-21 17:03:25,377 - PostProcessor  - INFO     - ── F5: StructuralActivationSolver
2026-06-21 17:03:25,377 - PostProcessor  - INFO     - [F5] chainsolve CAMADA_1: φ=2.00e+14 n/cm²/s t=168.0h T=300K
2026-06-21 17:07:24,068 - PostProcessor  - INFO     - [F5] ✓ CAMADA_1: 1293 nuclídeos ativados A=5.156e+14 Bq
2026-06-21 17:07:24,084 - PostProcessor  - INFO     - [F5] Pulando CAMADA_2: combustível já depletado pelo OpenMC
2026-06-21 17:07:24,085 - PostProcessor  - INFO     - [F5] chainsolve CAMADA_3: φ=2.00e+14 n/cm²/s t=168.0h T=300K
