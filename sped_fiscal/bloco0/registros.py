"""
Bloco 0 — Abertura, Identificação e Referências
Leiaute: EFD ICMS/IPI — Guia Prático 3.1.9 (Leiaute 019)

Registros implementados:
    0000 - Abertura do arquivo e identificação do contribuinte
    0001 - Abertura do Bloco 0
    0005 - Dados complementares do contribuinte
    0015 - Dados do contribuinte substituto ou do responsável
    0100 - Dados do contabilista
    0150 - Tabela de cadastro do participante
    0175 - Alteração da tabela de cadastro de participantes
    0190 - Identificação das unidades de medida
    0200 - Tabela de identificação do item (produto e serviços)
    0205 - Alteração do item da tabela de identificação do item
    0210 - Consumo específico padronizado
    0220 - Fatores de conversão de unidades
    0300 - Cadastro de bens ou componentes do imobilizado
    0305 - Informações sobre o uso do imobilizado
    0400 - Tabela de natureza da operação / prestação
    0450 - Tabela de informações complementares do documento fiscal
    0460 - Tabela de observações do lançamento fiscal
    0500 - Plano de contas contábeis
    0600 - Centro de custos
    0990 - Encerramento do Bloco 0
"""

from dataclasses import dataclass, field, fields
from typing import Optional
from datetime import date


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

@dataclass
class RegistroBase:
    """Classe base com serialização/deserialização para o formato SPED (pipe-delimited)."""

    REGISTRO: str = ""  # código do registro, ex: "0000"

    def to_sped_line(self) -> str:
        """Serializa o registro numa linha SPED: |REG|campo1|campo2|...|"""
        valores = []
        for f in fields(self):
            val = getattr(self, f.name)
            if isinstance(val, date):
                val = val.strftime("%d%m%Y")
            elif val is None:
                val = ""
            else:
                val = str(val)
            valores.append(val)
        return "|" + "|".join(valores) + "|"

    @classmethod
    def from_sped_line(cls, linha: str):
        """Desserializa uma linha SPED para uma instância do registro."""
        partes = linha.strip().strip("|").split("|")
        nomes = [f.name for f in fields(cls)]
        kwargs = {}
        for i, nome in enumerate(nomes):
            kwargs[nome] = partes[i] if i < len(partes) else ""
        return cls(**kwargs)

    def validar(self) -> list[str]:
        """Retorna lista de erros de validação. Subclasses sobrescrevem."""
        return []


# ---------------------------------------------------------------------------
# Registros do Bloco 0
# ---------------------------------------------------------------------------

@dataclass
class Reg0000(RegistroBase):
    """
    0000 — Abertura do arquivo e identificação do contribuinte.
    Obrigatório. Único por arquivo.

    Campos principais:
        COD_VER   : Código da versão do leiaute (019)
        COD_FIN   : Código de finalidade do arquivo (0=Original, 1=Substituto)
        DT_INI    : Data inicial das informações (DDMMAAAA)
        DT_FIN    : Data final das informações (DDMMAAAA)
        NOME      : Nome empresarial do contribuinte
        CNPJ      : CNPJ do contribuinte
        CPF       : CPF do contribuinte (PF)
        UF        : Sigla da UF do contribuinte
        IE        : Inscrição Estadual do contribuinte
        COD_MUN   : Código do município (IBGE)
        IM        : Inscrição Municipal do contribuinte
        SUFRAMA   : Inscrição na SUFRAMA
        IND_PERFIL: Perfil de apresentação do arquivo (A, B ou C)
        IND_ATIV  : Indicador de atividade (0=Industrial/equiparado, 1=Outros)
    """
    REGISTRO:   str = "0000"
    COD_VER:    str = "019"
    COD_FIN:    str = "0"
    DT_INI:     str = ""
    DT_FIN:     str = ""
    NOME:       str = ""
    CNPJ:       str = ""
    CPF:        str = ""
    UF:         str = ""
    IE:         str = ""
    COD_MUN:    str = ""
    IM:         str = ""
    SUFRAMA:    str = ""
    IND_PERFIL: str = "A"
    IND_ATIV:   str = "0"

    def validar(self) -> list[str]:
        erros = []
        if self.COD_VER not in ("017", "018", "019"):
            erros.append(f"0000.COD_VER inválido: '{self.COD_VER}'. Esperado 017/018/019.")
        if self.COD_FIN not in ("0", "1"):
            erros.append(f"0000.COD_FIN inválido: '{self.COD_FIN}'. Use 0=Original ou 1=Substituto.")
        if not self.DT_INI or len(self.DT_INI) != 8:
            erros.append("0000.DT_INI obrigatório e deve ter 8 dígitos (DDMMAAAA).")
        if not self.DT_FIN or len(self.DT_FIN) != 8:
            erros.append("0000.DT_FIN obrigatório e deve ter 8 dígitos (DDMMAAAA).")
        if not self.NOME:
            erros.append("0000.NOME é obrigatório.")
        if not self.CNPJ and not self.CPF:
            erros.append("0000: CNPJ ou CPF é obrigatório.")
        if self.CNPJ and len(self.CNPJ) != 14:
            erros.append(f"0000.CNPJ deve ter 14 dígitos (sem máscara). Recebido: '{self.CNPJ}'.")
        if not self.UF or len(self.UF) != 2:
            erros.append("0000.UF obrigatório e deve ter 2 caracteres.")
        if self.IND_PERFIL not in ("A", "B", "C"):
            erros.append(f"0000.IND_PERFIL inválido: '{self.IND_PERFIL}'. Use A, B ou C.")
        if self.IND_ATIV not in ("0", "1"):
            erros.append(f"0000.IND_ATIV inválido: '{self.IND_ATIV}'. Use 0 ou 1.")
        return erros


@dataclass
class Reg0001(RegistroBase):
    """0001 — Abertura do Bloco 0. IND_MOV: 0=com dados, 1=sem dados."""
    REGISTRO: str = "0001"
    IND_MOV:  str = "0"

    def validar(self) -> list[str]:
        if self.IND_MOV not in ("0", "1"):
            return [f"0001.IND_MOV inválido: '{self.IND_MOV}'. Use 0 ou 1."]
        return []


@dataclass
class Reg0005(RegistroBase):
    """0005 — Dados complementares do contribuinte."""
    REGISTRO:  str = "0005"
    FANTASIA:  str = ""
    CEP:       str = ""
    END:       str = ""
    NUM:       str = ""
    COMPL:     str = ""
    BAIRRO:    str = ""
    FONE:      str = ""
    FAX:       str = ""
    EMAIL:     str = ""
    COD_MUN:   str = ""


@dataclass
class Reg0100(RegistroBase):
    """0100 — Dados do contabilista."""
    REGISTRO:  str = "0100"
    NOME:      str = ""
    CPF:       str = ""
    CRC:       str = ""
    CNPJ:      str = ""
    CEP:       str = ""
    END:       str = ""
    NUM:       str = ""
    COMPL:     str = ""
    BAIRRO:    str = ""
    FONE:      str = ""
    FAX:       str = ""
    EMAIL:     str = ""
    COD_MUN:   str = ""


@dataclass
class Reg0150(RegistroBase):
    """
    0150 — Tabela de cadastro do participante (cliente/fornecedor).
    Cada NF-e referenciada no Bloco C precisa ter seu participante aqui.
    """
    REGISTRO: str = "0150"
    COD_PART: str = ""   # Código interno do participante (chave)
    NOME:     str = ""
    COD_PAIS: str = "1058"  # 1058 = Brasil
    CNPJ:     str = ""
    CPF:      str = ""
    IE:       str = ""
    COD_MUN:  str = ""
    SUFRAMA:  str = ""
    END:      str = ""
    NUM:      str = ""
    COMPL:    str = ""
    BAIRRO:   str = ""

    def validar(self) -> list[str]:
        erros = []
        if not self.COD_PART:
            erros.append("0150.COD_PART é obrigatório.")
        if not self.NOME:
            erros.append("0150.NOME é obrigatório.")
        if not self.CNPJ and not self.CPF:
            erros.append(f"0150 ({self.COD_PART}): CNPJ ou CPF é obrigatório.")
        return erros


@dataclass
class Reg0190(RegistroBase):
    """0190 — Identificação das unidades de medida usadas nos itens."""
    REGISTRO: str = "0190"
    UNID:     str = ""   # Ex: UN, KG, LT, MT, M2, CX
    DESCR:    str = ""

    def validar(self) -> list[str]:
        if not self.UNID:
            return ["0190.UNID é obrigatório."]
        return []


@dataclass
class Reg0200(RegistroBase):
    """
    0200 — Tabela de identificação do item (produto ou serviço).
    Todo item referenciado nos demais blocos deve estar aqui.
    """
    REGISTRO:  str = "0200"
    COD_ITEM:  str = ""   # Código interno do item (chave)
    DESCR_ITEM:str = ""
    COD_BARRA: str = ""   # GTIN/EAN
    COD_ANT_ITEM: str = ""
    UNID_INV:  str = ""   # Unidade de inventário (deve existir no 0190)
    TIPO_ITEM: str = ""   # 00=Merc. p/ revenda, 01=MP, 02=Embalagem, ...
    COD_NCM:   str = ""   # NCM (8 dígitos)
    EX_IPI:    str = ""   # Exceção IPI da TIPI
    COD_GEN:   str = ""   # Código de gênero (2 dígitos do NCM)
    COD_LST:   str = ""   # Código da lista de serviços (ISS)
    ALIQ_ICMS: str = ""   # Alíquota ICMS

    TIPOS_ITEM_VALIDOS = {
        "00": "Mercadoria para revenda",
        "01": "Matéria-prima",
        "02": "Embalagem",
        "03": "Produto em processo",
        "04": "Produto acabado",
        "05": "Subproduto",
        "06": "Produto intermediário",
        "07": "Material de uso e consumo",
        "08": "Ativo imobilizado",
        "09": "Serviços",
        "10": "Outros insumos",
        "99": "Outras",
    }

    def validar(self) -> list[str]:
        erros = []
        if not self.COD_ITEM:
            erros.append("0200.COD_ITEM é obrigatório.")
        if not self.DESCR_ITEM:
            erros.append(f"0200 ({self.COD_ITEM}): DESCR_ITEM é obrigatório.")
        if self.TIPO_ITEM and self.TIPO_ITEM not in self.TIPOS_ITEM_VALIDOS:
            erros.append(f"0200 ({self.COD_ITEM}): TIPO_ITEM '{self.TIPO_ITEM}' inválido.")
        if self.COD_NCM and len(self.COD_NCM) != 8:
            erros.append(f"0200 ({self.COD_ITEM}): COD_NCM deve ter 8 dígitos. Recebido: '{self.COD_NCM}'.")
        return erros


@dataclass
class Reg0400(RegistroBase):
    """0400 — Tabela de natureza da operação / prestação (CFOP + descrição)."""
    REGISTRO:  str = "0400"
    COD_NAT:   str = ""   # Código da natureza (livre, ex: "VENDA")
    DESCR_NAT: str = ""

    def validar(self) -> list[str]:
        if not self.COD_NAT:
            return ["0400.COD_NAT é obrigatório."]
        return []


@dataclass
class Reg0450(RegistroBase):
    """0450 — Tabela de informações complementares do documento fiscal."""
    REGISTRO: str = "0450"
    COD_INF:  str = ""
    TXT:      str = ""


@dataclass
class Reg0990(RegistroBase):
    """0990 — Encerramento do Bloco 0. QTD_LIN_0: total de linhas do bloco."""
    REGISTRO:   str = "0990"
    QTD_LIN_0:  str = "0"
