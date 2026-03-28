"""
utils.py — Constantes e funções compartilhadas entre as views.
"""

import re
import json
import calendar
from pathlib import Path

import streamlit as st


# ── Constantes ────────────────────────────────────────────────────────────────

MUNICIPIOS_PA = {
    "Belém":          "1501402",
    "Ananindeua":     "1500800",
    "Santarém":       "1506807",
    "Marabá":         "1504208",
    "Parauapebas":    "1505536",
    "Castanhal":      "1502400",
    "Abaetetuba":     "1500107",
    "Cametá":         "1502103",
    "Altamira":       "1500602",
    "Itaituba":       "1503606",
}

MUNICIPIOS_CE = {
    "Fortaleza":         "2304400",
    "Caucaia":           "2303709",
    "Juazeiro do Norte": "2307304",
    "Sobral":            "2312908",
    "Maracanaú":         "2307650",
    "Crato":             "2304202",
    "Iguatu":            "2305407",
    "Quixadá":           "2311405",
}

MUNICIPIOS_SP = {
    "São Paulo":      "3550308",
    "Campinas":       "3509502",
    "Guarulhos":      "3518800",
    "Santo André":    "3547809",
    "Ribeirão Preto": "3543402",
    "Sorocaba":       "3552205",
}

MUNICIPIOS_POR_UF = {
    "PA": MUNICIPIOS_PA,
    "CE": MUNICIPIOS_CE,
    "SP": MUNICIPIOS_SP,
}

UFS = ["AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
       "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO"]


# ── Funções auxiliares ────────────────────────────────────────────────────────

def formatar_cnpj(v: str) -> str:
    d = re.sub(r"\D", "", v)
    if len(d) == 14:
        return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
    return v


def limpar_cnpj(v: str) -> str:
    return re.sub(r"\D", "", v)


def primeiro_dia_mes(ano: int, mes: int) -> str:
    return f"01{mes:02d}{ano}"


def ultimo_dia_mes(ano: int, mes: int) -> str:
    ultimo = calendar.monthrange(ano, mes)[1]
    return f"{ultimo:02d}{mes:02d}{ano}"


def colorir_linha(linha: str) -> str:
    """Retorna HTML colorido para a linha do arquivo SPED."""
    linha = linha.strip()
    if not linha:
        return ""
    partes = linha.split("|")
    reg = partes[1] if len(partes) > 1 else ""
    cor_map = {
        "0000": "reg-0000",
        "0001": "reg-0001",
        "0005": "reg-0005",
        "0100": "reg-0001",
        "0150": "reg-0150",
        "0190": "reg-default",
        "0200": "reg-0200",
        "0400": "reg-default",
        "0990": "reg-default",
    }
    cls = cor_map.get(reg, "reg-default")
    linha_safe = linha.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<span class="{cls}">{linha_safe}</span>'


def carregar_config() -> dict:
    if "empresa" in st.secrets:
        dados_secrets = dict(st.secrets["empresa"])
        if dados_secrets:
            return dados_secrets
    cfg_path = Path(__file__).parent / "config_empresa.json"
    if cfg_path.exists():
        with open(cfg_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_config(dados: dict):
    cfg_path = Path(__file__).parent / "config_empresa.json"
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
