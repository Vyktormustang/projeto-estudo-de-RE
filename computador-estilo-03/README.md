# Como nasceu o computador — estilo 03

Primeira versão ilustrada e narrada de 90 s, 960×540, 24 fps. São sete ilustrações estáticas com cortes e narração em português; não há animação de personagens nem música. A narração termina antes do fim e a imagem final permanece em silêncio por alguns segundos. O termo “primeiro computador” depende dos critérios empregados; este roteiro apresenta alguns marcos, não uma linhagem causal direta.

Vídeo renderizado: https://drive.google.com/file/d/1nrwM06N7jZK99qCyEFJKzJBiiSCvp95c/view

## Recriar

Requer Python 3 com Pillow, fontes DejaVu em `/usr/share/fonts/truetype/dejavu/` e FFmpeg com libx264 e AAC. Os três arquivos MP3 da narração selecionada acompanham o projeto. Da raiz do repositório:

```sh
python3 computador-estilo-03/criar_ilustracoes.py
./computador-estilo-03/renderizar.sh
```

Se necessário, especifique o executável com `FFMPEG=/caminho/para/ffmpeg`. As imagens e o MP4 são gerados localmente e não são versionados. As durações das cenas foram calculadas para esta narração; alterações na voz ou no texto exigem ajustar os cortes.

## Referências históricas

- Computer History Museum, [The Neverending Quest for “Firsts”](https://computerhistory.org/blog/the-neverending-quest-for-firsts/): contexto sobre a diversidade de definições e pioneiros.
- Computer History Museum, [Ada Lovelace Day](https://computerhistory.org/blog/ada-lovelace-day/): notas sobre a Máquina Analítica e os números de Bernoulli.
- Computer History Museum, [Digital Machines](https://www.computerhistory.org/revolution/story/271): máquinas digitais e válvulas do ENIAC.
