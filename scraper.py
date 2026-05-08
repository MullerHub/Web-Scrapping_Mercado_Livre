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


def click_condition_filter(page, condition: str = "used") -> None:
    """Clica no filtro de condição (Novo/Usado) na página de busca."""
    condition_labels = {
        "used": ["usados", "usado"],
        "new": ["novo", "novos"],
    }
    
    target_labels = condition_labels.get(condition, ["usados"])
    
    # Procura por um elemento que contenha o texto do filtro (case-insensitive)
    for label in target_labels:
        try:
            # Tenta encontrar um checkbox ou label com o texto do filtro
            filter_element = page.locator(f"label:has-text(/{label}/i)").first
            if filter_element.is_visible(timeout=5000):
                filter_element.click()
                page.wait_for_load_state("networkidle", timeout=15_000)
                return
        except (PlaywrightTimeoutError, Exception):
            continue
    
    # Fallback: tenta encontrar via aria-label
    try:
        filter_element = page.locator(f"[aria-label*='{target_labels[0].capitalize()}']").first
        if filter_element.is_visible(timeout=5000):
            filter_element.click()
            page.wait_for_load_state("networkidle", timeout=15_000)
            return
    except (PlaywrightTimeoutError, Exception):
        pass


def extract_products(page, verbose: bool = False) -> list[Product]:
    page.wait_for_load_state("domcontentloaded")
    try:
        page.wait_for_load_state("networkidle", timeout=10_000)
    except PlaywrightTimeoutError:
        pass

    # Aguarda um pouco extra para o React renderizar
    page.wait_for_timeout(2000)

    seen_urls: set[str] = set()
    products: list[Product] = []
    stable_rounds = 0
    previous_count = 0
    max_iterations = 30  # Aumentado para capturar mais itens
    scroll_distance = 5000
    wait_time = 1500

    for iteration in range(max_iterations):
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

        new_products_count = 0
        for row in rows:
            if row["url"] and row["url"] not in seen_urls:
                seen_urls.add(row["url"])
                products.append(Product(title=row["title"], price=row["price"], url=row["url"]))
                new_products_count += 1

        if verbose:
            print(f"[Iteração {iteration + 1}] Itens no DOM: {len(rows)}, Novos produtos: {new_products_count}, Total: {len(products)}")

        if len(rows) == previous_count:
            stable_rounds += 1
        else:
            stable_rounds = 0
        previous_count = len(rows)

        # Para após 5 rodadas sem novos itens ou se já tem produtos suficientes
        if stable_rounds >= 5 or (len(products) > 0 and len(rows) == 0):
            if verbose:
                print(f"[Iteração {iteration + 1}] Nenhum novo item detectado. Encerrando busca.")
            break

        # Scroll para o final
        page.mouse.wheel(0, scroll_distance)
        page.wait_for_timeout(wait_time)

    return products


def search_products(
    query: str,
    *,
    condition: str = "used",
    category_path: str | None = None,
    headed: bool = False,
    click_filter: bool = True,  # Alterado para True por padrão
    verbose: bool = False,
) -> tuple[str, list[Product]]:
    # Sempre navega para URL sem a condição no path e clica no filtro
    # Isso funciona melhor que ir direto pra URL com /usado/
    url = build_search_url(
        query,
        condition=condition,
        category_path=category_path,
        apply_condition_in_path=False,  # Sempre False para usar click_filter
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
        
        # Clica no filtro de condição
        if click_filter and condition == "used":
            if verbose:
                print("[Debug] Clicando no filtro 'USADOS'...")
            click_condition_filter(page, condition)
        
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
    parser.add_argument("--no-click-filter", action="store_true", help="Desativa o clique automático no filtro (navega direto para URL com /usado/)")
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
        apply_condition_in_path=not args.click_filter,
    )

    if args.dry_run:
        print(url)
        return

    _, products = search_products(
        args.query,
        condition=args.condition,
        category_path=args.category_path,
        headed=args.headed,
        click_filter=args.click_filter,
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
