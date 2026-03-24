"""
Bloco0 — Classe principal que agrupa todos os registros do Bloco 0,
oferece geração (to_lines) e leitura (from_lines / from_file).
"""

from __future__ import annotations
from typing import Optional
from .registros import (
    Reg0000, Reg0001, Reg0005, Reg0100,
    Reg0150, Reg0190, Reg0200, Reg0400, Reg0450, Reg0990,
)

# Mapa: código de registro → classe correspondente
_REGISTRO_MAP: dict[str, type] = {
    "0000": Reg0000,
    "0001": Reg0001,
    "0005": Reg0005,
    "0100": Reg0100,
    "0150": Reg0150,
    "0190": Reg0190,
    "0200": Reg0200,
    "0400": Reg0400,
    "0450": Reg0450,
    "0990": Reg0990,
}


class Bloco0:
    """
    Representa o Bloco 0 completo do arquivo EFD ICMS/IPI.

    Uso — geração:
        bloco = Bloco0()
        bloco.registro_0000 = Reg0000(DT_INI="01012024", ...)
        bloco.adicionar_participante(Reg0150(COD_PART="CLI001", ...))
        bloco.adicionar_item(Reg0200(COD_ITEM="PROD001", ...))
        linhas = bloco.to_lines()

    Uso — leitura:
        bloco = Bloco0.from_file("sped_fiscal.txt")
        print(bloco.registro_0000.NOME)
        for part in bloco.participantes:
            print(part.COD_PART, part.NOME)
    """

    def __init__(self):
        # Registros únicos
        self.registro_0000: Optional[Reg0000] = None
        self.registro_0001: Optional[Reg0001] = Reg0001()
        self.registro_0005: Optional[Reg0005] = None
        self.registro_0100: Optional[Reg0100] = None
        self.registro_0990: Optional[Reg0990] = Reg0990()

        # Registros múltiplos (listas)
        self.participantes:     list[Reg0150] = []   # 0150
        self.unidades:          list[Reg0190] = []   # 0190
        self.itens:             list[Reg0200] = []   # 0200
        self.naturezas:         list[Reg0400] = []   # 0400
        self.inf_complementares:list[Reg0450] = []   # 0450

        # Índices para lookup rápido
        self._idx_participantes: dict[str, Reg0150] = {}
        self._idx_itens:         dict[str, Reg0200] = {}
        self._idx_unidades:      dict[str, Reg0190] = {}

    # ------------------------------------------------------------------
    # Métodos de adição
    # ------------------------------------------------------------------

    def adicionar_participante(self, reg: Reg0150) -> None:
        self.participantes.append(reg)
        self._idx_participantes[reg.COD_PART] = reg

    def adicionar_unidade(self, reg: Reg0190) -> None:
        self.unidades.append(reg)
        self._idx_unidades[reg.UNID] = reg

    def adicionar_item(self, reg: Reg0200) -> None:
        self.itens.append(reg)
        self._idx_itens[reg.COD_ITEM] = reg

    def adicionar_natureza(self, reg: Reg0400) -> None:
        self.naturezas.append(reg)

    def adicionar_inf_complementar(self, reg: Reg0450) -> None:
        self.inf_complementares.append(reg)

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def buscar_participante(self, cod_part: str) -> Optional[Reg0150]:
        return self._idx_participantes.get(cod_part)

    def buscar_item(self, cod_item: str) -> Optional[Reg0200]:
        return self._idx_itens.get(cod_item)

    def buscar_unidade(self, unid: str) -> Optional[Reg0190]:
        return self._idx_unidades.get(unid)

    # ------------------------------------------------------------------
    # Geração (to_lines)
    # ------------------------------------------------------------------

    def to_lines(self) -> list[str]:
        """
        Gera a lista de linhas do Bloco 0 na ordem obrigatória do leiaute.
        Atualiza automaticamente o QTD_LIN_0 no registro 0990.
        """
        if not self.registro_0000:
            raise ValueError("Registro 0000 é obrigatório para gerar o Bloco 0.")

        linhas: list[str] = []

        # 0000 — Sempre primeiro
        linhas.append(self.registro_0000.to_sped_line())

        # 0001 — Abertura do bloco
        linhas.append(self.registro_0001.to_sped_line())

        # 0005 — Dados complementares (opcional)
        if self.registro_0005:
            linhas.append(self.registro_0005.to_sped_line())

        # 0100 — Contabilista (opcional)
        if self.registro_0100:
            linhas.append(self.registro_0100.to_sped_line())

        # 0150 — Participantes
        for p in self.participantes:
            linhas.append(p.to_sped_line())

        # 0190 — Unidades de medida
        for u in self.unidades:
            linhas.append(u.to_sped_line())

        # 0200 — Itens
        for i in self.itens:
            linhas.append(i.to_sped_line())

        # 0400 — Naturezas de operação
        for n in self.naturezas:
            linhas.append(n.to_sped_line())

        # 0450 — Informações complementares
        for inf in self.inf_complementares:
            linhas.append(inf.to_sped_line())

        # 0990 — Encerramento: total de linhas INCLUINDO o próprio 0990
        total = len(linhas) + 1
        self.registro_0990.QTD_LIN_0 = str(total)
        linhas.append(self.registro_0990.to_sped_line())

        return linhas

    def to_text(self) -> str:
        """Retorna o bloco completo como string com quebras de linha."""
        return "\r\n".join(self.to_lines()) + "\r\n"

    # ------------------------------------------------------------------
    # Leitura (from_lines / from_file)
    # ------------------------------------------------------------------

    @classmethod
    def from_lines(cls, linhas: list[str]) -> "Bloco0":
        """
        Parseia uma lista de linhas do arquivo SPED e retorna um Bloco0.
        Aceita linhas de qualquer bloco — ignora as que não são do Bloco 0.
        """
        bloco = cls()

        for linha in linhas:
            linha = linha.strip()
            if not linha or not linha.startswith("|"):
                continue

            partes = linha.strip("|").split("|")
            codigo = partes[0] if partes else ""

            if codigo not in _REGISTRO_MAP:
                continue

            cls_reg = _REGISTRO_MAP[codigo]
            reg = cls_reg.from_sped_line(linha)

            if codigo == "0000":
                bloco.registro_0000 = reg
            elif codigo == "0001":
                bloco.registro_0001 = reg
            elif codigo == "0005":
                bloco.registro_0005 = reg
            elif codigo == "0100":
                bloco.registro_0100 = reg
            elif codigo == "0150":
                bloco.adicionar_participante(reg)
            elif codigo == "0190":
                bloco.adicionar_unidade(reg)
            elif codigo == "0200":
                bloco.adicionar_item(reg)
            elif codigo == "0400":
                bloco.adicionar_natureza(reg)
            elif codigo == "0450":
                bloco.adicionar_inf_complementar(reg)
            elif codigo == "0990":
                bloco.registro_0990 = reg

        return bloco

    @classmethod
    def from_file(cls, caminho: str, encoding: str = "latin-1") -> "Bloco0":
        """Lê um arquivo .txt EFD e retorna o Bloco0 parseado."""
        with open(caminho, encoding=encoding) as f:
            linhas = f.readlines()
        return cls.from_lines(linhas)

    # ------------------------------------------------------------------
    # Validação
    # ------------------------------------------------------------------

    def validar(self) -> list[str]:
        """
        Executa todas as validações do Bloco 0 e retorna lista de erros.
        Inclui validações estruturais (registros obrigatórios) e
        validações de cada registro individualmente.
        """
        erros: list[str] = []

        # Registros obrigatórios
        if not self.registro_0000:
            erros.append("Registro 0000 ausente — é obrigatório.")
            return erros  # sem ele não dá para continuar

        # Validações individuais dos registros únicos
        for reg in [self.registro_0000, self.registro_0001,
                    self.registro_0005, self.registro_0100]:
            if reg:
                erros.extend(reg.validar())

        # Validações dos registros múltiplos
        for reg in self.participantes + self.unidades + self.itens + self.naturezas:
            erros.extend(reg.validar())

        # Validações cruzadas
        erros.extend(self._validar_cruzamentos())

        return erros

    def _validar_cruzamentos(self) -> list[str]:
        """Validações de integridade referencial entre registros."""
        erros = []
        unidades_cadastradas = {u.UNID for u in self.unidades}

        for item in self.itens:
            if item.UNID_INV and item.UNID_INV not in unidades_cadastradas:
                erros.append(
                    f"0200 ({item.COD_ITEM}): UNID_INV '{item.UNID_INV}' "
                    f"não encontrada no registro 0190."
                )
        return erros

    # ------------------------------------------------------------------
    # Resumo
    # ------------------------------------------------------------------

    def resumo(self) -> str:
        """Exibe um resumo legível do Bloco 0."""
        linhas = ["=" * 55, "  RESUMO — BLOCO 0", "=" * 55]

        if self.registro_0000:
            r = self.registro_0000
            linhas += [
                f"  Empresa   : {r.NOME}",
                f"  CNPJ      : {r.CNPJ}",
                f"  UF        : {r.UF}",
                f"  Período   : {r.DT_INI} a {r.DT_FIN}",
                f"  Leiaute   : {r.COD_VER}",
                f"  Perfil    : {r.IND_PERFIL}",
                f"  Finalidade: {'Original' if r.COD_FIN == '0' else 'Substituto'}",
            ]

        linhas += [
            "-" * 55,
            f"  Participantes (0150): {len(self.participantes)}",
            f"  Unidades      (0190): {len(self.unidades)}",
            f"  Itens         (0200): {len(self.itens)}",
            f"  Naturezas     (0400): {len(self.naturezas)}",
            "=" * 55,
        ]

        erros = self.validar()
        if erros:
            linhas.append(f"  ⚠ {len(erros)} erro(s) de validação:")
            for e in erros:
                linhas.append(f"    • {e}")
        else:
            linhas.append("  ✓ Nenhum erro de validação encontrado.")

        linhas.append("=" * 55)
        return "\n".join(linhas)
