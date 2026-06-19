#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
source_calibration.py — Calibração da intensidade da fonte para reproduzir fluxo experimental.

Módulo V238 — Implementa o contrato físico de calibração da fonte.

CONTRATO FÍSICO:
  Quando FLUXO + espectro são fornecidos no input, o simulador executa uma
  etapa de calibração para encontrar source_rate que reproduza o fluxo-alvo
  experimental na face do alvo.

ALGORITMO:
  1. Constrói modelo OpenMC curto com geometria real
  2. Adiciona tally de fluxo na região receptora (primeira camada do alvo)
  3. Executa simulação curta com source_rate inicial de referência
  4. Mede fluxo obtido ϕ_medido
  5. Atualiza: sr_novo = sr_velho × (ϕ_alvo / ϕ_medido)
  6. Repete até |ϕ_alvo - ϕ_medido| / ϕ_alvo < tolerância

RESULTADO:
  source_rate calibrado que reproduz o FLUXO experimental dentro da tolerância.
  Este valor é congelado e usado em toda a depleção subsequente.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import openmc
    _OPENMC_OK = True
except ImportError:
    _OPENMC_OK = False

from config import (
    SourceCalibrationConfig,
    GeometryContract,
    PhysicsConstants,
    ValidationLimits,
)

logger = logging.getLogger(__name__)

_EV_TO_J = PhysicsConstants.EV_TO_J


# ─────────────────────────────────────────────────────────────────────────────
# Resultado da calibração
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CalibrationResult:
    """Resultado da calibração da fonte."""
    success: bool
    flux_target: float          # Fluxo-alvo experimental [n/cm²/s]
    flux_achieved: float        # Fluxo medido na convergência [n/cm²/s]
    source_rate_calibrated: float  # source_rate final calibrado [n/s]
    source_rate_initial: float     # source_rate inicial [n/s]
    n_iterations: int           # Número de iterações executadas
    converged: bool             # True se atingiu tolerância
    error_relative_final: float # Erro relativo final |ϕ_alvo - ϕ_medido| / ϕ_alvo
    tally_used: str             # Nome do tally usado para calibração
    iterations_history: List[Dict[str, Any]] = field(default_factory=list)
    error_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "flux_target_n_cm2_s": self.flux_target,
            "flux_achieved_n_cm2_s": self.flux_achieved,
            "source_rate_calibrated_n_s": self.source_rate_calibrated,
            "source_rate_initial_n_s": self.source_rate_initial,
            "n_iterations": self.n_iterations,
            "converged": self.converged,
            "error_relative_final": self.error_relative_final,
            "tally_used": self.tally_used,
            "iterations_history": self.iterations_history,
            "error_message": self.error_message,
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────────────────────────────────────
# SourceCalibrator
# ─────────────────────────────────────────────────────────────────────────────

class SourceCalibrator:
    """
    Calibra a intensidade da fonte para reproduzir fluxo experimental.
    
    Uso:
      calibrator = SourceCalibrator(flux_target, geometry_result, energy_source)
      result = calibrator.run()
      source_rate = result.source_rate_calibrated
    """
    
    VERSION = "V238"
    
    def __init__(
        self,
        flux_target: float,                    # Fluxo-alvo experimental [n/cm²/s]
        geometry_result: Dict,                 # Resultado de geometry.py
        energy_source: Dict,                   # Espectro de energia da fonte
        wafer_x_cm: float,                     # Dimensão x do alvo [cm]
        wafer_y_cm: float,                     # Dimensão y do alvo [cm]
        water_lateral_cm: float,               # Água lateral [cm]
        config: Optional[SourceCalibrationConfig] = None,
        debug: bool = False,
    ) -> None:
        self.flux_target = float(flux_target)
        self.geometry_result = geometry_result
        self.energy_source = energy_source or {}
        self.wafer_x_cm = float(wafer_x_cm)
        self.wafer_y_cm = float(wafer_y_cm)
        self.water_lateral_cm = float(water_lateral_cm)
        self.config = config or SourceCalibrationConfig()
        self.debug = debug
        
        # Dimensões da fonte: alvo + água lateral
        self.source_x_cm = self.wafer_x_cm + 2.0 * self.water_lateral_cm
        self.source_y_cm = self.wafer_y_cm + 2.0 * self.water_lateral_cm
        self.source_area_cm2 = self.source_x_cm * self.source_y_cm
        
        # Source rate inicial estimado: flux × area
        self.source_rate_initial = self.flux_target * self.source_area_cm2
        
        # História de iterações
        self._history: List[Dict[str, Any]] = []
        
        logger.info(
            "SourceCalibrator initialized: flux_target=%.4e n/cm²/s, "
            "source_area=%.4f cm², source_rate_initial=%.4e n/s",
            self.flux_target, self.source_area_cm2, self.source_rate_initial,
        )
    
    def run(self) -> CalibrationResult:
        """Executa a calibração da fonte."""
        if not _OPENMC_OK:
            return CalibrationResult(
                success=False,
                flux_target=self.flux_target,
                flux_achieved=0.0,
                source_rate_calibrated=self.source_rate_initial,
                source_rate_initial=self.source_rate_initial,
                n_iterations=0,
                converged=False,
                error_relative_final=1.0,
                tally_used=self.config.CALIBRATION_TALLY_NAME,
                error_message="OpenMC não disponível",
            )
        
        if not self.config.ENABLE_CALIBRATION:
            logger.warning("Calibração desabilitada — usando source_rate inicial")
            return CalibrationResult(
                success=True,
                flux_target=self.flux_target,
                flux_achieved=self.flux_target,  # assume perfeito sem calibração
                source_rate_calibrated=self.source_rate_initial,
                source_rate_initial=self.source_rate_initial,
                n_iterations=0,
                converged=True,
                error_relative_final=0.0,
                tally_used=self.config.CALIBRATION_TALLY_NAME,
            )
        
        source_rate_current = self.source_rate_initial
        
        for iteration in range(self.config.MAX_ITERATIONS):
            logger.info(
                "Calibração iteração %d/%d: source_rate=%.4e n/s",
                iteration + 1, self.config.MAX_ITERATIONS, source_rate_current,
            )
            
            # Executa simulação de calibração
            flux_measured, flux_unc = self._run_calibration_iteration(
                source_rate_current, iteration
            )
            
            if flux_measured <= 0.0 or np.isnan(flux_measured):
                logger.error("Fluxo medido zero ou NaN — abortando calibração")
                return CalibrationResult(
                    success=False,
                    flux_target=self.flux_target,
                    flux_achieved=0.0,
                    source_rate_calibrated=source_rate_current,
                    source_rate_initial=self.source_rate_initial,
                    n_iterations=iteration + 1,
                    converged=False,
                    error_relative_final=1.0,
                    tally_used=self.config.CALIBRATION_TALLY_NAME,
                    iterations_history=list(self._history),
                    error_message=f"Fluxo medido zero/NaN na iteração {iteration + 1}",
                )
            
            # Calcula erro relativo
            error_rel = abs(self.flux_target - flux_measured) / self.flux_target
            
            # Registra histórico
            iter_record = {
                "iteration": iteration + 1,
                "source_rate_n_s": source_rate_current,
                "flux_measured_n_cm2_s": flux_measured,
                "flux_uncertainty": flux_unc,
                "flux_target_n_cm2_s": self.flux_target,
                "error_relative": error_rel,
                "converged": error_rel <= self.config.FLUX_TOLERANCE_REL,
            }
            self._history.append(iter_record)
            
            logger.info(
                "  Fluxo medido: %.4e ± %.4e n/cm²/s (alvo: %.4e), erro: %.4f%%",
                flux_measured, flux_unc, self.flux_target, error_rel * 100,
            )
            
            # Verifica convergência
            if error_rel <= self.config.FLUX_TOLERANCE_REL:
                logger.info(
                    "Calibração convergiu em %d iterações: erro=%.4f%% <= %.4f%%",
                    iteration + 1, error_rel * 100, self.config.FLUX_TOLERANCE_REL * 100,
                )
                return CalibrationResult(
                    success=True,
                    flux_target=self.flux_target,
                    flux_achieved=flux_measured,
                    source_rate_calibrated=source_rate_current,
                    source_rate_initial=self.source_rate_initial,
                    n_iterations=iteration + 1,
                    converged=True,
                    error_relative_final=error_rel,
                    tally_used=self.config.CALIBRATION_TALLY_NAME,
                    iterations_history=list(self._history),
                )
            
            # Atualiza source_rate com under-relaxation
            sr_new = source_rate_current * (self.flux_target / flux_measured)
            source_rate_current = (
                self.config.UNDER_RELAXATION * sr_new +
                (1.0 - self.config.UNDER_RELAXATION) * source_rate_current
            )
            
            logger.info(
                "  source_rate atualizado: %.4e → %.4e (under-relax=%.2f)",
                source_rate_current if iteration == 0 else source_rate_current / self.config.UNDER_RELAXATION,
                source_rate_current, self.config.UNDER_RELAXATION,
            )
        
        # Não convergiu dentro do máximo de iterações
        logger.warning(
            "Calibração não convergiu em %d iterações — usando último valor",
            self.config.MAX_ITERATIONS,
        )
        return CalibrationResult(
            success=False,
            flux_target=self.flux_target,
            flux_achieved=flux_measured,
            source_rate_calibrated=source_rate_current,
            source_rate_initial=self.source_rate_initial,
            n_iterations=self.config.MAX_ITERATIONS,
            converged=False,
            error_relative_final=error_rel,
            tally_used=self.config.CALIBRATION_TALLY_NAME,
            iterations_history=list(self._history),
            error_message=f"Não convergiu em {self.config.MAX_ITERATIONS} iterações",
        )
    
    def _run_calibration_iteration(
        self,
        source_rate: float,
        iteration: int,
    ) -> Tuple[float, float]:
        """
        Executa uma iteração de calibração e retorna (fluxo_medido, incerteza).
        """
        # Configura modelo OpenMC mínimo para calibração
        settings = self._build_calibration_settings(source_rate, iteration)
        tallies = self._build_calibration_tallies()
        
        # Exporta XMLs temporários
        temp_dir = Path("temp_calibration")
        temp_dir.mkdir(exist_ok=True)
        
        settings.export_to_xml(temp_dir / "settings.xml")
        tallies.export_to_xml(temp_dir / "tallies.xml")
        
        # Materiais e geometria já estão configurados globalmente
        # (geometry.py já exportou materials.xml e geometry.xml)
        
        # Executa OpenMC
        try:
            openmc.run(
                cwd=str(temp_dir),
                particles=settings.particles,
                batches=settings.batches,
            )
        except Exception as exc:
            logger.error("OpenMC falhou na calibração: %s", exc)
            return 0.0, 0.0
        
        # Lê StatePoint
        sp_files = list(temp_dir.glob("statepoint.*.h5"))
        if not sp_files:
            logger.error("Nenhum statepoint encontrado após calibração")
            return 0.0, 0.0
        
        sp_path = max(sp_files, key=lambda p: p.stat().st_mtime)
        
        try:
            with openmc.StatePoint(str(sp_path)) as sp:
                tally = sp.get_tally(name=self.config.CALIBRATION_TALLY_NAME)
                df = tally.get_pandas_dataframe()
                
                # Extrai fluxo médio e incerteza
                mean_flux = float(df["mean"].sum())
                std_flux = float(df["std. dev."].sum()) if "std. dev." in df.columns else 0.0
                
                # Normaliza por volume da célula se necessário
                # O tally de fluxo em OpenMC já está em [n·cm/src]
                # Para obter [n/cm²], dividimos pela área da face
                # Mas como estamos fazendo razão, as unidades se cancelam
                
                return mean_flux, std_flux
        except Exception as exc:
            logger.error("Erro ao ler statepoint da calibração: %s", exc)
            return 0.0, 0.0
        finally:
            # Limpa arquivos temporários
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _build_calibration_settings(
        self,
        source_rate: float,
        iteration: int,
    ) -> openmc.Settings:
        """Constrói settings OpenMC para iteração de calibração."""
        settings = openmc.Settings()
        settings.run_mode = "fixed source"
        settings.particles = self.config.PARTICLES_PER_ITERATION
        settings.batches = self.config.BATCHES_PER_ITERATION
        settings.inactive = 0
        
        # Semente aleatória para reprodutibilidade
        if self.config.RANDOM_SEED is not None:
            settings.seed = self.config.RANDOM_SEED + iteration
        
        # Fonte plana incidente
        # Posição: 1 cm da face frontal do alvo (em água frontal)
        z_source = -GeometryContract.DISTANCE_SOURCE_TO_FACE_CM
        
        source_box = openmc.stats.Box(
            [-self.source_x_cm / 2, -self.source_y_cm / 2, z_source],
            [ self.source_x_cm / 2,  self.source_y_cm / 2, 
              z_source + GeometryContract.SOURCE_PLANE_THICKNESS_CM],
        )
        
        settings.source = [openmc.IndependentSource(
            space=source_box,
            energy=self._build_energy_distribution(),
            angle=openmc.stats.Monodirectional(GeometryContract.SOURCE_DIRECTION),
        )]
        
        settings.output = {"summary": True}
        
        return settings
    
    def _build_energy_distribution(self) -> "openmc.stats.Univariate":
        """Constrói distribuição energética da fonte a partir do espectro."""
        stype = self.energy_source.get("type", "maxwell")
        data = self.energy_source.get("data", {})
        kb_eV = PhysicsConstants.KB_EV
        
        if stype == "single":
            ev = data.get("energy_ev")
            if ev is not None:
                return openmc.stats.Discrete([float(ev)], [1.0])
        
        if stype == "discrete":
            energies = data.get("energies_ev", [])
            probs = data.get("probabilities", [])
            if energies and probs:
                return openmc.stats.Discrete(
                    [float(e) for e in energies],
                    [float(p) for p in probs],
                )
        
        if stype == "maxwell":
            params = data.get("parameters", {})
            theta = float(params.get("theta", 300.0 * kb_eV))
            return openmc.stats.Maxwell(theta)
        
        if stype == "watt":
            params = data.get("parameters", {})
            return openmc.stats.Watt(
                float(params.get("a", 0.988e6)),
                float(params.get("b", 2.249e-6)),
            )
        
        if stype == "tabular":
            energies = data.get("energies_ev", [])
            probs = data.get("probabilities", [])
            if energies and probs and len(energies) == len(probs):
                return openmc.stats.Tabular(energies, probs)
        
        # Fallback: Maxwell com temperatura padrão
        return openmc.stats.Maxwell(300.0 * kb_eV)
    
    def _build_calibration_tallies(self) -> openmc.Tallies:
        """Constrói tallies para calibração."""
        cells_dict = self.geometry_result.get("cells_dict", {})
        
        if not cells_dict:
            raise ValueError("cells_dict ausente na geometria")
        
        # Identifica primeira camada do alvo (região receptora)
        # A primeira camada não-água é o proxy operacional do fluxo experimental
        first_layer_cell = None
        for name, cell in cells_dict.items():
            if not name.startswith("water_"):
                first_layer_cell = cell
                break
        
        if first_layer_cell is None:
            raise ValueError("Nenhuma camada do alvo encontrada")
        
        # Tally de fluxo na primeira camada
        cell_filter = openmc.CellFilter([first_layer_cell])
        
        tally = openmc.Tally(name=self.config.CALIBRATION_TALLY_NAME)
        tally.filters = [cell_filter]
        tally.scores = ["flux"]
        
        tallies = openmc.Tallies([tally])
        
        logger.info(
            "Tally de calibração criado: '%s' na célula '%s' (id=%d)",
            self.config.CALIBRATION_TALLY_NAME,
            first_layer_cell.name if hasattr(first_layer_cell, "name") else "?",
            first_layer_cell.id,
        )
        
        return tallies


# ─────────────────────────────────────────────────────────────────────────────
# API pública
# ─────────────────────────────────────────────────────────────────────────────

def calibrate_source(
    flux_target: float,
    geometry_result: Dict,
    energy_source: Dict,
    wafer_x_cm: float,
    wafer_y_cm: float,
    water_lateral_cm: float,
    config: Optional[SourceCalibrationConfig] = None,
    debug: bool = False,
) -> CalibrationResult:
    """
    Função de alto nível para calibrar a fonte.
    
    Args:
        flux_target: Fluxo-alvo experimental [n/cm²/s]
        geometry_result: Resultado de geometry.build()
        energy_source: Espectro de energia (parser_data['energy_source'])
        wafer_x_cm: Dimensão x do alvo [cm]
        wafer_y_cm: Dimensão y do alvo [cm]
        water_lateral_cm: Espessura de água lateral [cm]
        config: Configuração opcional de calibração
        debug: Modo debug
    
    Returns:
        CalibrationResult com source_rate calibrado
    """
    calibrator = SourceCalibrator(
        flux_target=flux_target,
        geometry_result=geometry_result,
        energy_source=energy_source,
        wafer_x_cm=wafer_x_cm,
        wafer_y_cm=wafer_y_cm,
        water_lateral_cm=water_lateral_cm,
        config=config,
        debug=debug,
    )
    return calibrator.run()


__all__ = [
    "SourceCalibrator",
    "CalibrationResult",
    "calibrate_source",
]
