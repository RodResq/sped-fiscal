"""
Testes do módulo Bloco 0 — EFD ICMS/IPI
Execute com: python -m pytest tests/test_bloco0.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sped_fiscal.bloco0 import (
    Bloco0, Reg0000, Reg0001, Reg0005, Reg0100,
    Reg0150, Reg0190, Reg0200, Reg0400, Reg0990,
)


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def bloco_minimo() -> Bloco0:
    """Monta um Bloco 0 válido mínimo para reuso nos testes."""
    bloco = Bloco0()
    bloco.registro_0000 = Reg0000(
        COD_VER="019",
        COD_FIN="0",
        DT_INI="01012024",
        DT_FIN="31012024",
        NOME="EMPRESA TESTE LTDA",
        CNPJ="12345678000195",
        UF="CE",
        IE="0123456789",
        COD_MUN="2304400",
        IND_PERFIL="A",
        IND_ATIV="0",
    )
    bloco.adicionar_unidade(Reg0190(UNID="UN", DESCR="Unidade"))
    bloco.adicionar_participante(Reg0150(
        COD_PART="CLI001",
        NOME="CLIENTE EXEMPLO SA",
        CNPJ="98765432000111",
        COD_MUN="2304400",
    ))
    bloco.adicionar_item(Reg0200(
        COD_ITEM="PROD001",
        DESCR_ITEM="PRODUTO EXEMPLO",
        UNID_INV="UN",
        TIPO_ITEM="00",
        COD_NCM="84713019",
    ))
    return bloco


# -----------------------------------------------------------------------
# Testes de geração (to_lines / to_text)
# -----------------------------------------------------------------------

class TestGeracao:

    def test_to_lines_retorna_lista(self):
        bloco = bloco_minimo()
        linhas = bloco.to_lines()
        assert isinstance(linhas, list)
        assert len(linhas) > 0

    def test_primeira_linha_e_0000(self):
        bloco = bloco_minimo()
        linhas = bloco.to_lines()
        assert linhas[0].startswith("|0000|")

    def test_ultima_linha_e_0990(self):
        bloco = bloco_minimo()
        linhas = bloco.to_lines()
        assert linhas[-1].startswith("|0990|")

    def test_qtd_lin_0990_correto(self):
        bloco = bloco_minimo()
        linhas = bloco.to_lines()
        total_declarado = int(linhas[-1].strip("|").split("|")[1])
        assert total_declarado == len(linhas)

    def test_linhas_formato_pipe(self):
        bloco = bloco_minimo()
        for linha in bloco.to_lines():
            assert linha.startswith("|"), f"Linha não começa com '|': {linha}"
            assert linha.endswith("|"), f"Linha não termina com '|': {linha}"

    def test_0000_campos_corretos(self):
        bloco = bloco_minimo()
        linha_0000 = bloco.to_lines()[0]
        partes = linha_0000.strip("|").split("|")
        assert partes[0] == "0000"
        assert partes[1] == "019"          # COD_VER
        assert partes[3] == "01012024"     # DT_INI
        assert partes[5] == "EMPRESA TESTE LTDA"  # NOME

    def test_sem_0000_levanta_erro(self):
        bloco = Bloco0()
        try:
            bloco.to_lines()
            assert False, "Devia ter levantado ValueError"
        except ValueError as e:
            assert "0000" in str(e)

    def test_to_text_usa_crlf(self):
        bloco = bloco_minimo()
        texto = bloco.to_text()
        assert "\r\n" in texto


# -----------------------------------------------------------------------
# Testes de leitura (from_lines)
# -----------------------------------------------------------------------

class TestLeitura:

    def test_roundtrip(self):
        """Gera → serializa → parseia → compara campos principais."""
        original = bloco_minimo()
        linhas = original.to_lines()
        lido = Bloco0.from_lines(linhas)

        assert lido.registro_0000.NOME == "EMPRESA TESTE LTDA"
        assert lido.registro_0000.CNPJ == "12345678000195"
        assert len(lido.participantes) == 1
        assert len(lido.itens) == 1
        assert len(lido.unidades) == 1

    def test_parse_0150_correto(self):
        bloco = bloco_minimo()
        linhas = bloco.to_lines()
        lido = Bloco0.from_lines(linhas)
        part = lido.buscar_participante("CLI001")
        assert part is not None
        assert part.NOME == "CLIENTE EXEMPLO SA"

    def test_parse_0200_correto(self):
        bloco = bloco_minimo()
        linhas = bloco.to_lines()
        lido = Bloco0.from_lines(linhas)
        item = lido.buscar_item("PROD001")
        assert item is not None
        assert item.COD_NCM == "84713019"

    def test_linhas_invalidas_ignoradas(self):
        linhas = [
            "# comentário",
            "",
            "|9999|campo_desconhecido|",
            "|0000|019|0|01012024|31012024|EMPRESA|12345678000195||CE|IE|2304400|||A|0|",
            "|0001|0|",
            "|0990|2|",
        ]
        bloco = Bloco0.from_lines(linhas)
        assert bloco.registro_0000 is not None
        assert bloco.registro_0000.NOME == "EMPRESA"

    def test_multiplos_participantes(self):
        bloco = bloco_minimo()
        bloco.adicionar_participante(Reg0150(
            COD_PART="FORN001",
            NOME="FORNECEDOR X",
            CNPJ="11122233000144",
        ))
        linhas = bloco.to_lines()
        lido = Bloco0.from_lines(linhas)
        assert len(lido.participantes) == 2
        assert lido.buscar_participante("FORN001").NOME == "FORNECEDOR X"


# -----------------------------------------------------------------------
# Testes de validação
# -----------------------------------------------------------------------

class TestValidacao:

    def test_bloco_valido_sem_erros(self):
        erros = bloco_minimo().validar()
        assert erros == [], f"Erros inesperados: {erros}"

    def test_0000_cod_ver_invalido(self):
        bloco = bloco_minimo()
        bloco.registro_0000.COD_VER = "999"
        erros = bloco.validar()
        assert any("COD_VER" in e for e in erros)

    def test_0000_sem_cnpj_e_cpf(self):
        bloco = bloco_minimo()
        bloco.registro_0000.CNPJ = ""
        bloco.registro_0000.CPF = ""
        erros = bloco.validar()
        assert any("CNPJ" in e or "CPF" in e for e in erros)

    def test_0000_dt_ini_formato_errado(self):
        bloco = bloco_minimo()
        bloco.registro_0000.DT_INI = "2024-01-01"
        erros = bloco.validar()
        assert any("DT_INI" in e for e in erros)

    def test_0200_ncm_incorreto(self):
        bloco = bloco_minimo()
        bloco.itens[0].COD_NCM = "123"   # deve ter 8 dígitos
        erros = bloco.validar()
        assert any("COD_NCM" in e for e in erros)

    def test_0200_tipo_item_invalido(self):
        bloco = bloco_minimo()
        bloco.itens[0].TIPO_ITEM = "XX"
        erros = bloco.validar()
        assert any("TIPO_ITEM" in e for e in erros)

    def test_0200_unidade_nao_cadastrada(self):
        bloco = bloco_minimo()
        bloco.itens[0].UNID_INV = "KG"   # KG não está no 0190
        erros = bloco.validar()
        assert any("UNID_INV" in e for e in erros)

    def test_ind_perfil_invalido(self):
        bloco = bloco_minimo()
        bloco.registro_0000.IND_PERFIL = "X"
        erros = bloco.validar()
        assert any("IND_PERFIL" in e for e in erros)


# -----------------------------------------------------------------------
# Testes de serialização dos registros (RegistroBase)
# -----------------------------------------------------------------------

class TestRegistroBase:

    def test_to_sped_line_formato(self):
        r = Reg0190(UNID="KG", DESCR="Quilograma")
        linha = r.to_sped_line()
        assert linha == "|0190|KG|Quilograma|"

    def test_from_sped_line_roundtrip(self):
        original = Reg0150(
            COD_PART="F001",
            NOME="FORNECEDOR A",
            COD_PAIS="1058",
            CNPJ="00111222000133",
        )
        linha = original.to_sped_line()
        lido = Reg0150.from_sped_line(linha)
        assert lido.COD_PART == "F001"
        assert lido.NOME == "FORNECEDOR A"
        assert lido.CNPJ == "00111222000133"

    def test_campos_none_viram_string_vazia(self):
        r = Reg0005()
        linha = r.to_sped_line()
        assert "None" not in linha


# -----------------------------------------------------------------------
# Runner simples (sem pytest)
# -----------------------------------------------------------------------

if __name__ == "__main__":
    import traceback
    classes = [TestGeracao, TestLeitura, TestValidacao, TestRegistroBase]
    passou = falhou = 0
    for cls in classes:
        obj = cls()
        for nome in [m for m in dir(obj) if m.startswith("test_")]:
            try:
                getattr(obj, nome)()
                print(f"  ✓  {cls.__name__}.{nome}")
                passou += 1
            except Exception:
                print(f"  ✗  {cls.__name__}.{nome}")
                traceback.print_exc()
                falhou += 1
    print(f"\n{passou} passou | {falhou} falhou")
