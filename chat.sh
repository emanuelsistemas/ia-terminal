#!/bin/bash

echo "Bem-vindo ao chat da IA na VPS!"
echo "Digite sua mensagem (ou 'sair' para encerrar):"
echo "----------------------------------------"

while true; do
    read -p "Você: " mensagem
    if [ "$mensagem" = "sair" ]; then
        echo "IA: Até logo! Foi um prazer conversar com você."
        break
    fi
    
    case "$mensagem" in
        *"ola"* | *"oi"* | *"olá"*)
            echo "IA: Olá! Como posso ajudar você hoje?"
            ;;
        *"como vai"* | *"tudo bem"*)
            echo "IA: Estou funcionando perfeitamente! Como posso ser útil?"
            ;;
        *"hora"* | *"data"*)
            echo "IA: Agora são $(date '+%H:%M:%S do dia %d/%m/%Y')"
            ;;
        *"sistema"* | *"linux"*)
            echo "IA: Estamos em um sistema $(uname -s) $(uname -r)"
            ;;
        *"memoria"* | *"memória"*)
            echo "IA: Aqui está o status da memória:"
            free -h
            ;;
        *"disco"*)
            echo "IA: Aqui está o uso do disco:"
            df -h /
            ;;
        *"processos"*)
            echo "IA: Aqui estão os principais processos:"
            ps aux | head -5
            ;;
        *"ajuda"* | *"help"*)
            echo "IA: Posso ajudar com:"
            echo "- Informações do sistema (digite 'sistema')"
            echo "- Status da memória (digite 'memoria')"
            echo "- Uso do disco (digite 'disco')"
            echo "- Processos ativos (digite 'processos')"
            echo "- Data e hora (digite 'hora')"
            echo "- E muito mais! Experimente conversar naturalmente"
            ;;
        *)
            echo "IA: Desculpe, não entendi completamente. Digite 'ajuda' para ver o que posso fazer!"
            ;;
    esac
    echo "----------------------------------------"
done
