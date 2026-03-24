"""
preview.py — Visualização e detecção de encoding de arquivos EFD ICMS/IPI

Uso rápido:
    from sped_fiscal.preview import preview_arquivo
    preview_arquivo("sped_janeiro_2024.txt")
"""

from __future__ import annotations
import os

# Descrições legíveis dos registros do Bloco 0
_DESCRICAO_REGISTRO = {
    "0000": "Abertura e identificação do contribuinte",
    "0001": "Abertura do Bloco 0",
    "0005": "Dados complementares do contribuinte",
    "0015": "Dados do contribuinte substituto",
    "0100": "Dados do contabilista",
    "0150": "Participante (cliente/fornecedor)",
    "0175": "Alteração de participante",
    "0190": "Unidade de medida",
    "0200": "Item (produto/serviço)",
    "0205": "Alteração de item",
    "0210": "Consumo específico padronizado",
    "0220": "Fator de conversão de unidade",
    "0300": "Bem do imobilizado",
    "0400": "Natureza da operação",
    "0450": "Informação complementar",
    "0460": "Observação de lançamento",
    "0500": "Plano de contas contábeis",
    "0600": "Centro de custos",
    "0990": "Encerramento do Bloco 0",
    # Outros blocos (identificação rápida)
    "C001": "Abertura Bloco C (documentos ICMS)",
    "C100": "NF-e / NFC-e",
    "C170": "Item da NF-e",
    "C190": "Registro analítico NF-e",
    "C990": "Encerramento Bloco C",
    "D001": "Abertura Bloco D (transporte)",
    "D990": "Encerramento Bloco D",
    "E001": "Abertura Bloco E (apuração)",
    "E110": "Apuração do ICMS",
    "E990": "Encerramento Bloco E",
    "H001": "Abertura Bloco H (inventário)",
    "H010": "Inventário físico — item",
    "H990": "Encerramento Bloco H",
    "K001": "Abertura Bloco K (produção/estoque)",
    "K990": "Encerramento Bloco K",
    "9001": "Abertura Bloco 9",
    "9999": "Encerramento do arquivo",
}


# ---------------------------------------------------------------------------
# Detecção de encoding
# ---------------------------------------------------------------------------

def detectar_encoding(caminho: str) -> str:
    """
    Testa os encodings mais comuns em arquivos SPED brasileiros
    e retorna o primeiro que conseguir ler o arquivo sem erros.
    """
    candidatos = ["latin-1", "utf-8", "cp1252", "utf-8-sig"]
    for enc in candidatos:
        try:
            with open(caminho, encoding=enc) as f:
                f.read()
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    return "latin-1"  # fallback


# ---------------------------------------------------------------------------
# Preview principal
# ---------------------------------------------------------------------------

def preview_arquivo(
    caminho: str,
    max_linhas_raw: int = 5,
    encoding: str | None = None,
) -> None:
    """
    Exibe um preview completo do arquivo EFD antes do parse.

    Mostra:
      - Metadados do arquivo (tamanho, encoding detectado)
      - Primeiras linhas brutas do arquivo
      - Contagem de registros por tipo (todos os blocos)
      - Resumo dos dados do Bloco 0 (empresa, período, totais)

    Args:
        caminho       : Caminho para o arquivo .txt EFD
        max_linhas_raw: Quantas linhas brutas exibir no preview
        encoding      : Forçar encoding (se None, detecta automaticamente)
    """
    if not os.path.exists(caminho):
        print(f"  ✗  Arquivo não encontrado: {caminho}")
        return

    # --- Metadados do arquivo ---
    tamanho_bytes = os.path.getsize(caminho)
    enc_detectado = encoding or detectar_encoding(caminho)

    with open(caminho, encoding=enc_detectado, errors="replace") as f:
        todas_linhas = f.readlines()

    total_linhas = len(todas_linhas)
    tamanho_fmt = (
        f"{tamanho_bytes / 1024:.1f} KB"
        if tamanho_bytes < 1_048_576
        else f"{tamanho_bytes / 1_048_576:.2f} MB"
    )

    sep = "─" * 58

    # =======================================================================
    # Cabeçalho
    # =======================================================================
    print(f"\n╔{'═'*58}╗")
    print(f"║  PREVIEW — ARQUIVO EFD ICMS/IPI{' '*25}║")
    print(f"╠{'═'*58}╣")
    print(f"║  Arquivo  : {os.path.basename(caminho):<45}║")
    print(f"║  Tamanho  : {tamanho_fmt:<45}║")
    print(f"║  Encoding : {enc_detectado:<45}║")
    print(f"║  Linhas   : {total_linhas:<45}║")
    print(f"╚{'═'*58}╝")

    # =======================================================================
    # Linhas brutas
    # =======================================================================
    print(f"\n  {'─'*56}")
    print(f"  PRIMEIRAS {max_linhas_raw} LINHAS (formato bruto)")
    print(f"  {'─'*56}")
    for i, linha in enumerate(todas_linhas[:max_linhas_raw]):
        print(f"  [{i+1:>2}]  {linha.rstrip()}")
    if total_linhas > max_linhas_raw:
        print(f"         ... ({total_linhas - max_linhas_raw} linhas restantes)")

    # =======================================================================
    # Contagem de registros por tipo
    # =======================================================================
    contagem: dict[str, int] = {}
    bloco_atual = "?"

    for linha in todas_linhas:
        linha = linha.strip()
        if not linha or not linha.startswith("|"):
            continue
        partes = linha.strip("|").split("|")
        if not partes:
            continue
        cod = partes[0]
        contagem[cod] = contagem.get(cod, 0) + 1

        # rastreia bloco para agrupamento
        if len(cod) == 4 and cod[1:] in ("000", "001"):
            bloco_atual = cod[0]

    print(f"\n  {'─'*56}")
    print(f"  REGISTROS ENCONTRADOS NO ARQUIVO")
    print(f"  {'─'*56}")

    bloco_anterior = None
    for cod in sorted(contagem.keys()):
        bloco = cod[0] if cod else "?"
        if bloco != bloco_anterior:
            print(f"\n  [ Bloco {bloco} ]")
            bloco_anterior = bloco
        descricao = _DESCRICAO_REGISTRO.get(cod, "Registro")
        qtd = contagem[cod]
        barra = "█" * min(qtd, 30) + ("+" if qtd > 30 else "")
        print(f"    {cod}  {qtd:>5}x  {barra}  {descricao}")

    # =======================================================================
    # Resumo do Bloco 0
    # =======================================================================
    print(f"\n  {'─'*56}")
    print(f"  RESUMO — BLOCO 0")
    print(f"  {'─'*56}")

    info: dict[str, str] = {}
    for linha in todas_linhas:
        linha = linha.strip().strip("|")
        partes = linha.split("|")
        cod = partes[0] if partes else ""

        if cod == "0000" and len(partes) >= 15:
            info["leiaute"]    = partes[1]
            info["finalidade"] = "Original" if partes[2] == "0" else "Substituto"
            info["dt_ini"]     = _formatar_data(partes[3])
            info["dt_fin"]     = _formatar_data(partes[4])
            info["empresa"]    = partes[5]
            info["cnpj"]       = _formatar_cnpj(partes[6])
            info["uf"]         = partes[8]
            info["ie"]         = partes[9]
            info["perfil"]     = partes[13]

        elif cod == "0005" and len(partes) >= 2:
            info["fantasia"] = partes[1]

    if info:
        print(f"  Empresa    : {info.get('empresa', '-')}")
        if info.get("fantasia"):
            print(f"  Fantasia   : {info['fantasia']}")
        print(f"  CNPJ       : {info.get('cnpj', '-')}")
        print(f"  UF / IE    : {info.get('uf', '-')} / {info.get('ie', '-')}")
        print(f"  Período    : {info.get('dt_ini', '-')} a {info.get('dt_fin', '-')}")
        print(f"  Leiaute    : {info.get('leiaute', '-')}")
        print(f"  Perfil     : {info.get('perfil', '-')}")
        print(f"  Finalidade : {info.get('finalidade', '-')}")

    print(f"\n  {'─'*56}")
    print(f"  Participantes (0150): {contagem.get('0150', 0)}")
    print(f"  Unidades      (0190): {contagem.get('0190', 0)}")
    print(f"  Itens         (0200): {contagem.get('0200', 0)}")
    nf = contagem.get('C100', 0)
    if nf:
        print(f"  NF-e/NFC-e   (C100): {nf}")
    print(f"  {'─'*56}\n")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _formatar_data(d: str) -> str:
    """DDMMAAAA → DD/MM/AAAA"""
    if len(d) == 8:
        return f"{d[0:2]}/{d[2:4]}/{d[4:8]}"
    return d


def _formatar_cnpj(c: str) -> str:
    """14 dígitos → XX.XXX.XXX/XXXX-XX"""
    c = c.zfill(14)
    if len(c) == 14:
        return f"{c[0:2]}.{c[2:5]}.{c[5:8]}/{c[8:12]}-{c[12:14]}"
    return c
