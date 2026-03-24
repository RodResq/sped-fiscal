"""
app.py — Interface web Streamlit para o projeto SPED Fiscal
Cadastro de empresa, geração e validação do Bloco 0

Execute com:
    cd sped_fiscal
    streamlit run app.py
"""

import sys, os, json, re
from pathlib import Path
from datetime import date, timedelta
import calendar

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from sped_fiscal.bloco0 import (
    Bloco0, Reg0000, Reg0005, Reg0100,
    Reg0150, Reg0190, Reg0200, Reg0400,
)
from sped_fiscal.preview import preview_arquivo, detectar_encoding

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="SPED Fiscal — Cadastro",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Estilos globais ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #1a1a2e;
}
section[data-testid="stSidebar"] * {
    color: #e0e0f0 !important;
}
section[data-testid="stSidebar"] .stRadio label {
    color: #b0b0d0 !important;
    font-size: 14px;
}

/* Cabeçalho principal */
.sped-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
    border-radius: 12px;
    padding: 28px 32px 22px;
    margin-bottom: 28px;
    border-left: 5px solid #534AB7;
}
.sped-header h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 22px;
    font-weight: 600;
    color: #ffffff;
    margin: 0 0 4px;
    letter-spacing: -0.5px;
}
.sped-header p {
    font-size: 13px;
    color: #8888bb;
    margin: 0;
    font-family: 'IBM Plex Mono', monospace;
}

/* Badges de status */
.badge-ok   { background:#e1f5ee; color:#085041; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-err  { background:#faece7; color:#712b13; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }
.badge-info { background:#eeedfe; color:#3c3489; padding:3px 10px; border-radius:20px; font-size:12px; font-weight:600; }

/* Caixas de seção */
.section-box {
    background: #f8f7ff;
    border: 1px solid #dddaf8;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 16px;
}
.section-title {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .08em;
    color: #534AB7;
    margin-bottom: 12px;
    font-family: 'IBM Plex Mono', monospace;
}

/* Preview do arquivo */
.file-preview {
    background: #0d1117;
    border-radius: 8px;
    padding: 16px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #58a6ff;
    line-height: 1.7;
    border: 1px solid #21262d;
    overflow-x: auto;
}
.file-line-num { color: #484f58; margin-right: 12px; user-select: none; }
.reg-0000 { color: #7ee787; }
.reg-0001 { color: #a5d6ff; }
.reg-0005 { color: #ffa657; }
.reg-0150 { color: #d2a8ff; }
.reg-0200 { color: #ff7b72; }
.reg-default { color: #8b949e; }

/* Métrica */
.metric-box {
    background: white;
    border: 1px solid #e0ddf8;
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
}
.metric-num  { font-size: 28px; font-weight: 600; color: #534AB7; font-family: 'IBM Plex Mono', monospace; }
.metric-lbl  { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: .06em; margin-top: 2px; }

/* Botões */
.stButton > button {
    background: #534AB7;
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 14px;
    padding: 10px 24px;
    transition: background .2s;
}
.stButton > button:hover { background: #3C3489; }

/* Remover padding do topo */
.block-container { padding-top: 1.5rem; }

/* Erros e sucesso */
.err-item { font-size: 13px; padding: 4px 0; color: #a32d2d; }
.err-item::before { content: "✗  "; font-weight: bold; }
.ok-msg { font-size: 14px; color: #085041; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

# ── Funções auxiliares ────────────────────────────────────────────────────────

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
    "Fortaleza":      "2304400",
    "Caucaia":        "2303709",
    "Juazeiro do Norte": "2307304",
    "Sobral":         "2312908",
    "Maracanaú":      "2307650",
    "Crato":          "2304202",
    "Iguatu":         "2305407",
    "Quixadá":        "2311405",
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
    # Escapa HTML
    linha_safe = linha.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<span class="{cls}">{linha_safe}</span>'


def carregar_config() -> dict:
    cfg_path = Path(__file__).parent / "config_empresa.json"
    if cfg_path.exists():
        with open(cfg_path) as f:
            return json.load(f)
    return {}


def salvar_config(dados: dict):
    cfg_path = Path(__file__).parent / "config_empresa.json"
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


# ── Estado da sessão ──────────────────────────────────────────────────────────
if "bloco" not in st.session_state:
    st.session_state.bloco = None
if "linhas_geradas" not in st.session_state:
    st.session_state.linhas_geradas = []
if "erros_validacao" not in st.session_state:
    st.session_state.erros_validacao = []

cfg_salvo = carregar_config()

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
        "<small style='color:#6666aa'>Projeto Piloto Python<br>"
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

# ════════════════════════════════════════════════════════════════════════════════
# PÁGINA 1 — Cadastro da Empresa
# ════════════════════════════════════════════════════════════════════════════════
if "Cadastro" in pagina:

    st.subheader("Cadastro da Empresa")
    st.caption("Dados fixos que alimentam os registros 0000 e 0005. Preencha uma vez — reutilizado em todo mês.")

    col_form, col_info = st.columns([2, 1], gap="large")

    with col_form:
        with st.form("form_empresa", clear_on_submit=False):

            st.markdown('<div class="section-title">Identificação fiscal</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            nome    = c1.text_input("Razão Social *", value=cfg_salvo.get("NOME", ""), placeholder="EMPRESA LTDA")
            fantasia= c2.text_input("Nome Fantasia",  value=cfg_salvo.get("FANTASIA", ""), placeholder="EMPRESA")

            c3, c4 = st.columns(2)
            cnpj_raw= c3.text_input("CNPJ *", value=cfg_salvo.get("CNPJ", ""), placeholder="00.000.000/0000-00",
                                     help="14 dígitos — pode digitar com ou sem máscara")
            ie      = c4.text_input("Inscrição Estadual *", value=cfg_salvo.get("IE", ""), placeholder="0612345678")

            c5, c6 = st.columns([1, 2])
            uf = c5.selectbox("UF *", UFS,
                index=UFS.index(cfg_salvo.get("UF", "PA")) if cfg_salvo.get("UF","PA") in UFS else 0)

            municipios = MUNICIPIOS_POR_UF.get(uf, {"Outro (informe o código)": ""})
            nomes_mun = list(municipios.keys()) + ["Outro (informe o código)"]
            cod_mun_salvo = cfg_salvo.get("COD_MUN", "")
            mun_nome_salvo = next((k for k, v in municipios.items() if v == cod_mun_salvo), "Outro (informe o código)")
            mun_sel = c6.selectbox("Município *", nomes_mun,
                index=nomes_mun.index(mun_nome_salvo) if mun_nome_salvo in nomes_mun else len(nomes_mun)-1)

            if mun_sel == "Outro (informe o código)":
                cod_mun = st.text_input("Código IBGE do Município (7 dígitos) *",
                    value=cod_mun_salvo, placeholder="1501402",
                    help="Consulte em ibge.gov.br ou no XML da NF-e campo <cMun>")
            else:
                cod_mun = municipios[mun_sel]
                st.info(f"Código IBGE: **{cod_mun}** — {mun_sel}/{uf}")

            im     = st.text_input("Inscrição Municipal (IM)", value=cfg_salvo.get("IM", ""),
                                    placeholder="Opcional — preencher se o município exigir ISS")
            suframa= st.text_input("Inscrição SUFRAMA", value=cfg_salvo.get("SUFRAMA", ""),
                                    placeholder="Opcional — apenas empresas da Zona Franca de Manaus")

            st.markdown('<div class="section-title" style="margin-top:16px">Endereço</div>', unsafe_allow_html=True)
            c7, c8, c9 = st.columns([3, 1, 1])
            end    = c7.text_input("Logradouro", value=cfg_salvo.get("END", ""), placeholder="RUA DAS FLORES")
            num    = c8.text_input("Número",     value=cfg_salvo.get("NUM", ""), placeholder="100")
            cep    = c9.text_input("CEP",        value=cfg_salvo.get("CEP", ""), placeholder="66000000")
            c10, c11 = st.columns(2)
            compl  = c10.text_input("Complemento", value=cfg_salvo.get("COMPL", ""), placeholder="SALA 10")
            bairro = c11.text_input("Bairro",       value=cfg_salvo.get("BAIRRO", ""), placeholder="CENTRO")
            c12, c13 = st.columns(2)
            fone   = c12.text_input("Telefone", value=cfg_salvo.get("FONE", ""), placeholder="91912345678")
            email  = c13.text_input("E-mail",   value=cfg_salvo.get("EMAIL", ""), placeholder="fiscal@empresa.com.br")

            st.markdown('<div class="section-title" style="margin-top:16px">Configuração fiscal</div>', unsafe_allow_html=True)
            c14, c15 = st.columns(2)
            perfil_opt = {"A — Escrituração completa": "A",
                          "B — Escrituração simplificada": "B",
                          "C — Escrituração especial": "C"}
            ativ_opt   = {"0 — Industrial ou equiparado": "0",
                          "1 — Outros (comércio / serviços)": "1"}
            perfil_lbl = c14.selectbox("Perfil de Apresentação *",
                list(perfil_opt.keys()),
                index=list(perfil_opt.values()).index(cfg_salvo.get("IND_PERFIL","A")))
            ativ_lbl   = c15.selectbox("Indicador de Atividade *",
                list(ativ_opt.keys()),
                index=list(ativ_opt.values()).index(cfg_salvo.get("IND_ATIV","1")))

            st.markdown('<div class="section-title" style="margin-top:16px">Contabilista</div>', unsafe_allow_html=True)
            c16, c17 = st.columns(2)
            cont_nome = c16.text_input("Nome do Contador", value=cfg_salvo.get("CONT_NOME",""), placeholder="JOAO DA SILVA")
            cont_cpf  = c17.text_input("CPF do Contador",  value=cfg_salvo.get("CONT_CPF",""),  placeholder="12345678901")
            c18, c19 = st.columns(2)
            cont_crc  = c18.text_input("CRC",   value=cfg_salvo.get("CONT_CRC",""),   placeholder="PA-012345/O-1")
            cont_email= c19.text_input("E-mail do Contador", value=cfg_salvo.get("CONT_EMAIL",""), placeholder="contador@escritorio.com.br")

            submitted = st.form_submit_button("💾  Salvar Cadastro da Empresa", use_container_width=True)

        if submitted:
            cnpj_limpo = limpar_cnpj(cnpj_raw)
            dados = {
                "NOME": nome.strip().upper(),
                "FANTASIA": fantasia.strip().upper(),
                "CNPJ": cnpj_limpo,
                "IE": ie.strip(),
                "UF": uf,
                "COD_MUN": cod_mun.strip(),
                "IM": im.strip(),
                "SUFRAMA": suframa.strip(),
                "END": end.strip().upper(),
                "NUM": num.strip(),
                "CEP": re.sub(r"\D","", cep),
                "COMPL": compl.strip().upper(),
                "BAIRRO": bairro.strip().upper(),
                "FONE": re.sub(r"\D","", fone),
                "EMAIL": email.strip().lower(),
                "IND_PERFIL": perfil_opt[perfil_lbl],
                "IND_ATIV": ativ_opt[ativ_lbl],
                "CONT_NOME": cont_nome.strip().upper(),
                "CONT_CPF": re.sub(r"\D","", cont_cpf),
                "CONT_CRC": cont_crc.strip(),
                "CONT_EMAIL": cont_email.strip().lower(),
            }
            # Validação rápida
            erros_form = []
            if not dados["NOME"]:         erros_form.append("Razão Social é obrigatória.")
            if len(dados["CNPJ"]) != 14:  erros_form.append("CNPJ deve ter 14 dígitos.")
            if not dados["IE"]:           erros_form.append("Inscrição Estadual é obrigatória.")
            if len(dados["COD_MUN"]) != 7:erros_form.append("Código IBGE do município deve ter 7 dígitos.")

            if erros_form:
                for e in erros_form:
                    st.error(e)
            else:
                salvar_config(dados)
                st.success("✅  Cadastro salvo com sucesso em `config_empresa.json`!")
                st.balloons()

    with col_info:
        st.markdown("#### O que é cada campo?")

        with st.expander("IND_PERFIL — Perfil A, B ou C", expanded=True):
            st.markdown("""
**A — Escrituração completa**
Obrigatório para indústrias, importadores e grandes contribuintes. Inclui todos os blocos.

**B — Escrituração simplificada**
Para contribuintes de menor porte. Alguns registros do Bloco C e K são dispensados.

**C — Especial**
Definido por legislação estadual específica. Consulte a SEFAZ do seu estado.

> Dúvida? Pergunte ao seu contador — ele define o perfil conforme o porte da empresa.
""")

        with st.expander("IND_ATIV — Atividade 0 ou 1"):
            st.markdown("""
**0 — Industrial ou equiparado**
Empresa que industrializa produtos (fabricação, montagem, transformação) ou é equiparada a industrial pela legislação do IPI.

**1 — Outros**
Comércio, serviços, distribuidores, revendedores.
""")

        with st.expander("COD_MUN — Código IBGE"):
            st.markdown("""
O código IBGE tem **7 dígitos** e identifica o município do estabelecimento.

Como encontrar:
- No **XML da NF-e** emitida pela empresa, campo `<cMun>`
- No site **ibge.gov.br** → Cidades e Estados
- Na tabela oficial do Portal SPED

Exemplos:
- Belém/PA → `1501402`
- Fortaleza/CE → `2304400`
- São Paulo/SP → `3550308`
""")

        if cfg_salvo:
            st.markdown("---")
            st.markdown("#### Cadastro atual")
            st.markdown(f"**{cfg_salvo.get('NOME','-')}**")
            st.markdown(f"CNPJ: `{formatar_cnpj(cfg_salvo.get('CNPJ',''))}`")
            st.markdown(f"UF: `{cfg_salvo.get('UF','-')}` · IE: `{cfg_salvo.get('IE','-')}`")
            st.markdown(f"Perfil: `{cfg_salvo.get('IND_PERFIL','-')}` · Atividade: `{cfg_salvo.get('IND_ATIV','-')}`")


# ════════════════════════════════════════════════════════════════════════════════
# PÁGINA 2 — Participantes
# ════════════════════════════════════════════════════════════════════════════════
elif "Participantes" in pagina:
    st.subheader("Participantes — Reg. 0150")
    st.caption("Clientes e fornecedores que aparecem nas NF-e do período. Cada CNPJ precisa estar cadastrado aqui.")

    part_path = Path(__file__).parent / "participantes.json"
    participantes = json.loads(part_path.read_text()) if part_path.exists() else []

    col_add, col_lista = st.columns([1, 1], gap="large")

    with col_add:
        st.markdown("#### Adicionar participante")
        with st.form("form_part"):
            cod   = st.text_input("Código interno *", placeholder="CLI001", help="Código único que você define")
            pnome = st.text_input("Nome/Razão Social *", placeholder="FORNECEDOR EXEMPLO LTDA")
            pcnpj = st.text_input("CNPJ *", placeholder="00.000.000/0000-00")
            pie   = st.text_input("Inscrição Estadual", placeholder="opcional")
            c1,c2 = st.columns(2)
            puf   = c1.selectbox("UF", UFS, index=UFS.index("PA"))
            pmun  = c2.text_input("Cód. IBGE Município", placeholder="1501402")
            pend  = st.text_input("Endereço", placeholder="AV PRINCIPAL")
            c3,c4 = st.columns(2)
            pnum  = c3.text_input("Número", placeholder="100")
            pbairro=c4.text_input("Bairro", placeholder="CENTRO")

            add = st.form_submit_button("➕  Adicionar Participante", use_container_width=True)

        if add:
            pcnpj_limpo = limpar_cnpj(pcnpj)
            erros_p = []
            if not cod:               erros_p.append("Código interno é obrigatório.")
            if not pnome:             erros_p.append("Nome é obrigatório.")
            if len(pcnpj_limpo) != 14:erros_p.append("CNPJ deve ter 14 dígitos.")
            if any(p["COD_PART"] == cod for p in participantes):
                erros_p.append(f"Código '{cod}' já existe.")

            if erros_p:
                for e in erros_p: st.error(e)
            else:
                participantes.append({
                    "COD_PART": cod.upper(),
                    "NOME": pnome.upper(),
                    "CNPJ": pcnpj_limpo,
                    "IE": pie.strip(),
                    "UF": puf,
                    "COD_MUN": pmun.strip(),
                    "END": pend.upper(),
                    "NUM": pnum,
                    "BAIRRO": pbairro.upper(),
                })
                part_path.write_text(json.dumps(participantes, ensure_ascii=False, indent=2))
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
                    st.markdown(f"UF/Município: `{p.get('UF','-')}` · `{p.get('COD_MUN','-')}`")
                    if st.button("🗑️ Remover", key=f"del_p_{i}"):
                        participantes.pop(i)
                        part_path.write_text(json.dumps(participantes, ensure_ascii=False, indent=2))
                        st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# PÁGINA 3 — Produtos / Itens
# ════════════════════════════════════════════════════════════════════════════════
elif "Produtos" in pagina:
    st.subheader("Produtos / Itens — Reg. 0200")
    st.caption("Todos os produtos que aparecem nas NF-e do período precisam estar cadastrados aqui com NCM correto.")

    itens_path = Path(__file__).parent / "itens.json"
    itens = json.loads(itens_path.read_text()) if itens_path.exists() else []

    TIPOS_ITEM = {
        "00 — Mercadoria para revenda": "00",
        "01 — Matéria-prima": "01",
        "02 — Embalagem": "02",
        "03 — Produto em processo": "03",
        "04 — Produto acabado": "04",
        "05 — Subproduto": "05",
        "06 — Produto intermediário": "06",
        "07 — Material de uso e consumo": "07",
        "08 — Ativo imobilizado": "08",
        "09 — Serviços": "09",
        "10 — Outros insumos": "10",
        "99 — Outras": "99",
    }
    UNIDADES = ["UN", "KG", "LT", "MT", "M2", "M3", "CX", "PC", "PR", "DZ", "GR", "TN"]

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
            if not icod:              erros_i.append("Código do item é obrigatório.")
            if not idescr:            erros_i.append("Descrição é obrigatória.")
            if len(incm.strip()) != 8:erros_i.append("NCM deve ter exatamente 8 dígitos.")
            if any(it["COD_ITEM"] == icod.upper() for it in itens):
                erros_i.append(f"Código '{icod}' já existe.")

            if erros_i:
                for e in erros_i: st.error(e)
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
                itens_path.write_text(json.dumps(itens, ensure_ascii=False, indent=2))
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
                    c1.markdown(f"NCM: `{it.get('COD_NCM','-')}`")
                    c2.markdown(f"Unidade: `{it.get('UNID_INV','-')}`")
                    c1.markdown(f"Tipo: `{it.get('TIPO_ITEM','-')}`")
                    c2.markdown(f"Alíq. ICMS: `{it.get('ALIQ_ICMS','-')}%`")
                    if st.button("🗑️ Remover", key=f"del_i_{i}"):
                        itens.pop(i)
                        itens_path.write_text(json.dumps(itens, ensure_ascii=False, indent=2))
                        st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# PÁGINA 4 — Gerar Bloco 0
# ════════════════════════════════════════════════════════════════════════════════
elif "Gerar" in pagina:
    st.subheader("Gerar Bloco 0")
    st.caption("Monta o arquivo .txt do Bloco 0 a partir dos cadastros salvos e valida antes de exportar.")

    cfg = carregar_config()
    part_path = Path(__file__).parent / "participantes.json"
    itens_path = Path(__file__).parent / "itens.json"
    participantes = json.loads(part_path.read_text()) if part_path.exists() else []
    itens = json.loads(itens_path.read_text()) if itens_path.exists() else []

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
        mes_lbl = c2.selectbox("Mês", list(meses.keys()),
                               index=max(0, date.today().month - 2))
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
        st.markdown(f"`{cfg.get('NOME','-')}`")
        st.markdown(f"CNPJ: `{formatar_cnpj(cfg.get('CNPJ',''))}`")
        st.markdown(f"UF: `{cfg.get('UF','-')}` · Perfil: `{cfg.get('IND_PERFIL','-')}`")

    if gerar:
        bloco = Bloco0()

        # 0000
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

        # 0005
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

        # 0100
        if cfg.get("CONT_NOME"):
            bloco.registro_0100 = Reg0100(
                NOME    = cfg.get("CONT_NOME", ""),
                CPF     = cfg.get("CONT_CPF", ""),
                CRC     = cfg.get("CONT_CRC", ""),
                EMAIL   = cfg.get("CONT_EMAIL", ""),
                COD_MUN = cfg.get("COD_MUN", ""),
            )

        # 0150 participantes
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

        # 0190 unidades únicas dos itens
        unidades_usadas = list({it["UNID_INV"] for it in itens})
        descr_unid = {"UN":"Unidade","KG":"Quilograma","LT":"Litro","MT":"Metro",
                      "M2":"Metro quadrado","M3":"Metro cubico","CX":"Caixa",
                      "PC":"Peca","PR":"Par","DZ":"Duzia","GR":"Grama","TN":"Tonelada"}
        for u in sorted(unidades_usadas):
            bloco.adicionar_unidade(Reg0190(UNID=u, DESCR=descr_unid.get(u, u)))

        # 0200 itens
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

        # Validar
        erros = bloco.validar()
        linhas = bloco.to_lines()

        st.session_state.bloco = bloco
        st.session_state.linhas_geradas = linhas
        st.session_state.erros_validacao = erros

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

    # Mostra prévia se já gerou
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


# ════════════════════════════════════════════════════════════════════════════════
# PÁGINA 5 — Preview de arquivo existente
# ════════════════════════════════════════════════════════════════════════════════
elif "Preview" in pagina:
    st.subheader("Preview de Arquivo EFD")
    st.caption("Faça upload de um arquivo .txt EFD existente para inspecionar antes de parsear.")

    uploaded = st.file_uploader("Selecione o arquivo .txt EFD", type=["txt"])

    if uploaded:
        tmp_path = Path("/tmp") / uploaded.name
        tmp_path.write_bytes(uploaded.read())

        enc = detectar_encoding(str(tmp_path))
        linhas = tmp_path.read_text(encoding=enc, errors="replace").splitlines()

        # Métricas
        contagem: dict[str, int] = {}
        for linha in linhas:
            linha = linha.strip()
            if linha.startswith("|"):
                reg = linha.strip("|").split("|")[0]
                contagem[reg] = contagem.get(reg, 0) + 1

        st.markdown(f"**Arquivo:** `{uploaded.name}` · **Encoding detectado:** `{enc}` · **Total de linhas:** `{len(linhas)}`")

        # Identifica empresa
        for linha in linhas:
            if linha.startswith("|0000|"):
                partes = linha.strip("|").split("|")
                if len(partes) >= 6:
                    st.success(f"**Empresa:** {partes[5]}  ·  **CNPJ:** {formatar_cnpj(partes[6])}  ·  "
                               f"**Período:** {partes[3][:2]}/{partes[3][2:4]}/{partes[3][4:]}  a  "
                               f"{partes[4][:2]}/{partes[4][2:4]}/{partes[4][4:]}")
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

        # Parsear e validar
        if st.button("🔍  Parsear e Validar Bloco 0", use_container_width=True):
            bloco_lido = Bloco0.from_lines(linhas)
            erros = bloco_lido.validar()
            if erros:
                st.error(f"**{len(erros)} erro(s) encontrado(s):**")
                for e in erros:
                    st.markdown(f'<div class="err-item">{e}</div>', unsafe_allow_html=True)
            else:
                st.success(f"✅  Arquivo válido! {len(bloco_lido.participantes)} participantes · "
                           f"{len(bloco_lido.itens)} itens · {len(bloco_lido.unidades)} unidades.")
