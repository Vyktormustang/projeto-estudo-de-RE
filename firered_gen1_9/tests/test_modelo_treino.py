import random
import unittest

from scripts.modelo_treino import MAXIMO_TOTAL, RascunhoTreino


class ModeloTreinoTests(unittest.TestCase):
    def test_sem_pontos_nao_adiciona_evs(self):
        treino = RascunhoTreino((0, 0, 0, 0, 0, 0))
        self.assertEqual(treino.atribuir(1, 4), 0)
        self.assertEqual(treino.confirmar(), (0, 0, 0, 0, 0, 0))

    def test_transferir_ev_nao_altera_total(self):
        treino = RascunhoTreino((20, 0, 0, 0, 0, 0))
        self.assertEqual(treino.retirar(0, 4), 4)
        self.assertEqual(treino.disponivel, 4)
        self.assertEqual(treino.atribuir(5, 4), 4)
        self.assertEqual(treino.confirmar(), (16, 0, 0, 0, 0, 4))

    def test_valores_253_a_255_da_base_sao_preservados(self):
        treino = RascunhoTreino((255, 253, 2, 0, 0, 0))
        self.assertEqual(treino.confirmar(), (255, 253, 2, 0, 0, 0))
        self.assertEqual(treino.retirar(1, 4), 4)
        self.assertEqual(treino.atribuir(0, 4), 0)
        self.assertEqual(treino.atribuir(1, 4), 4)
        self.assertEqual(treino.confirmar(), (255, 253, 2, 0, 0, 0))

    def test_passos_parciais_nao_descartam_pontos(self):
        treino = RascunhoTreino((1, 254, 0, 0, 0, 0))
        self.assertEqual(treino.retirar(0, 4), 1)
        self.assertEqual(treino.atribuir(1, 4), 1)
        self.assertEqual(treino.confirmar(), (0, 255, 0, 0, 0, 0))

    def test_limite_do_atributo_e_saldo(self):
        treino = RascunhoTreino((8, 254, 0, 0, 0, 0))
        treino.retirar(0, 4)
        self.assertEqual(treino.atribuir(1, 4), 1)
        self.assertEqual(treino.disponivel, 3)
        self.assertEqual(treino.atribuir(2, 4), 3)
        self.assertEqual(treino.confirmar(), (4, 255, 3, 0, 0, 0))

    def test_nao_confirma_saldo_pendente(self):
        treino = RascunhoTreino((8, 0, 0, 0, 0, 0))
        treino.retirar(0, 4)
        with self.assertRaises(ValueError):
            treino.confirmar()
        self.assertEqual(treino.cancelar(), (8, 0, 0, 0, 0, 0))
        self.assertEqual(treino.disponivel, 0)

    def test_entrada_externa_nao_e_modificada(self):
        entrada = [4, 2, 0, 0, 0, 0]
        treino = RascunhoTreino(entrada)
        treino.retirar(0, 4)
        treino.atribuir(2, 4)
        entrada[1] = 100
        self.assertEqual(treino.confirmar(), (0, 2, 4, 0, 0, 0))
        self.assertEqual(treino.cancelar(), (4, 2, 0, 0, 0, 0))

    def test_rejeita_valores_corrompidos(self):
        invalidos = [
            (0, 0, 0, 0, 0),
            (0, 0, 0, 0, 0, 0, 0),
            (256, 0, 0, 0, 0, 0),
            (-1, 0, 0, 0, 0, 0),
            (255, 255, 1, 0, 0, 0),
            (True, 0, 0, 0, 0, 0),
            (1.0, 0, 0, 0, 0, 0),
        ]
        for valores in invalidos:
            with self.subTest(valores=valores), self.assertRaises(ValueError):
                RascunhoTreino(valores)

    def test_rejeita_operacoes_invalidas_sem_efeito(self):
        treino = RascunhoTreino((1, 2, 3, 4, 5, 6))
        for indice, passo in [(-1, 1), (6, 1), (True, 1), (0, 0), (0, 2), (0, True)]:
            with self.subTest(indice=indice, passo=passo), self.assertRaises(ValueError):
                treino.retirar(indice, passo)
        self.assertEqual(treino.confirmar(), (1, 2, 3, 4, 5, 6))

    def test_sequencias_aleatorias_conservam_pontos_e_limites(self):
        rng = random.Random(9173)
        for _ in range(150):
            valores = [0] * 6
            for _ in range(rng.randrange(MAXIMO_TOTAL + 1)):
                opcoes = [i for i in range(6) if valores[i] < 255]
                valores[rng.choice(opcoes)] += 1
            treino = RascunhoTreino(valores)
            for _ in range(150):
                indice, passo = rng.randrange(6), rng.choice((1, 4))
                if rng.randrange(2):
                    treino.retirar(indice, passo)
                else:
                    treino.atribuir(indice, passo)
                self.assertTrue(all(0 <= n <= 255 for n in treino.valores))
                self.assertEqual(sum(treino.valores) + treino.disponivel, sum(valores))
            for indice in range(6):
                while treino.disponivel and treino.valores[indice] < 255:
                    treino.atribuir(indice, 4)
            self.assertEqual(sum(treino.confirmar()), sum(valores))


if __name__ == "__main__":
    unittest.main()
