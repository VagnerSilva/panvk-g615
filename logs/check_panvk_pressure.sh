#!/usr/bin/env bash
set -euo pipefail

PKG="${1:-com.nyushu.androbench2}"
IDLE_WAIT="${2:-30}"
LOG_FILE="panvk_mem_validation_$(date +%Y%m%d_%H%M%S).log"

if ! adb get-state >/dev/null 2>&1; then
    echo "Erro: Nenhum dispositivo Android conectado via ADB."
    exit 1
fi

get_mem_metrics() {
    local prefix="$1"
    local label="$2"
    local dump
    dump=$(adb shell dumpsys meminfo "$PKG" 2>/dev/null || true)

    if [[ -z "$dump" || "$dump" == *"No process found"* ]]; then
        echo "[$label] Processo $PKG não encontrado!"
        return 1
    fi

    local gl_mtrack egl_mtrack other_mmap native_heap total_pss swap_pss
    gl_mtrack=$(echo "$dump" | awk "/GL mtrack/ {print \$3; exit}")
    egl_mtrack=$(echo "$dump" | awk "/EGL mtrack/ {print \$3; exit}")
    other_mmap=$(echo "$dump" | awk "/Other mmap/ {print \$3; exit}")
    native_heap=$(echo "$dump" | awk "/Native Heap/ {print \$3; exit}")
    total_pss=$(echo "$dump" | awk "/TOTAL PSS:/ {print \$3; exit}")
    swap_pss=$(echo "$dump" | awk "/TOTAL SWAP PSS:/ {print \$7; exit}")

    gl_mtrack=${gl_mtrack:-0}
    egl_mtrack=${egl_mtrack:-0}
    other_mmap=${other_mmap:-0}
    native_heap=${native_heap:-0}
    total_pss=${total_pss:-0}
    swap_pss=${swap_pss:-0}

    printf "%-18s | %10d | %10d | %10d | %10d | %10d | %10d\n" \
        "$label" \
        "$((gl_mtrack / 1024))" \
        "$((egl_mtrack / 1024))" \
        "$((other_mmap / 1024))" \
        "$((native_heap / 1024))" \
        "$((total_pss / 1024))" \
        "$((swap_pss / 1024))" | tee -a "$LOG_FILE"

    printf -v "${prefix}_GL" "%s" "$gl_mtrack"
}

echo "==================================================================================================" | tee "$LOG_FILE"
echo " Validação de Pressão de Memória PanVK (G615) - Pacote: $PKG" | tee -a "$LOG_FILE"
echo "==================================================================================================" | tee -a "$LOG_FILE"

adb logcat -c

echo ""
echo "1) Abra o app ($PKG) e deixe-o parado no MENU INICIAL (antes de rodar o teste)."
read -rp "   Pressione [ENTER] quando estiver no menu inicial..."

printf "\n%-18s | %10s | %10s | %10s | %10s | %10s | %10s\n" \
    "FASE" "GL (MB)" "EGL (MB)" "MMAP (MB)" "NATIVE(MB)" "TOTAL(MB)" "SWAP (MB)" | tee -a "$LOG_FILE"
echo "--------------------------------------------------------------------------------------------------" | tee -a "$LOG_FILE"

get_mem_metrics "BASELINE" "1_BASELINE"

echo ""
echo "2) Inicie o benchmark/cena 3D pesada agora."
read -rp "   Pressione [ENTER] durante o PICO da carga gráfica..."

get_mem_metrics "PICO" "2_PICO_CARGA"

echo ""
echo "3) Encerre o teste e volte para o MENU INICIAL (deixe o app ocioso em primeiro plano)."
read -rp "   Pressione [ENTER] assim que voltar ao menu..."

echo "   Aguardando ${IDLE_WAIT}s para o shrinker/idle timeout do driver agir..."
sleep "$IDLE_WAIT"

get_mem_metrics "IDLE" "3_APOS_IDLE"

echo "--------------------------------------------------------------------------------------------------" | tee -a "$LOG_FILE"

DELTA_GL_MB=$(( (PICO_GL - IDLE_GL) / 1024 ))
RETAINED_GL_MB=$(( (IDLE_GL - BASELINE_GL) / 1024 ))
LMKD_KILLS=$(adb logcat -d | grep -c "lowmemorykiller: Kill" || true)
PANVK_ERRORS=$(adb logcat -d | grep -iE "VK_ERROR|Tiler OOM|panvk.*fail|kbase.*fail" || true)

echo "" | tee -a "$LOG_FILE"
echo "=== RESUMO DO DIAGNÓSTICO ===" | tee -a "$LOG_FILE"
echo "• Memória GPU (GL mtrack) liberada após idle: ${DELTA_GL_MB} MB" | tee -a "$LOG_FILE"
echo "• Memória GPU retida acima do baseline:       ${RETAINED_GL_MB} MB" | tee -a "$LOG_FILE"
echo "• Kills disparados pelo LMKD durante o teste: ${LMKD_KILLS}" | tee -a "$LOG_FILE"

if [[ "$LMKD_KILLS" -gt 0 ]]; then
    echo "⚠️  ALERTA: O sistema ainda sofreu pressão crítica de RAM ($LMKD_KILLS processos encerrados pelo LMKD)." | tee -a "$LOG_FILE"
else
    echo "✅ LMKD estável: Nenhum processo foi derrubado por pressão de memória." | tee -a "$LOG_FILE"
fi

if [[ "$RETAINED_GL_MB" -gt 250 ]]; then
    echo "⚠️  RETENÇÃO ALTA: Mais de 250 MB de memória GPU permaneceram alocados após ${IDLE_WAIT}s ocioso." | tee -a "$LOG_FILE"
else
    echo "✅ SHRINKER OK: Os buffers ociosos da GPU retornaram próximo ao nível inicial." | tee -a "$LOG_FILE"
fi

if [[ -n "$PANVK_ERRORS" ]]; then
    echo "❌ ERROS DO DRIVER DETECTADOS:" | tee -a "$LOG_FILE"
    echo "$PANVK_ERRORS" | tee -a "$LOG_FILE"
else
    echo "✅ DRIVER ESTÁVEL: Sem falhas de alocação Vulkan ou Tiler OOM." | tee -a "$LOG_FILE"
fi

echo ""
echo "Relatório completo salvo em: $LOG_FILE"
