# -*- coding: utf-8 -*-
"""Corrige caracteres corrompidos (U+FFFD) no views.py."""
import re

path = "polls/views.py"
content = open(path, encoding="utf-8").read()

R = "\ufffd"

# Duplos: -ção endings (ç + ã corrompidos = dois \ufffd antes do 'o')
double_fixes = [
    (f"importa{R}{R}o", "importacao"),
    (f"Importa{R}{R}o", "Importacao"),
    (f"indenta{R}{R}o", "indentacao"),
    (f"Implementa{R}{R}o", "Implementacao"),
    (f"edi{R}{R}o", "edicao"),
    (f"requisi{R}{R}o", "requisicao"),
    (f"Requisi{R}{R}o", "Requisicao"),
    (f"lota{R}{R}o", "lotacao"),
    (f"capitaliza{R}{R}o", "capitalizacao"),
    (f"preserva{R}{R}o", "preservacao"),
    (f"classifica{R}{R}o", "classificacao"),
    (f"Atualiza{R}{R}o", "Atualizacao"),
    (f"informa{R}{R}o", "informacao"),
    (f"Informa{R}{R}o", "Informacao"),
]

# Simples: palavras com um único acento corrompido
single_fixes = [
    (f"mem{R}ria", "memoria"),
    (f"Mem{R}ria", "Memoria"),
    (f"CL{R}NICAS", "CLINICAS"),
    (f"cl{R}nicas", "clinicas"),
    (f"Cl{R}nicas", "Clinicas"),
    (f"cl{R}nica", "clinica"),
    (f"Cl{R}nica", "Clinica"),
    (f"c{R}digos", "codigos"),
    (f"C{R}digos", "Codigos"),
    (f"munic{R}pio", "municipio"),
    (f"Munic{R}pio", "Municipio"),
    (f"endere{R}o", "endereco"),
    (f"espa{R}amento", "espacamento"),
    (f"espa{R}os", "espacos"),
    (f"espa{R}o", "espaco"),
    (f"mai{R}sculas", "maiusculas"),
    (f"mai{R}scula", "maiuscula"),
    (f"min{R}sculas", "minusculas"),
    (f"min{R}sculo", "minusculo"),
    (f"m{R}nimo", "minimo"),
    (f"M{R}nimo", "Minimo"),
    (f"m{R}nima", "minima"),
    (f"exclu{R}do", "excluido"),
    (f"exclu{R}da", "excluida"),
    (f"Exclu{R}do", "Excluido"),
    (f"exclu{R}dos", "excluidos"),
    (f"padr{R}o", "padrao"),
    (f"Padr{R}o", "Padrao"),
    (f"obrigat{R}rios", "obrigatorios"),
    (f"obrigat{R}rias", "obrigatorias"),
    (f"M{R}todo", "Metodo"),
    (f"m{R}todo", "metodo"),
    (f"inv{R}lido", "invalido"),
    (f"Inv{R}lido", "Invalido"),
    (f"v{R}lido", "valido"),
    (f"V{R}lido", "Valido"),
    (f"Sequ{R}ncia", "Sequencia"),
    (f"sequ{R}ncia", "sequencia"),
    (f"gen{R}rico", "generico"),
    (f"Gen{R}rico", "Generico"),
    (f"pr{R}via", "previa"),
    (f"Pr{R}via", "Previa"),
    (f"VE{R}CULO", "VEICULO"),
    (f"ve{R}culo", "veiculo"),
    (f"Ve{R}culo", "Veiculo"),
    (f"p{R}gina", "pagina"),
    (f"P{R}gina", "Pagina"),
    (f"pol{R}tica", "politica"),
    (f"Pol{R}tica", "Politica"),
    (f"poss{R}vel", "possivel"),
    (f"Poss{R}vel", "Possivel"),
    (f"C{R}lculo", "Calculo"),
    (f"c{R}lculo", "calculo"),
    (f"AMBUL{R}NCIAS", "AMBULANCIAS"),
    (f"ambul{R}ncias", "ambulancias"),
    (f"ESTAT{R}STICA", "ESTATISTICA"),
    (f"PER{R}ODO", "PERIODO"),
    (f"Per{R}odo", "Periodo"),
    (f"per{R}odo", "periodo"),
    (f"Transfer{R}ncias", "Transferencias"),
    (f"transfer{R}ncias", "transferencias"),
    (f"Transfer{R}ncia", "Transferencia"),
    (f"transfer{R}ncia", "transferencia"),
    (f"sugest{R}es", "sugestoes"),
    (f"Sugest{R}es", "Sugestoes"),
    (f"m{R}s", "mes"),
    (f"M{R}s", "Mes"),
    (f"vari{R}veis", "variaveis"),
    (f"Vari{R}veis", "Variaveis"),
    (f"patrim{R}nio", "patrimonio"),
    (f"Patrim{R}nio", "Patrimonio"),
    (f"{R}nicas", "unicas"),
    (f"{R}nica", "unica"),
    (f"{R}nico", "unico"),
    (f"{R}ltimo", "ultimo"),
    (f"{R}ltima", "ultima"),
]

# Palavras curtas (substituir com cuidado usando contexto)
short_fixes = [
    (f"est{R} ", "esta "),
    (f"Est{R} ", "Esta "),
    (f"est{R}\n", "esta\n"),
    (f"n{R}o ", "nao "),
    (f"N{R}o ", "Nao "),
    (f"N{R}O ", "NAO "),
    (f"n{R}o\n", "nao\n"),
    (f'n{R}o"', 'nao"'),
    (f"n{R}o.", "nao."),
    (f"n{R}o,", "nao,"),
    (f"n{R}o!", "nao!"),
    (f"n{R}o:", "nao:"),
    (f"j{R} ", "ja "),
    (f"j{R}\n", "ja\n"),
    (f"j{R}.", "ja."),
    (f"j{R},", "ja,"),
    (f"j{R};", "ja;"),
    (f's{R} ', "so "),
    (f's{R}\n', "so\n"),
]

result = content
total = 0

for wrong, correct in double_fixes + single_fixes + short_fixes:
    n = result.count(wrong)
    if n:
        result = result.replace(wrong, correct)
        total += n

remaining = result.count(R)
open(path, "w", encoding="utf-8").write(result)
print(f"Corrigidos: {total} | Restantes: {remaining}")
