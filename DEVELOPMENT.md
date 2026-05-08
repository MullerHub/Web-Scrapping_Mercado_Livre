# Notas de Desenvolvimento

## 📅 Data: 7 de maio de 2026

### 🎯 Sessão Atual: Investigação de Scraper Mercado Livre

---

## ✅ O que foi alcançado nesta sessão

### 1. Identificação do Bloqueio HTTP
- Tentamos inicialmente usar `requests` + `BeautifulSoup`
- **Resultado:** Mercado Livre bloqueia requisições HTTP com desafio `_bmstate` (SHA256 hashcash)
- **Solução:** Pivotamos para **Playwright** (browser automation)

### 2. Implementação com Playwright
- ✅ Integração do Playwright com Chromium
- ✅ Construção de URLs dinâmicas com suporte a categorias
- ✅ Extração de dados via `page.evaluate()` (JavaScript no contexto do navegador)
- ✅ CLI com múltiplas flags (`--headed`, `--verbose`, `--json`, `--dry-run`)
- ✅ Testes bem-sucedidos de extração (1 produto validado)

### 3. Otimizações de Scroll
- ✅ Implementação de scroll infinito
- ✅ Detecção de fim de página por `scrollHeight`
- ✅ Tratamento robusto de erros com try/except
- ✅ Mode verbose para debug

### 4. Descoberta da Limitação de Login
- 🔒 **Descoberto:** O Mercado Livre bloqueia o filtro "Usado" sem autenticação
- 📊 **Resultado:**
  - Sem login: 1 produto capturado
  - Com login (manual do usuário): 18 produtos disponíveis
  - Diferença: 17 produtos "escondidos" sem autenticação

---

## 🛑 Onde Paramos Exatamente

### Status do Código
- ✅ `scraper.py`: Completamente funcional sem login
- ✅ `requirements.txt`: Playlist 1.59.0 instalado e testado
- ✅ `README.md`: Documentação atualizada com roadmap completo

### Por que não implementamos login ainda?
1. Sem credenciais fornecidas pelo usuário (por segurança)
2. Escopo inicial era apenas criar o scraper básico
3. Login requer validação de segurança adicional

### Próximo Passo Definido
- Implementar `login_to_mercadolivre()` function
- Adicionar flags `--email` e `--password` ao CLI
- Testar com conta logada para validar 18 produtos

---

## 📋 Checklist para Retomada

### Fase 3a: Login Implementation (PRÓXIMA)
- [ ] Criar função `login_to_mercadolivre(page, email, password)`
- [ ] Adicionar argumentos ao `parse_args()`: `--email`, `--password`
- [ ] Modificar `search_products()` para chamar login se credenciais fornecidas
- [ ] Testar com email/senha do usuário
- [ ] Validar que retorna 18+ produtos com login

### Fase 3b: Security Hardening
- [ ] Implementar suporte a `.env` (python-dotenv)
- [ ] Adicionar `.env` ao `.gitignore`
- [ ] Documentar como usar variáveis de ambiente

### Fase 3c: Polish & Deployment
- [ ] Tratamento de erros de login (credenciais inválidas)
- [ ] Cache de sessão (evitar login toda vez)
- [ ] Rate-limiting protection
- [ ] Logging estruturado

---

## 🔍 Investigações Técnicas Realizadas

### DOM Structure (Descoberto)
```javascript
// Cards principais
li.ui-search-layout__item

// Elemento do título (fallback chain)
a.poly-component__title
h3.poly-component__title-wrapper a  
a[href*="produto.mercadolivre.com.br/MLB-"]

// Preço
span.andes-money-amount__fraction

// Link do produto
a[href*="produto.mercadolivre.com.br/MLB-"]
```

### URL Patterns (Confirmado)
```
Sem filtro:
https://lista.mercadolivre.com.br/eletronicos-audio-video/audio/equipamento-djs/xdj?sb=all_mercadolibre

Com filtro usado:
https://lista.mercadolivre.com.br/eletronicos-audio-video/audio/equipamento-djs/usado/xdj?sb=all_mercadolibre
```

### Comportamento do Mercado Livre
- URL com `/usado/` redireciona para login se não autenticado
- Sem autenticação: retorna resultado mínimo (1 produto)
- Com autenticação: retorna resultado completo (18+ produtos)
- Scroll infinito funciona em ambos os casos

---

## 💾 Arquivos Modificados

### scraper.py
- ✅ Classe `Product` (dataclass frozen)
- ✅ `slugify_term(term)` - normaliza busca
- ✅ `build_search_url()` - constrói URL com categorias e condições
- ✅ `click_condition_filter()` - clica em filtro (experimental, requer login)
- ✅ `extract_products(page, verbose)` - scroll infinito + extração
- ✅ `search_products()` - orquestra navegação e extração
- ✅ `parse_args()` - CLI com 8+ flags
- ✅ `main()` - entry point

### README.md
- ✅ Documentação completa (reescrita)
- ✅ Roadmap adicionado
- ✅ FAQs sobre login
- ✅ Notas técnicas e problemas resolvidos

---

## 🧠 Aprendizados Principais

1. **Anti-bot Protection é Real**
   - Mercado Livre usa hashcash SHA256 + redirects para login
   - Burlar requer browser automation completo

2. **Playwright é Poderoso**
   - `page.evaluate()` permite JavaScript no contexto do navegador
   - Muito mais confiável que parsing HTML estático

3. **Login é Gargalo**
   - Sem autenticação, dados são limitados
   - Com autenticação, todos os filtros funcionam
   - Requer tratamento especial de segurança

4. **Scroll Infinito é Detectável**
   - Monitorar `scrollHeight` é mais confiável que contador de rodadas
   - React renderiza dinamicamente, precisa de timeouts

---

## 📝 Como Retomar Daqui a Dias

1. **Abrir este arquivo primeiro** para contexto
2. **Criar branch** para feature de login:
   ```bash
   git checkout -b feature/login-support
   ```
3. **Seguir checklist da Fase 3a** neste arquivo
4. **Testar com:** `python scraper.py "XDJ" --email seu@email.com --password sua_senha --headed --verbose`
5. **Validar:** Deve retornar 18 produtos

---

## 🚨 Problemas Conhecidos / Aviso

⚠️ **Sem Login:** Máximo 1 resultado
- Não é bug, é limitação do site sem autenticação
- Esperado e documentado

⚠️ **Click no Filtro Fallback:** Não funciona
- Seletor CSS `label:has-text()` requer login prévio
- Pode ser removido após implementar login real

---

## 📞 Notas para o Futuro

- Usuário alertou que **sem login pede autenticação**
- Confirmado que com **login manual ele viu 18 produtos**
- Solução está bem definida: implementar login automático
- Segurança é crítica: **NUNCA commitar credenciais**

---

**Status:** 🟡 **Em Desenvolvimento** (Phase 2 of 3)
**Próxima Sessão:** Login Implementation
**Estimativa:** 2-3 horas para implementar + testar

---

*Criado em: 7 de maio de 2026*
*Última atualização: Session 1 (atual)*
