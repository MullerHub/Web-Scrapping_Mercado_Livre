# Web Scraper Mercado Livre

Scraper em Python usando Playwright para abrir o Chromium e extrair produtos do Mercado Livre por nome, com filtro de condição.

## O que ele faz

- Monta a URL de busca no padrão do Mercado Livre.
- Aplica o filtro de condição `usado` quando `--condition used`.
- Itera pelos cards renderizados no browser e coleta `título`, `preço` e `url`.

## Instalação

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Uso

```bash
python scraper.py "XDJ" --condition used
```

Se quiser ver só a URL final, sem abrir o navegador:

```bash
python scraper.py "XDJ" --condition used --dry-run
```

Se quiser abrir o Chromium visível, use:

```bash
python scraper.py "XDJ" --condition used --headed
```

Para reproduzir mais de perto o caminho manual que você montou, o script usa por padrão a categoria:

```text
eletronicos-audio-video/audio/equipamento-djs
```

Se quiser mudar, passe outro caminho:

```bash
python scraper.py "XDJ" --condition used --category-path "eletronicos-audio-video/audio/equipamento-djs"
```

## Como o filtro entra na URL

O trecho importante não é o `#applied_filter...`, porque a parte depois de `#` não é enviada na requisição HTTP. O que realmente controla o resultado é a rota:

```text
/eletronicos-audio-video/audio/equipamento-djs/usado/xdj?sb=all_mercadolibre
```

Em outras palavras:

- `usado` representa a condição.
- `xdj` é o termo pesquisado.

## Observação

Esse fluxo usa o browser para renderizar a página antes de extrair os cards, o que é o caminho mais estável quando a listagem bloqueia `requests`.
