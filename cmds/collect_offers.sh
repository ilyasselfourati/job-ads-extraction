#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

read -rp "Mot-cle de recherche : " keywords
read -rp "Nombre minimum d'offres a collecter : " min_new_offers

uv run python -m jobscope.scraping.france_travail --keywords "$keywords" --min-new-offers "$min_new_offers"
