"""
views/gerar_bloco0.py — Página 4: Gerar Bloco 0
"""

import json
import streamlit as st
from pathlib import Path
from datetime import date

from utils import (
    formatar_cnpj, colorir_linha,
    primeiro_dia_mes, ultimo_dia_mes,
    carregar_config,
)
from sped_fiscal.bloco0 import (
    Bloco0, Reg0000, Reg0005, Reg0100,
    Reg0150, Reg0190, Reg0200,
)

PART_PATH  = Path(__file__).parent.parent / "participantes.json"
ITENS_PATH = Path(__file__).parent.parent / "itens.json"

DESCR_UNID = {
    "UN": "Unidade", "KG": "Quilograma", "LT": "Litro",
    "MT": "Metro",   "M2": "Metro quadrado", "M3": "Metro cubico",
    "CX": "Caixa",   "PC": "Peca",  "PR": "Par",
    "DZ": "Duzia",   "GR": "Grama", "TN": "Tonelada",
}


def render():
    st.subheader("Gerar Bloco 0")
    st.caption("Monta o arquivo .txt do Bloco 0 a partir dos cadastros salvos e valida antes de exportar.")

    cfg = carregar_config()
    participantes = json.loads(PART_PATH.read_text())  if PART_PATH.exists()  else []
    itens = json.loads(ITENS_PATH.read_text()) if ITENS_PATH.exists() else []

    if not cfg:
        st.warning("⚠️  Nenhum cadastro de empresa encontrado. Vá em **Cadastro da Empresa** primeiro.")
        st.stop()

    col_param, col_status = st.columns([1.2, 1], gap="large")

    with col_param:
        st.markdown("#### Parâmetros do período")
        anos  = list(range(2022, date.today().year + 2))
        meses = {
            "01 — Janeiro": 1,  "02 — Fevereiro": 2, "03 — Março": 3,
            "04 — Abril": 4,    "05 — Maio": 5,       "06 — Junho": 6,
            "07 — Julho": 7,    "08 — Agosto": 8,     "09 — Setembro": 9,
            "10 — Outubro": 10, "11 — Novembro": 11,  "12 — Dezembro": 12,
        }
        c1, c2, c3 = st.columns(3)
        ano_sel = c1.selectbox("Ano", anos, index=anos.index(date.today().year))
        mes_lbl = c2.selectbox("Mês", list(meses.keys()), index=max(0, date.today().month - 2))
        mes_sel = meses[mes_lbl]
        cod_fin = c3.selectbox("Finalidade", ["0 — Original", "1 — Substituto"])

        dt_ini = primeiro_dia_mes(ano_sel, mes_sel)
        dt_fin = ultimo_dia_mes(ano_sel, mes_sel)
        st.info(f"Período: **{dt_ini[:2]}/{dt_ini[2:4]}/{dt_ini[4:]}** a **{dt_fin[:2]}/{dt_fin[2:4]}/{dt_fin[4:]}**")

        gerar = st.button("⚙️  Gerar e Validar Bloco 0", use_container_width=True, type="primary")

    with col_status:
        st.markdown("#### Resumo dos dados")
        m1, m2, m3 = st.columns(3)
        m1.metric("Empresa", "✓" if cfg else "✗")
        m2.metric("Participantes", len(participantes))
        m3.metric("Itens", len(itens))

        st.markdown("**Empresa:**")
        st.markdown(f"`{cfg.get('NOME', '-')}`")
        st.markdown(f"CNPJ: `{formatar_cnpj(cfg.get('CNPJ', ''))}`")
        st.markdown(f"UF: `{cfg.get('UF', '-')}` · Perfil: `{cfg.get('IND_PERFIL', '-')}`")

    if gerar:
        bloco = Bloco0()

        bloco.registro_0000 = Reg0000(
            COD_VER    = "019",
            COD_FIN    = cod_fin[0],
            DT_INI     = dt_ini,
            DT_FIN     = dt_fin,
            NOME       = cfg.get("NOME", ""),
            CNPJ       = cfg.get("CNPJ", ""),
            UF         = cfg.get("UF", ""),
            IE         = cfg.get("IE", ""),
            COD_MUN    = cfg.get("COD_MUN", ""),
            IM         = cfg.get("IM", ""),
            SUFRAMA    = cfg.get("SUFRAMA", ""),
            IND_PERFIL = cfg.get("IND_PERFIL", "A"),
            IND_ATIV   = cfg.get("IND_ATIV", "1"),
        )

        bloco.registro_0005 = Reg0005(
            FANTASIA = cfg.get("FANTASIA", ""),
            CEP      = cfg.get("CEP", ""),
            END      = cfg.get("END", ""),
            NUM      = cfg.get("NUM", ""),
            COMPL    = cfg.get("COMPL", ""),
            BAIRRO   = cfg.get("BAIRRO", ""),
            FONE     = cfg.get("FONE", ""),
            EMAIL    = cfg.get("EMAIL", ""),
            COD_MUN  = cfg.get("COD_MUN", ""),
        )

        if cfg.get("CONT_NOME"):
            bloco.registro_0100 = Reg0100(
                NOME    = cfg.get("CONT_NOME", ""),
                CPF     = cfg.get("CONT_CPF", ""),
                CRC     = cfg.get("CONT_CRC", ""),
                EMAIL   = cfg.get("CONT_EMAIL", ""),
                COD_MUN = cfg.get("COD_MUN", ""),
            )

        for p in participantes:
            bloco.adicionar_participante(Reg0150(
                COD_PART = p["COD_PART"],
                NOME     = p["NOME"],
                CNPJ     = p["CNPJ"],
                IE       = p.get("IE", ""),
                COD_MUN  = p.get("COD_MUN", ""),
                END      = p.get("END", ""),
                NUM      = p.get("NUM", ""),
                BAIRRO   = p.get("BAIRRO", ""),
            ))

        unidades_usadas = list({it["UNID_INV"] for it in itens})
        for u in sorted(unidades_usadas):
            bloco.adicionar_unidade(Reg0190(UNID=u, DESCR=DESCR_UNID.get(u, u)))

        for it in itens:
            bloco.adicionar_item(Reg0200(
                COD_ITEM   = it["COD_ITEM"],
                DESCR_ITEM = it["DESCR_ITEM"],
                COD_BARRA  = it.get("COD_BARRA", ""),
                UNID_INV   = it["UNID_INV"],
                TIPO_ITEM  = it.get("TIPO_ITEM", "00"),
                COD_NCM    = it.get("COD_NCM", ""),
                ALIQ_ICMS  = it.get("ALIQ_ICMS", ""),
            ))

        erros  = bloco.validar()
        linhas = bloco.to_lines()

        st.session_state.bloco            = bloco
        st.session_state.linhas_geradas   = linhas
        st.session_state.erros_validacao  = erros

        st.markdown("---")
        if erros:
            st.error(f"**{len(erros)} erro(s) de validação encontrado(s):**")
            for e in erros:
                st.markdown(f'<div class="err-item">{e}</div>', unsafe_allow_html=True)
        else:
            st.success(f"✅  Bloco 0 gerado com sucesso — **{len(linhas)} linhas**, sem erros!")

            nome_arquivo = f"sped_bloco0_{ano_sel}{mes_sel:02d}.txt"
            conteudo = "\r\n".join(linhas) + "\r\n"
            st.download_button(
                label="⬇️  Baixar arquivo .txt",
                data=conteudo.encode("latin-1", errors="replace"),
                file_name=nome_arquivo,
                mime="text/plain",
                use_container_width=True,
            )

    if st.session_state.linhas_geradas:
        st.markdown("---")
        st.markdown("#### Prévia das linhas geradas")
        html_linhas = ""
        for i, linha in enumerate(st.session_state.linhas_geradas, 1):
            num = f'<span class="file-line-num">{i:>3}</span>'
            html_linhas += num + colorir_linha(linha) + "<br>"
        st.markdown(
            f'<div class="file-preview">{html_linhas}</div>',
            unsafe_allow_html=True
        )
