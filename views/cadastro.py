"""
views/cadastro.py — Página 1: Cadastro da Empresa (Reg. 0000 / 0005 / 0100)
"""

import re
import streamlit as st

from utils import (
    UFS, MUNICIPIOS_POR_UF,
    formatar_cnpj, limpar_cnpj,
    carregar_config, salvar_config,
)


def render():
    cfg_salvo = carregar_config()

    st.subheader("Cadastro da Empresa")
    st.caption("Dados fixos que alimentam os registros 0000 e 0005. Preencha uma vez — reutilizado em todo mês.")

    col_form, col_info = st.columns([2, 1], gap="large")

    with col_form:
        with st.form("form_empresa", clear_on_submit=False):

            st.markdown('<div class="section-title">Identificação fiscal</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            nome     = c1.text_input("Razão Social *", value=cfg_salvo.get("NOME", ""), placeholder="EMPRESA LTDA")
            fantasia = c2.text_input("Nome Fantasia",  value=cfg_salvo.get("FANTASIA", ""), placeholder="EMPRESA")

            c3, c4 = st.columns(2)
            cnpj_raw = c3.text_input("CNPJ *", value=cfg_salvo.get("CNPJ", ""), placeholder="00.000.000/0000-00",
                                     help="14 dígitos — pode digitar com ou sem máscara")
            ie       = c4.text_input("Inscrição Estadual *", value=cfg_salvo.get("IE", ""), placeholder="0612345678")

            c5, c6 = st.columns([1, 2])
            uf = c5.selectbox("UF *", UFS,
                index=UFS.index(cfg_salvo.get("UF", "PA")) if cfg_salvo.get("UF", "PA") in UFS else 0)

            municipios = MUNICIPIOS_POR_UF.get(uf, {"Outro (informe o código)": ""})
            nomes_mun = list(municipios.keys()) + ["Outro (informe o código)"]
            cod_mun_salvo = cfg_salvo.get("COD_MUN", "")
            mun_nome_salvo = next((k for k, v in municipios.items() if v == cod_mun_salvo), "Outro (informe o código)")
            mun_sel = c6.selectbox("Município *", nomes_mun,
                index=nomes_mun.index(mun_nome_salvo) if mun_nome_salvo in nomes_mun else len(nomes_mun) - 1)

            if mun_sel == "Outro (informe o código)":
                cod_mun = st.text_input("Código IBGE do Município (7 dígitos) *",
                    value=cod_mun_salvo, placeholder="1501402",
                    help="Consulte em ibge.gov.br ou no XML da NF-e campo <cMun>")
            else:
                cod_mun = municipios[mun_sel]
                st.info(f"Código IBGE: **{cod_mun}** — {mun_sel}/{uf}")

            im      = st.text_input("Inscrição Municipal (IM)", value=cfg_salvo.get("IM", ""),
                                    placeholder="Opcional — preencher se o município exigir ISS")
            suframa = st.text_input("Inscrição SUFRAMA", value=cfg_salvo.get("SUFRAMA", ""),
                                    placeholder="Opcional — apenas empresas da Zona Franca de Manaus")

            st.markdown('<div class="section-title" style="margin-top:16px">Endereço</div>', unsafe_allow_html=True)
            c7, c8, c9 = st.columns([3, 1, 1])
            end   = c7.text_input("Logradouro", value=cfg_salvo.get("END", ""), placeholder="RUA DAS FLORES")
            num   = c8.text_input("Número",     value=cfg_salvo.get("NUM", ""), placeholder="100")
            cep   = c9.text_input("CEP",        value=cfg_salvo.get("CEP", ""), placeholder="66000000")
            c10, c11 = st.columns(2)
            compl  = c10.text_input("Complemento", value=cfg_salvo.get("COMPL", ""), placeholder="SALA 10")
            bairro = c11.text_input("Bairro",       value=cfg_salvo.get("BAIRRO", ""), placeholder="CENTRO")
            c12, c13 = st.columns(2)
            fone  = c12.text_input("Telefone", value=cfg_salvo.get("FONE", ""), placeholder="91912345678")
            email = c13.text_input("E-mail",   value=cfg_salvo.get("EMAIL", ""), placeholder="fiscal@empresa.com.br")

            st.markdown('<div class="section-title" style="margin-top:16px">Configuração fiscal</div>', unsafe_allow_html=True)
            c14, c15 = st.columns(2)
            perfil_opt = {"A — Escrituração completa": "A",
                          "B — Escrituração simplificada": "B",
                          "C — Escrituração especial": "C"}
            ativ_opt   = {"0 — Industrial ou equiparado": "0",
                          "1 — Outros (comércio / serviços)": "1"}
            perfil_lbl = c14.selectbox("Perfil de Apresentação *",
                list(perfil_opt.keys()),
                index=list(perfil_opt.values()).index(cfg_salvo.get("IND_PERFIL", "A")))
            ativ_lbl   = c15.selectbox("Indicador de Atividade *",
                list(ativ_opt.keys()),
                index=list(ativ_opt.values()).index(cfg_salvo.get("IND_ATIV", "1")))

            st.markdown('<div class="section-title" style="margin-top:16px">Contabilista</div>', unsafe_allow_html=True)
            c16, c17 = st.columns(2)
            cont_nome  = c16.text_input("Nome do Contador", value=cfg_salvo.get("CONT_NOME", ""), placeholder="JOAO DA SILVA")
            cont_cpf   = c17.text_input("CPF do Contador",  value=cfg_salvo.get("CONT_CPF", ""),  placeholder="12345678901")
            c18, c19 = st.columns(2)
            cont_crc   = c18.text_input("CRC",              value=cfg_salvo.get("CONT_CRC", ""),   placeholder="PA-012345/O-1")
            cont_email = c19.text_input("E-mail do Contador", value=cfg_salvo.get("CONT_EMAIL", ""), placeholder="contador@escritorio.com.br")

            submitted = st.form_submit_button("💾  Salvar Cadastro da Empresa", use_container_width=True)

        if submitted:
            cnpj_limpo = limpar_cnpj(cnpj_raw)
            dados = {
                "NOME":       nome.strip().upper(),
                "FANTASIA":   fantasia.strip().upper(),
                "CNPJ":       cnpj_limpo,
                "IE":         ie.strip(),
                "UF":         uf,
                "COD_MUN":    cod_mun.strip(),
                "IM":         im.strip(),
                "SUFRAMA":    suframa.strip(),
                "END":        end.strip().upper(),
                "NUM":        num.strip(),
                "CEP":        re.sub(r"\D", "", cep),
                "COMPL":      compl.strip().upper(),
                "BAIRRO":     bairro.strip().upper(),
                "FONE":       re.sub(r"\D", "", fone),
                "EMAIL":      email.strip().lower(),
                "IND_PERFIL": perfil_opt[perfil_lbl],
                "IND_ATIV":   ativ_opt[ativ_lbl],
                "CONT_NOME":  cont_nome.strip().upper(),
                "CONT_CPF":   re.sub(r"\D", "", cont_cpf),
                "CONT_CRC":   cont_crc.strip(),
                "CONT_EMAIL": cont_email.strip().lower(),
            }
            erros_form = []
            if not dados["NOME"]:          erros_form.append("Razão Social é obrigatória.")
            if len(dados["CNPJ"]) != 14:   erros_form.append("CNPJ deve ter 14 dígitos.")
            if not dados["IE"]:            erros_form.append("Inscrição Estadual é obrigatória.")
            if len(dados["COD_MUN"]) != 7: erros_form.append("Código IBGE do município deve ter 7 dígitos.")

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
            st.markdown(f"**{cfg_salvo.get('NOME', '-')}**")
            st.markdown(f"CNPJ: `{formatar_cnpj(cfg_salvo.get('CNPJ', ''))}`")
            st.markdown(f"UF: `{cfg_salvo.get('UF', '-')}` · IE: `{cfg_salvo.get('IE', '-')}`")
            st.markdown(f"Perfil: `{cfg_salvo.get('IND_PERFIL', '-')}` · Atividade: `{cfg_salvo.get('IND_ATIV', '-')}`")
