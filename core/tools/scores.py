"""Score tools for Ecocardiografia.
Gerado pelo RAG Factory.
"""

from core.auto_scores import compute_disfuncao_diastolica, compute_tapse_classificacao, compute_gravidade_ea


def calcular_disfuncao_diastolica(e_prime_septal_baixo: bool = False, e_prime_lateral_baixo: bool = False, e_E_elevado: bool = False, tr_velocity_elevada: bool = False, lai_volume_elevado: bool = False) -> str:
    """Calcula o Disfunção Diastólica. Classificação da função diastólica do VE (ASE/EACVI)"""
    result = compute_disfuncao_diastolica(e_prime_septal_baixo=e_prime_septal_baixo, e_prime_lateral_baixo=e_prime_lateral_baixo, e_E_elevado=e_E_elevado, tr_velocity_elevada=tr_velocity_elevada, lai_volume_elevado=lai_volume_elevado)
    return f"{result['name']}: {result['score']} — {result['risk']}. {result['recommendation']}"

def calcular_tapse_classificacao(tapse_reduzido: bool = False) -> str:
    """Calcula o TAPSE. Excursão sistólica do plano do anel tricúspide"""
    result = compute_tapse_classificacao(tapse_reduzido=tapse_reduzido)
    return f"{result['name']}: {result['score']} — {result['risk']}. {result['recommendation']}"

def calcular_gravidade_ea(ava_menor_1: bool = False, grad_medio_maior_40: bool = False, vmax_maior_4: bool = False) -> str:
    """Calcula o Gravidade da Estenose Aórtica. Classificação de gravidade da estenose aórtica por parâmetros ecocardiográficos"""
    result = compute_gravidade_ea(ava_menor_1=ava_menor_1, grad_medio_maior_40=grad_medio_maior_40, vmax_maior_4=vmax_maior_4)
    return f"{result['name']}: {result['score']} — {result['risk']}. {result['recommendation']}"

