"""Modelo independente para estudar redistribuição de EVs; NÃO modifica ROM/saves.

O jogo atribui os EVs ao vencer batalhas. Este rascunho permite transferir
somente EVs já conquistados, sem criar pontos. A integração com a ROM é trabalho
separado e precisa preservar seus próprios limites e os Pokémon existentes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

ESTATISTICAS = ("hp", "ataque", "defesa", "ataque_especial", "defesa_especial", "velocidade")
MAXIMO_POR_ATRIBUTO = 255
MAXIMO_TOTAL = 510
PASSOS = (1, 4)


def _validar_evs(valores: Sequence[int]) -> tuple[int, ...]:
    valores = tuple(valores)
    if len(valores) != len(ESTATISTICAS):
        raise ValueError("São necessários exatamente seis valores de EV.")
    if any(type(x) is not int or not 0 <= x <= MAXIMO_POR_ATRIBUTO for x in valores):
        raise ValueError("Cada EV deve ser inteiro entre 0 e 255.")
    if sum(valores) > MAXIMO_TOTAL:
        raise ValueError("O total de EVs excede 510; não modificar dados inválidos.")
    return valores


@dataclass
class RascunhoTreino:
    """Transferência conservadora que só confirma se nenhum ponto foi perdido."""

    inicial: Sequence[int]
    _original: tuple[int, ...] = field(init=False, repr=False)
    _atual: list[int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._original = _validar_evs(self.inicial)
        self._atual = list(self._original)
        # Não manter referência mutável aos dados fornecidos pelo chamador.
        self.inicial = self._original

    @property
    def valores(self) -> tuple[int, ...]:
        return tuple(self._atual)

    @property
    def disponivel(self) -> int:
        return sum(self._original) - sum(self._atual)

    @staticmethod
    def _validar_operacao(atributo: int, passo: int) -> None:
        if type(atributo) is not int or not 0 <= atributo < len(ESTATISTICAS):
            raise ValueError("Atributo inválido.")
        if type(passo) is not int or passo not in PASSOS:
            raise ValueError("O passo deve ser 1 ou 4.")

    def retirar(self, atributo: int, passo: int = 1) -> int:
        """Retira até `passo` EVs do atributo para o saldo temporário."""
        self._validar_operacao(atributo, passo)
        quantidade = min(passo, self._atual[atributo])
        self._atual[atributo] -= quantidade
        return quantidade

    def atribuir(self, atributo: int, passo: int = 1) -> int:
        """Usa somente o saldo já retirado, respeitando o limite do atributo."""
        self._validar_operacao(atributo, passo)
        quantidade = min(passo, self.disponivel, MAXIMO_POR_ATRIBUTO - self._atual[atributo])
        self._atual[atributo] += quantidade
        return quantidade

    def confirmar(self) -> tuple[int, ...]:
        """Confirma apenas uma distribuição válida sem saldo perdido."""
        if self.disponivel:
            raise ValueError("Redistribua todos os pontos ou cancele o treino.")
        valores = _validar_evs(self._atual)
        if sum(valores) != sum(self._original):
            raise ValueError("O total de EVs não pode mudar na redistribuição.")
        return valores

    def cancelar(self) -> tuple[int, ...]:
        """Descarta o rascunho, sem tocar no Pokémon original."""
        self._atual = list(self._original)
        return self._original


if __name__ == "__main__":
    # Exemplo sintético: transferir quatro EVs de ataque para velocidade.
    treino = RascunhoTreino((0, 20, 0, 0, 0, 0))
    treino.retirar(1, 4)
    treino.atribuir(5, 4)
    print("Exemplo, antes:", treino.inicial, "depois:", treino.confirmar())
    print("Simulação apenas: nenhuma ROM ou save foi modificado.")
