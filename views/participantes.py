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
            codigo_interno = st.text_input("Código interno *", placeholder="CLI001", help="Código único que você define")
            participante_nome = st.text_input("Nome/Razão Social *", placeholder="FORNECEDOR EXEMPLO LTDA")
            participante_cnpj = st.text_input("CNPJ *", placeholder="00.000.000/0000-00")
            participante_ie = st.text_input("Inscrição Estadual", placeholder="opcional")
            
            col_puf, col_pibge = st.columns(2)
            participante_uf    = col_puf.selectbox("UF", UFS, index=UFS.index("PA"))
            participante_cod_mun_ibge   = col_pibge.text_input("Cód. IBGE Município", placeholder="1501402")
            participante_endereco   = st.text_input("Endereço", placeholder="AV PRINCIPAL")
            
            col_pnumero, col_pbairro = st.columns(2)
            participante_numero   = col_pnumero.text_input("Número", placeholder="100")
            participante_bairro= col_pbairro.text_input("Bairro", placeholder="CENTRO")

            add = st.form_submit_button("➕  Adicionar Participante", use_container_width=True)

        if add:
            pcnpj_limpo = limpar_cnpj(participante_cnpj)
            erros_p = []
            
            if not codigo_interno: erros_p.append("Código interno é obrigatório.")
            if not participante_nome: erros_p.append("Nome é obrigatório.")
            
            if len(pcnpj_limpo) != 14: erros_p.append("CNPJ deve ter 14 dígitos.")
            
            if any(p["COD_PART"] == codigo_interno for p in participantes):
                erros_p.append(f"Código '{codigo_interno}' já existe.")

            if erros_p:
                for e in erros_p:
                    st.error(e)
            else:
                participantes.append({
                    "COD_PART": codigo_interno.upper(),
                    "NOME": participante_nome.upper(),
                    "CNPJ": pcnpj_limpo,
                    "IE": participante_ie.strip(),
                    "UF": participante_uf,
                    "COD_MUN": participante_cod_mun_ibge.strip(),
                    "END": participante_endereco.upper(),
                    "NUM": participante_numero,
                    "BAIRRO": participante_bairro.upper(),
                })
                
                PART_PATH.write_text(json.dumps(participantes, ensure_ascii=False, indent=2))
                st.success(f"✅  Participante **{codigo_interno}** adicionado!")
                st.rerun()

    with col_lista:
        st.markdown(f"#### Participantes cadastrados ({len(participantes)})")
        
        if not participantes:
            st.info("Nenhum participante cadastrado ainda.")
        else:
            for index, participante in enumerate(participantes):
                with st.expander(f"**{participante['COD_PART']}** — {participante['NOME'][:35]}"):
                    st.markdown(f"CNPJ: `{formatar_cnpj(participante['CNPJ'])}`")
                    st.markdown(f"UF/Município: `{participante.get('UF', '-')}` · `{participante.get('COD_MUN', '-')}`")
                    
                    if st.button("🗑️ Remover", key=f"del_p_{index}"):
                        participantes.pop(index)
                        PART_PATH.write_text(json.dumps(participantes, ensure_ascii=False, indent=2))
                        st.rerun()
