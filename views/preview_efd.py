"""
views/preview_efd.py — Página 5: Preview de arquivo EFD existente
"""

from pathlib import Path

import streamlit as st

from utils import formatar_cnpj, colorir_linha
from sped_fiscal.bloco0 import Bloco0
from sped_fiscal.preview import detectar_encoding


def render():
    st.subheader("Preview de Arquivo EFD")
    st.caption("Faça upload de um arquivo .txt EFD existente para inspecionar antes de parsear.")

    uploaded = st.file_uploader("Selecione o arquivo .txt EFD", type=["txt"])

    if not uploaded:
        return

    tmp_path = Path("/tmp") / uploaded.name
    tmp_path.write_bytes(uploaded.read())

    enc    = detectar_encoding(str(tmp_path))
    linhas = tmp_path.read_text(encoding=enc, errors="replace").splitlines()

    contagem: dict[str, int] = {}
    for linha in linhas:
        linha = linha.strip()
        if linha.startswith("|"):
            reg = linha.strip("|").split("|")[0]
            contagem[reg] = contagem.get(reg, 0) + 1

    st.markdown(
        f"**Arquivo:** `{uploaded.name}` · "
        f"**Encoding detectado:** `{enc}` · "
        f"**Total de linhas:** `{len(linhas)}`"
    )

    for linha in linhas:
        if linha.startswith("|0000|"):
            partes = linha.strip("|").split("|")
            if len(partes) >= 6:
                st.success(
                    f"**Empresa:** {partes[5]}  ·  **CNPJ:** {formatar_cnpj(partes[6])}  ·  "
                    f"**Período:** {partes[3][:2]}/{partes[3][2:4]}/{partes[3][4:]}  a  "
                    f"{partes[4][:2]}/{partes[4][2:4]}/{partes[4][4:]}"
                )
            break

    col_cont, col_prev = st.columns([1, 2])

    with col_cont:
        st.markdown("#### Registros encontrados")
        bloco_ant = None
        for cod in sorted(contagem):
            bloco = cod[0] if cod else "?"
            if bloco != bloco_ant:
                st.markdown(f"**Bloco {bloco}**")
                bloco_ant = bloco
            st.markdown(f"&nbsp;&nbsp;`{cod}` — {contagem[cod]}x")

    with col_prev:
        st.markdown("#### Primeiras 20 linhas")
        html_prev = ""
        for i, linha in enumerate(linhas[:20], 1):
            num = f'<span class="file-line-num">{i:>3}</span>'
            html_prev += num + colorir_linha(linha) + "<br>"
        st.markdown(
            f'<div class="file-preview">{html_prev}</div>',
            unsafe_allow_html=True
        )

    if st.button("🔍  Parsear e Validar Bloco 0", use_container_width=True):
        bloco_lido = Bloco0.from_lines(linhas)
        erros = bloco_lido.validar()
        if erros:
            st.error(f"**{len(erros)} erro(s) encontrado(s):**")
            for e in erros:
                st.markdown(f'<div class="err-item">{e}</div>', unsafe_allow_html=True)
        else:
            st.success(
                f"✅  Arquivo válido! {len(bloco_lido.participantes)} participantes · "
                f"{len(bloco_lido.itens)} itens · {len(bloco_lido.unidades)} unidades."
            )
