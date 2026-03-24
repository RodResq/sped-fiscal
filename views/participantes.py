"""
views/participantes.py — Página 2: Participantes (Reg. 0150)
"""

import json
import streamlit as st
from pathlib import Path

from utils import UFS, formatar_cnpj, limpar_cnpj

PART_PATH = Path(__file__).parent.parent / "participantes.json"


def render():
    st.subheader("Participantes — Reg. 0150")
    st.caption("Clientes e fornecedores que aparecem nas NF-e do período. Cada CNPJ precisa estar cadastrado aqui.")

    participantes = json.loads(PART_PATH.read_text()) if PART_PATH.exists() else []

    col_add, col_lista = st.columns([1, 1], gap="large")

    with col_add:
        st.markdown("#### Adicionar participante")
        with st.form("form_part"):
            cod    = st.text_input("Código interno *", placeholder="CLI001", help="Código único que você define")
            pnome  = st.text_input("Nome/Razão Social *", placeholder="FORNECEDOR EXEMPLO LTDA")
            pcnpj  = st.text_input("CNPJ *", placeholder="00.000.000/0000-00")
            pie    = st.text_input("Inscrição Estadual", placeholder="opcional")
            c1, c2 = st.columns(2)
            puf    = c1.selectbox("UF", UFS, index=UFS.index("PA"))
            pmun   = c2.text_input("Cód. IBGE Município", placeholder="1501402")
            pend   = st.text_input("Endereço", placeholder="AV PRINCIPAL")
            c3, c4 = st.columns(2)
            pnum   = c3.text_input("Número", placeholder="100")
            pbairro= c4.text_input("Bairro", placeholder="CENTRO")

            add = st.form_submit_button("➕  Adicionar Participante", use_container_width=True)

        if add:
            pcnpj_limpo = limpar_cnpj(pcnpj)
            erros_p = []
            if not cod:                erros_p.append("Código interno é obrigatório.")
            if not pnome:              erros_p.append("Nome é obrigatório.")
            if len(pcnpj_limpo) != 14: erros_p.append("CNPJ deve ter 14 dígitos.")
            if any(p["COD_PART"] == cod for p in participantes):
                erros_p.append(f"Código '{cod}' já existe.")

            if erros_p:
                for e in erros_p:
                    st.error(e)
            else:
                participantes.append({
                    "COD_PART": cod.upper(),
                    "NOME":     pnome.upper(),
                    "CNPJ":     pcnpj_limpo,
                    "IE":       pie.strip(),
                    "UF":       puf,
                    "COD_MUN":  pmun.strip(),
                    "END":      pend.upper(),
                    "NUM":      pnum,
                    "BAIRRO":   pbairro.upper(),
                })
                PART_PATH.write_text(json.dumps(participantes, ensure_ascii=False, indent=2))
                st.success(f"✅  Participante **{cod}** adicionado!")
                st.rerun()

    with col_lista:
        st.markdown(f"#### Participantes cadastrados ({len(participantes)})")
        if not participantes:
            st.info("Nenhum participante cadastrado ainda.")
        else:
            for i, p in enumerate(participantes):
                with st.expander(f"**{p['COD_PART']}** — {p['NOME'][:35]}"):
                    st.markdown(f"CNPJ: `{formatar_cnpj(p['CNPJ'])}`")
                    st.markdown(f"UF/Município: `{p.get('UF', '-')}` · `{p.get('COD_MUN', '-')}`")
                    if st.button("🗑️ Remover", key=f"del_p_{i}"):
                        participantes.pop(i)
                        PART_PATH.write_text(json.dumps(participantes, ensure_ascii=False, indent=2))
                        st.rerun()
