"""
app.py — Ponto de entrada da interface web SPED Fiscal.

Execute com:
    streamlit run app.py
"""

import sys
import streamlit as st
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from views import cadastro, participantes, produtos, gerar_bloco0, preview_efd

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="SPED Fiscal — Cadastro",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos globais ───────────────────────────────────────────────────────────
_css = (Path(__file__).parent / "assets" / "style.css").read_text(encoding="utf-8")
st.markdown(f"<style>{_css}</style>", unsafe_allow_html=True)

# ── Estado da sessão ──────────────────────────────────────────────────────────
if "bloco" not in st.session_state:
    st.session_state.bloco = None
if "linhas_geradas" not in st.session_state:
    st.session_state.linhas_geradas = []
if "erros_validacao" not in st.session_state:
    st.session_state.erros_validacao = []

# ── Sidebar — navegação ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧾 SPED Fiscal")
    st.markdown("**EFD ICMS/IPI — Leiaute 019**")
    st.markdown("---")
    pagina = st.radio("Módulo", [
        "📋  Cadastro da Empresa",
        "👥  Participantes",
        "📦  Produtos / Itens",
        "⚙️  Gerar Bloco 0",
        "🔍  Preview do Arquivo",
    ])
    st.markdown("---")
    st.markdown(
        "<small style='color:#6666aa'>Projeto Piloto<br>"
        "Leiaute 019 · PVA 6.0.1</small>",
        unsafe_allow_html=True
    )

# ── Cabeçalho ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="sped-header">
  <h1>🧾 SPED Fiscal — EFD ICMS/IPI</h1>
  <p>Geração, validação e envio automatizado · Leiaute 019 · Guia Prático 3.1.9</p>
</div>
""", unsafe_allow_html=True)

# ── Roteamento ────────────────────────────────────────────────────────────────
if   "Cadastro"      in pagina: cadastro.render()
elif "Participantes" in pagina: participantes.render()
elif "Produtos"      in pagina: produtos.render()
elif "Gerar"         in pagina: gerar_bloco0.render()
elif "Preview"       in pagina: preview_efd.render()
