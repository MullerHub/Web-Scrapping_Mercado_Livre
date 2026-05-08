# Web Scraper Mercado Livre

Scraper em Python usando **Playwright** para automação de navegador e extração de produtos do Mercado Livre por nome, com filtro de condição (novo/usado).

---

## 🎯 Objetivo

Criar um web scraper que reproduza o comportamento manual de um usuário navegando no Mercado Livre:
- Pesquisar por termo (ex: "XDJ")
- Aplicar filtro de condição ("Usado")
- Extrair título, preço e URL de cada produto
- Suportar scroll infinito para capturar todos os resultados

---

## ✅ O que foi implementado

### Fase 1: Investigação Inicial (Bloqueio HTTP)
- ❌ Tentativa inicial com `requests` + `BeautifulSoup` fracassou
- 🔍 Descoberto: Mercado Livre bloqueia requisições HTTP diretas com desafio SHA256 (`_bmstate`)
- 📊 Análise da proteção anti-bot do site

### Fase 2: Implementação com Playwright ✅
- ✅ Integração com Playwright para automação de navegador (Chromium)
- ✅ Construção dinâmica de URLs de busca com suporte a categorias e condições
- ✅ Extração de dados via JavaScript evaluation no contexto da página renderizada
- ✅ Scroll infinito para capturar múltiplos produtos
- ✅ Suporte a modo headless e visible (`--headed`)
- ✅ CLI com múltiplas opções (flags)
- ✅ Saída em texto ou JSON
- ✅ Modo dry-run para verificar URL antes de executar

### Fase 3: Otimizações
- ✅ Detecção de fim de página por `scrollHeight` (em vez de contador de rodadas)
- ✅ Timeouts aumentados para melhor renderização
- ✅ Tratamento robusto de erros
- ✅ Debug mode com `--verbose` para diagnóstico

---

## 📍 Onde paramos

**Status Atual:** Scraper funcional sem login (captura 1 produto)

### Limitação Identificada
🔒 **O Mercado Livre requer login para acessar filtros avançados e ver todos os anúncios**
- Sem login: 1 resultado capturado
- Com login: 18 resultados (conforme teste manual do usuário)

### Razão do Bloqueio
O filtro "USADOS" redireciona para página de login quando não autenticado:
```text
https://lista.mercadolivre.com.br/eletronicos-audio-video/audio/equipamento-djs/usado/xdj
		  ↓ (sem login)
https://auth.mercadolivre.com.br/login
```

---

## 🚀 Como usar (Estado Atual)

### Instalação

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### Uso Básico

```bash
# Busca simples (sem login - 1 resultado)
python scraper.py "XDJ" --condition used

# Ver URL sem executar
python scraper.py "XDJ" --condition used --dry-run

# Com janela visível (debug)
python scraper.py "XDJ" --condition used --headed

# Modo verbose com debug info
python scraper.py "XDJ" --condition used --headed --verbose

# Saída em JSON
python scraper.py "XDJ" --condition used --json
```

### Opções Disponíveis

```
python scraper.py QUERY [OPTIONS]

QUERY                 Termo de busca (ex: "XDJ", "iPhone")

OPTIONS:
  --condition {used,new}  Filtro de condição (padrão: used)
  --category-path PATH    Caminho da categoria (padrão: eletronicos-audio-video/audio/equipamento-djs)
  --headed               Abre o navegador visível
  --click-filter         Navega para URL base e clica no filtro (experimental)
  --verbose              Mostra debug info durante extração
  --dry-run              Apenas constrói e exibe a URL
  --json                 Retorna output em JSON
```

### Exemplos

```bash
# Buscar iPhones usados com navegador visível
python scraper.py "iPhone" --condition used --headed

# Buscar em categoria diferente
python scraper.py "Notebook" --category-path "computadores/notebooks" --condition used

# Output JSON
python scraper.py "XDJ" --json > resultados.json

# Com debug verbose
python scraper.py "XDJ" --headed --verbose
```

---

## 🔑 Como Adicionar Login (Próxima Etapa)

### Implementação Necessária

Para capturar todos os 18+ produtos, será necessário:

1. **Adicionar credenciais ao CLI:**
```bash
python scraper.py "XDJ" --condition used --email seu@email.com --password sua_senha --headed
```

2. **Implementação no código** (ainda não feita):

```python
def login_to_mercadolivre(page, email: str, password: str, verbose: bool = False) -> bool:
	"""
	Realiza login na conta do Mercado Livre
    
	Args:
		page: Página Playwright
		email: Email da conta
		password: Senha da conta
		verbose: Modo debug
    
	Returns:
		True se login bem-sucedido, False caso contrário
	"""
	# 1. Navegar para página de login
	# 2. Preencher email e clicar "Continuar"
	# 3. Aguardar para preencher senha
	# 4. Enviar formulário e aguardar redirecionamento
	# 5. Verificar se está autenticado
```

3. **Modificar `search_products()`** para fazer login antes de navegar:

```python
def search_products(
	query: str,
	*,
	condition: str = "used",
	category_path: str | None = None,
	headed: bool = False,
	verbose: bool = False,
	email: str | None = None,           # NOVO
	password: str | None = None,        # NOVO
) -> tuple[str, list[Product]]:
	# ... código existente ...
    
	page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    
	# NOVO: Login se credenciais fornecidas
	if email and password:
		if verbose:
			print("[Debug] Realizando login...")
		login_success = login_to_mercadolivre(page, email, password, verbose)
		if not login_success:
			raise Exception("Falha no login")
    
	# ... resto do código ...
```

4. **Adicionar ao `parse_args()`:**

```python
parser.add_argument("--email", help="Email da conta Mercado Livre (para login)")
parser.add_argument("--password", help="Senha da conta Mercado Livre (para login)")
```

### ⚠️ Considerações de Segurança

- **Nunca commitar credenciais no Git**
- Usar variáveis de ambiente: `os.getenv("ML_EMAIL")` e `os.getenv("ML_PASSWORD")`
- Ou usar arquivo `.env` (add ao `.gitignore`)

Exemplo com `.env`:
```bash
# .env
ML_EMAIL=seu_email@example.com
ML_PASSWORD=sua_senha_segura
```

```python
from dotenv import load_dotenv

load_dotenv()
email = os.getenv("ML_EMAIL")
password = os.getenv("ML_PASSWORD")
```

---

## 📊 Estrutura do Projeto

```
.
├── scraper.py           # Script principal
├── requirements.txt     # Dependências (playwright)
├── README.md           # Documentação
└── .venv/              # Ambiente virtual
```

### Fluxo de Execução

```
1. parse_args() → Lê argumentos da linha de comando
2. build_search_url() → Constrói URL do Mercado Livre
3. search_products() → Inicia navegador e navega para URL
4. extract_products() → Scroll infinito + extração de dados
5. Output → Exibe resultados (texto ou JSON)
```

---

## 🔧 Estrutura de Dados

### Produto (Dataclass)
```python
@dataclass(frozen=True)
class Product:
	title: str    # Ex: "Pioneer Dj Xdj-700 Reprodutor Digital Compacto"
	price: str    # Ex: "5.530"
	url: str      # Link completo do produto
```

---

## 🧪 Testes Realizados

| Teste | Status | Resultado |
|-------|--------|-----------|
| HTTP requests + BeautifulSoup | ❌ Falhou | Bloqueado por anti-bot |
| Playwright sem filtro dinâmico | ✅ Sucesso | 1 produto extraído |
| Playwright com scroll infinito | ✅ Sucesso | Detecção de fim de página |
| Click no filtro "Usados" | ⚠️ Parcial | Requer login (redireciona) |
| JSON output | ✅ Sucesso | Output formatado |
| Modo verbose | ✅ Sucesso | Debug info funcionando |

---

## 📝 Notas Técnicas

### DOM Selectors Descobertos
```javascript
// Cards de produtos
'li.ui-search-layout__item'

// Título
'a.poly-component__title' 
'h3.poly-component__title-wrapper a'

// Preço
'span.andes-money-amount__fraction'

// Link do produto
'a[href*="produto.mercadolivre.com.br/MLB-"]'
```

### URL Pattern
```
https://lista.mercadolivre.com.br/{category}/{condition}/{query}?sb=all_mercadolibre

Exemplo com login:
https://lista.mercadolivre.com.br/eletronicos-audio-video/audio/equipamento-djs/usado/xdj?sb=all_mercadolibre
```

### Problemas Resolvidos
1. **Bloqueio HTTP** → Solução: Usar Playwright (browser automation)
2. **Poucos resultados sem scroll** → Solução: Scroll infinito com detecção de altura
3. **React rendering** → Solução: Aguardar `networkidle` + timeout extra

---

## 🚫 Limitações Atuais

- **Sem login:** Máximo 1 resultado
- **Com login:** Até ~18 resultados (testado manualmente)
- **Sem implementação:** Detecção automática de paginação tradicional (se houver)
- **Rate-limiting:** Possível limite de requisições após muitas buscas

---

## 📋 Roadmap (Próximas Fases)

### Curto Prazo (Priority Alta)
- [ ] Implementar login automático (email + senha)
- [ ] Testar com conta logada para validar 18 produtos
- [ ] Tratar erro de login (credenciais inválidas)

### Médio Prazo
- [ ] Suporte a variáveis de ambiente (.env)
- [ ] Cache de sessão (não fazer login toda vez)
- [ ] Retry logic com exponential backoff
- [ ] Logging estruturado

### Longo Prazo
- [ ] Filtros adicionais (preço mín/máx, localização)
- [ ] Suporte a múltiplas buscas em batch
- [ ] Banco de dados para histórico
- [ ] API REST simples
- [ ] Docker container

---

## ❓ FAQs

**P: Por que o scraper retorna apenas 1 produto?**
R: Sem login, o Mercado Livre bloqueia o filtro "Usado" e retorna conteúdo reduzido.

**P: Como fazer login?**
R: Ainda está em desenvolvimento. Será adicionado nas próximas etapas (veja "Como Adicionar Login").

**P: É seguro compartilhar minhas credenciais?**
R: Não! Use variáveis de ambiente ou arquivo .env, nunca commit no Git.

**P: Posso usar em produção?**
R: Apenas após implementar login e testar com múltiplas contas. Respeite ToS do Mercado Livre.

---

## 📚 Referências

- [Playwright Documentation](https://playwright.dev/python/)
- [Mercado Livre Brasil](https://lista.mercadolivre.com.br)
- DOM Inspector do Chrome/Firefox para descobrir novos seletores

---

**Última atualização:** 7 de maio de 2026
**Status:** Em desenvolvimento (fase 2 de 3)

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
