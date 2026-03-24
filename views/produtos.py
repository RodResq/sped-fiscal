"""
views/produtos.py — Página 3: Produtos / Itens (Reg. 0200)
"""

import json
import streamlit as st
from pathlib import Path

ITENS_PATH = Path(__file__).parent.parent / "itens.json"

TIPOS_ITEM = {
    "00 — Mercadoria para revenda": "00",
    "01 — Matéria-prima":           "01",
    "02 — Embalagem":               "02",
    "03 — Produto em processo":     "03",
    "04 — Produto acabado":         "04",
    "05 — Subproduto":              "05",
    "06 — Produto intermediário":   "06",
    "07 — Material de uso e consumo": "07",
    "08 — Ativo imobilizado":       "08",
    "09 — Serviços":                "09",
    "10 — Outros insumos":          "10",
    "99 — Outras":                  "99",
}

UNIDADES = ["UN", "KG", "LT", "MT", "M2", "M3", "CX", "PC", "PR", "DZ", "GR", "TN"]


def render():
    st.subheader("Produtos / Itens — Reg. 0200")
    st.caption("Todos os produtos que aparecem nas NF-e do período precisam estar cadastrados aqui com NCM correto.")

    itens = json.loads(ITENS_PATH.read_text()) if ITENS_PATH.exists() else []

    col_add, col_lista = st.columns([1, 1], gap="large")

    with col_add:
        st.markdown("#### Adicionar item")
        with st.form("form_item"):
            icod   = st.text_input("Código do item *", placeholder="PROD001")
            idescr = st.text_input("Descrição *", placeholder="NOTEBOOK CORE I7 16GB SSD")
            c1, c2 = st.columns(2)
            incm   = c1.text_input("NCM * (8 dígitos)", placeholder="84713019",
                                   help="Nomenclatura Comum do Mercosul — 8 dígitos obrigatórios")
            iunid  = c2.selectbox("Unidade *", UNIDADES)
            c3, c4 = st.columns(2)
            itipo_lbl = c3.selectbox("Tipo do item *", list(TIPOS_ITEM.keys()))
            ialiq  = c4.text_input("Alíquota ICMS (%)", placeholder="12.00")
            ibarra = st.text_input("Código de barras (GTIN/EAN)", placeholder="7891234567890 — opcional")

            add_i = st.form_submit_button("➕  Adicionar Item", use_container_width=True)

        if add_i:
            erros_i = []
            if not icod:               erros_i.append("Código do item é obrigatório.")
            if not idescr:             erros_i.append("Descrição é obrigatória.")
            if len(incm.strip()) != 8: erros_i.append("NCM deve ter exatamente 8 dígitos.")
            if any(it["COD_ITEM"] == icod.upper() for it in itens):
                erros_i.append(f"Código '{icod}' já existe.")

            if erros_i:
                for e in erros_i:
                    st.error(e)
            else:
                itens.append({
                    "COD_ITEM":   icod.upper(),
                    "DESCR_ITEM": idescr.upper(),
                    "COD_NCM":    incm.strip(),
                    "UNID_INV":   iunid,
                    "TIPO_ITEM":  TIPOS_ITEM[itipo_lbl],
                    "ALIQ_ICMS":  ialiq.strip(),
                    "COD_BARRA":  ibarra.strip(),
                })
                ITENS_PATH.write_text(json.dumps(itens, ensure_ascii=False, indent=2))
                st.success(f"✅  Item **{icod.upper()}** adicionado!")
                st.rerun()

    with col_lista:
        st.markdown(f"#### Itens cadastrados ({len(itens)})")
        if not itens:
            st.info("Nenhum item cadastrado ainda.")
        else:
            for i, it in enumerate(itens):
                with st.expander(f"**{it['COD_ITEM']}** — {it['DESCR_ITEM'][:35]}"):
                    c1, c2 = st.columns(2)
                    c1.markdown(f"NCM: `{it.get('COD_NCM', '-')}`")
                    c2.markdown(f"Unidade: `{it.get('UNID_INV', '-')}`")
                    c1.markdown(f"Tipo: `{it.get('TIPO_ITEM', '-')}`")
                    c2.markdown(f"Alíq. ICMS: `{it.get('ALIQ_ICMS', '-')}%`")
                    if st.button("🗑️ Remover", key=f"del_i_{i}"):
                        itens.pop(i)
                        ITENS_PATH.write_text(json.dumps(itens, ensure_ascii=False, indent=2))
                        st.rerun()
