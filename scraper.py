from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


BASE_URL = "https://lista.mercadolivre.com.br"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


@dataclass(frozen=True)
class Product:
    title: str
    price: str
    url: str


def slugify_term(term: str) -> str:
    return term.strip().lower().replace(" ", "-")


def build_search_url(
    query: str,
    *,
    condition: str = "used",
    category_path: str | None = None,
    apply_condition_in_path: bool = True,
) -> str:
    parts: list[str] = [BASE_URL]

    if category_path:
        parts.append(category_path.strip("/"))

    if condition == "used" and apply_condition_in_path:
        parts.append("usado")

    parts.append(slugify_term(query))
    return "/".join(parts) + "?sb=all_mercadolibre"


def first_text(elements: Iterable[str]) -> str:
    for value in elements:
        if value:
            return value.strip()
    return ""


def click_condition_filter(page, condition: str = "used", verbose: bool = False) -> None:
    """Clica no filtro de condição (Novo/Usado) na página de busca."""
    condition_labels = {
        "used": ["Usados", "usados", "usado"],
        "new": ["Novo", "novo", "novos"],
    }
    
    target_labels = condition_labels.get(condition, ["Usados"])
    
    # Procura por um elemento que contenha o texto do filtro
    for label in target_labels:
        try:
            # Usa filter com has_text que funciona melhor
            filter_element = page.locator("label").filter(has_text=label).first
            if filter_element.is_visible(timeout=5000):
                if verbose:
                    print(f"[Debug] Encontrou label com '{label}'")
                filter_element.click()
                page.wait_for_timeout(3000)  # Aguarda mais tempo após clique
                page.wait_for_load_state("networkidle", timeout=15_000)
                page.wait_for_timeout(2000)  # Mais espera após network idle
                if verbose:
                    print(f"[Debug] Clique bem-sucedido no filtro '{label}'")
                return
        except (PlaywrightTimeoutError, Exception) as e:
            if verbose:
                print(f"[Debug] Label '{label}' não encontrado: {e}")
            continue
    
    # Fallback: tenta encontrar via role attribute
    try:
        filter_element = page.locator("input[role='checkbox'][aria-label*='Usados']").first
        if filter_element.is_visible(timeout=5000):
            if verbose:
                print(f"[Debug] Encontrou checkbox via aria-label")
            filter_element.click()
            page.wait_for_timeout(3000)
            page.wait_for_load_state("networkidle", timeout=15_000)
            page.wait_for_timeout(2000)
            if verbose:
                print(f"[Debug] Clique bem-sucedido no checkbox")
            return
    except (PlaywrightTimeoutError, Exception) as e:
        if verbose:
            print(f"[Debug] Fallback checkbox não funcionou: {e}")
    
    if verbose:
        print("[Debug] Nenhum filtro encontrado! Continuando sem clicar...")


def extract_products(page, verbose: bool = False) -> list[Product]:
    try:
        page.wait_for_load_state("domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=15_000)
        except PlaywrightTimeoutError:
            pass

        # Aguarda um pouco extra para o React renderizar completamente
        page.wait_for_timeout(4000)
    except Exception as e:
        if verbose:
            print(f"[Debug] Erro durante espera inicial: {e}")
        return []

    # Debug: verifica quantos itens estão no DOM antes de começar
    if verbose:
        try:
            item_count = page.evaluate("() => document.querySelectorAll('li.ui-search-layout__item').length")
            scroll_height = page.evaluate("() => document.documentElement.scrollHeight")
            print(f"[Debug] Itens no DOM: {item_count}, Altura da página: {scroll_height}")
        except Exception as e:
            print(f"[Debug] Erro ao inspecionar: {e}")

    seen_urls: set[str] = set()
    products: list[Product] = []
    previous_scroll_height = 0
    max_iterations = 100  # Aumentado muito
    wait_time = 2500  # Mais tempo entre scrolls

    for iteration in range(max_iterations):
        try:
            # Scroll agressivo para o final
            page.evaluate("() => window.scrollBy(0, 10000)")
            page.wait_for_timeout(wait_time)
        except Exception as e:
            if verbose:
                print(f"[Debug] Erro durante scroll: {e}")
            break

        try:
            # Verifica altura atual da página
            current_scroll_height = page.evaluate("() => document.documentElement.scrollHeight")
            
            rows = page.evaluate(
                """
                () => Array.from(document.querySelectorAll('li.ui-search-layout__item'))
                  .map((item) => {
                    const titleNode = item.querySelector('a.poly-component__title, h3.poly-component__title-wrapper a, a[href*="produto.mercadolivre.com.br/MLB-"]');
                    const priceNode = item.querySelector('span.andes-money-amount__fraction');
                    const linkNode = item.querySelector('a[href*="produto.mercadolivre.com.br/MLB-"]');
                    const title = (titleNode?.textContent || titleNode?.getAttribute('aria-label') || '').trim();
                    const price = (priceNode?.textContent || '').trim();
                    const url = linkNode?.href || titleNode?.href || '';
                    return { title, price, url };
                  })
                  .filter((item) => item.title && item.price)
                """
            )
        except Exception as e:
            if verbose:
                print(f"[Debug] Erro durante evaluate: {e}")
            break

        new_products_count = 0
        for row in rows:
            if row["url"] and row["url"] not in seen_urls:
                seen_urls.add(row["url"])
                products.append(Product(title=row["title"], price=row["price"], url=row["url"]))
                new_products_count += 1

        if verbose and (new_products_count > 0 or iteration % 10 == 0):
            print(f"[Iteração {iteration + 1}] Produtos: {len(products)}, Novos: {new_products_count}, Altura: {current_scroll_height}")

        # Para quando a altura da página não muda mais (fim do conteúdo)
        if current_scroll_height == previous_scroll_height:
            if verbose:
                print(f"[Iteração {iteration + 1}] Fim do conteúdo. Total: {len(products)}")
            break
        
        previous_scroll_height = current_scroll_height

    return products


def search_products(
    query: str,
    *,
    condition: str = "used",
    category_path: str | None = None,
    headed: bool = False,
    click_filter: bool = False,  # Revertido para False (usa URL com /usado/)
    verbose: bool = False,
) -> tuple[str, list[Product]]:
    # Por padrão, usa a URL com a condição no path (/usado/)
    # Se click_filter é True, navega sem a condição e clica no filtro
    url = build_search_url(
        query,
        condition=condition,
        category_path=category_path,
        apply_condition_in_path=not click_filter,  # True quando click_filter é False
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not headed)
        page = browser.new_page(
            user_agent=USER_AGENT,
            locale="pt-BR",
            viewport={"width": 1440, "height": 1800},
            extra_http_headers={
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            },
        )
        
        if verbose:
            print(f"[Debug] Navegando para: {url}")
        
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(2000)  # Espera inicial após carregamento
        
        # Clica no filtro de condição se solicitado
        if click_filter and condition == "used":
            if verbose:
                print("[Debug] Clicando no filtro 'USADOS'...")
            click_condition_filter(page, condition, verbose=verbose)
        
        products = extract_products(page, verbose=verbose)
        browser.close()

    return url, products


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scraper do Mercado Livre usando navegador Chromium via Playwright.")
    parser.add_argument("query", help="Termo de busca, por exemplo: XDJ")
    parser.add_argument("--condition", choices=["used", "new"], default="used", help="Condição do produto")
    parser.add_argument(
        "--category-path",
        default="eletronicos-audio-video/audio/equipamento-djs",
        help="Caminho de categoria para reproduzir a navegação manual do site",
    )
    parser.add_argument("--headed", action="store_true", help="Abre o Chromium visível em vez de headless")
    parser.add_argument("--click-filter", action="store_true", help="Navega para a URL base e clica no filtro 'Usados'")
    parser.add_argument("--verbose", action="store_true", help="Mostra debug info durante o scroll e extração")
    parser.add_argument("--dry-run", action="store_true", help="Mostra a URL construída e não abre o navegador")
    parser.add_argument("--json", action="store_true", help="Imprime a saída em JSON")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    url = build_search_url(
        args.query,
        condition=args.condition,
        category_path=args.category_path,
        apply_condition_in_path=not args.click_filter,  # Usa /usado/ por padrão
    )

    if args.dry_run:
        print(url)
        return

    _, products = search_products(
        args.query,
        condition=args.condition,
        category_path=args.category_path,
        headed=args.headed,
        click_filter=args.click_filter,  # False por padrão
        verbose=args.verbose,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "url": url,
                    "count": len(products),
                    "products": [product.__dict__ for product in products],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    print(f"URL: {url}")
    print(f"Produtos encontrados: {len(products)}")
    for index, product in enumerate(products, start=1):
        print(f"{index}. {product.title} | {product.price}")
        if product.url:
            print(f"   {product.url}")


if __name__ == "__main__":
    main()
