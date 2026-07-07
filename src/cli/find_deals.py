"""
Herramienta CLI: Buscador de Chollos por Categoría
Este script busca en Amazon los productos en oferta de una categoría concreta
(ej. "Videojuegos") y los muestra en consola con su título, descuento y precio.
Es el punto de partida para automatizar la caza de chollos sin pegar URLs manualmente.
"""

import sys
import argparse
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.use_cases.find_deals import FindDealsUseCase


def main():
    parser = argparse.ArgumentParser(description="Busca chollos de Amazon por categoría.")
    parser.add_argument("categoria", help='Nombre de la categoría (ej. "Videojuegos", "Informática y software").')
    parser.add_argument("--min-descuento", type=int, default=20, help="Descuento mínimo en %% (por defecto 20).")
    parser.add_argument("--max-descuento", type=int, default=None, help="Descuento máximo en %% (por defecto sin límite).")
    parser.add_argument("--limite", type=int, default=10, help="Número máximo de productos a mostrar (por defecto 10).")

    args = parser.parse_args()

    print(f"Buscando chollos en '{args.categoria}' con descuento mínimo del {args.min_descuento}%...")

    use_case = FindDealsUseCase()
    try:
        chollos = use_case.execute(
            args.categoria,
            min_descuento=args.min_descuento,
            max_descuento=args.max_descuento,
            limite=args.limite,
        )
    except ValueError as e:
        print(f"\n[!] {e}")
        sys.exit(1)

    if not chollos:
        print("\n[!] No se encontraron chollos que cumplan el descuento mínimo.")
        sys.exit(1)

    print("\n" + "=" * 70)
    print(f"=== {len(chollos)} CHOLLOS ENCONTRADOS EN '{args.categoria.upper()}' ===")
    print("=" * 70 + "\n")

    for p in chollos:
        titulo = p.titulo[:70] + ("..." if len(p.titulo) > 70 else "")
        precio = f"{p.precio_actual:.2f} {p.moneda}" if p.precio_actual else "Precio no disponible"
        print(f"-{p.descuento_porcentaje}%  {titulo}")
        print(f"   Precio: {precio}")
        print(f"   Imagen: {p.imagen_principal or '-'}")
        print(f"   Link:   {p.url_afiliado}")
        print()


if __name__ == "__main__":
    main()
