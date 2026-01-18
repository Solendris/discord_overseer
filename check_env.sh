#!/bin/bash
# check_env.sh

echo "---------------------------------------------------"
echo "🔍 DIAGNOSTYKA ŚRODOWISKA (Environment Diagnostics)"
echo "---------------------------------------------------"

echo -e "\n1. Sprawdzam kontenery Docker (Docker Containers):"
docker ps -a | grep -E "discord|overseer" || echo "   ✅ Brak aktywnych kontenerów discord/overseer."

echo -e "\n2. Sprawdzam Harmonogram zadań (Crontab):"
if crontab -l 2>/dev/null | grep -q "run_once.sh"; then
    echo "   ⚠️ ZNALEZIONO CRON:"
    crontab -l | grep "run_once.sh"
else
    echo "   ✅ Czysto. Brak wpisów w crontab dla bieżącego użytkownika."
fi

echo -e "\n3. Sprawdzam aktywne procesy (Active Processes):"
# Szukamy procesów pythona lub skryptu shell
ps aux | grep -v grep | grep -E "main.py|run_once.sh" || echo "   ✅ Brak działających procesów aplikacji w tle."

echo -e "\n---------------------------------------------------"
