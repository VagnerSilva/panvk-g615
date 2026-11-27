#!/bin/bash

PKG="com.nyushu.androbench2"
DURATION="${1:-5}"

PKG=$(adb shell "dumpsys window | grep -E 'mCurrentFocus|mFocusedApp'" | grep -oE '[a-zA-Z0-9._]+/[a-zA-Z0-9._]+' | head -n 1 | cut -d/ -f1)
PID=$(adb shell pidof "$PKG" | awk '{print $1}' | tr -d '\r')

if [ -z "$PID" ]; then
  echo "Erro: Nyushu ($PKG) não está rodando. Inicie um jogo primeiro."
  exit 1
fi

echo "=== AUDITORIA PRÉ-PATCH: MESA 27 + KRAID (Mali-G615 MC2) ==="
echo "Coletando evidências por ${DURATION}s no PID $PID ($PKG)..."
echo ""

# -------------------------------------------------------------------
# TESTE 1: Comprovação do excesso de ioctls / IRQs do mali_kbase (sys 146%)
# -------------------------------------------------------------------
IRQ_START=$(adb shell "grep -iE 'mali|gpu|mfg' /proc/interrupts | awk '{sum=0; for(i=2;i<=9;i++) sum+=\$i; print sum}' | awk '{t+=\$1} END{print t}'" | tr -d '\r')
SYSCALL_START=$(adb shell "cat /proc/$PID/task/*/schedstat 2>/dev/null | awk '{sum+=\$3} END{print sum}'" | tr -d '\r')

# Contadores do MediaTek GED (GPU Utilization breakdown: Vertex / Fragment / Compute / Memory)
GED_START=$(adb shell "cat /sys/kernel/ged/hal/gpu_utilization 2>/dev/null" | tr -d '\r')

sleep "$DURATION"

IRQ_END=$(adb shell "grep -iE 'mali|gpu|mfg' /proc/interrupts | awk '{sum=0; for(i=2;i<=9;i++) sum+=\$i; print sum}' | awk '{t+=\$1} END{print t}'" | tr -d '\r')
SYSCALL_END=$(adb shell "cat /proc/$PID/task/*/schedstat 2>/dev/null | awk '{sum+=\$3} END{print sum}'" | tr -d '\r')
GED_END=$(adb shell "cat /sys/kernel/ged/hal/gpu_utilization 2>/dev/null" | tr -d '\r')

IRQ_PER_SEC=$(( (IRQ_END - IRQ_START) / DURATION ))
SLICES_PER_SEC=$(( (SYSCALL_END - SYSCALL_START) / DURATION ))

# -------------------------------------------------------------------
# TESTE 2: Auditoria de Banda de Memória / AFBC / Contadores Mali
# -------------------------------------------------------------------
MALI_MEM=$(adb shell "cat /sys/class/misc/mali0/device/mem_pool_size /sys/kernel/debug/mali0/gpu_memory 2>/dev/null | head -n 10" | tr -d '\r')
BANDWIDTH_INFO=$(adb shell "cat /sys/kernel/ged/hal/loading_base /sys/kernel/ged/hal/loading_stride 2>/dev/null" | tr -d '\r')

# -------------------------------------------------------------------
# TESTE 3: Auditoria dos Shaders em Cache / Variáveis de Ambiente do Processo
# -------------------------------------------------------------------
PROC_ENV=$(adb shell "su -c 'tr \"\0\" \"\n\" < /proc/$PID/environ 2>/dev/null' | grep -iE 'PAN_|MESA_|VK_'" | tr -d '\r')

echo "-------------------------------------------------------------------"
echo "EVIDÊNCIA 1: OVERHEAD DE SUBMISSÃO CSF / MALI_KBASE (Alvo #4)"
echo "-------------------------------------------------------------------"
echo "Interrupções de Hardware da GPU (IRQs/seg): ${IRQ_PER_SEC} IRQs/s"
echo "Time slices agendados nas threads/seg:      ${SLICES_PER_SEC} slices/s"
echo "-> Se IRQs/s > 1500: Comprova que o CSF/kbase está disparando kicks"
echo "   ou eventos de conclusão excessivos por frame (alvo: batching)."
echo ""

echo "-------------------------------------------------------------------"
echo "EVIDÊNCIA 2: SATURAÇÃO DE SHADERS VS BANDA DE MEMÓRIA (Alvos #2 e #3)"
echo "-------------------------------------------------------------------"
echo "GED GPU Utilization (Início): ${GED_START:-N/A}"
echo "GED GPU Utilization (Fim):    ${GED_END:-N/A}"
echo "Memória alocada no mali0:"
echo "${MALI_MEM:-Não exposto sem debugfs}"
echo "-> Nota: No formato GED (Total Active, Vertex/Tiler, Fragment),"
echo "   se Fragment estiver próximo de 95-100%, o gargalo é pixel/textura/AFBC."
echo ""

echo "-------------------------------------------------------------------"
echo "EVIDÊNCIA 3: VARIÁVEIS DE DEBUG/COMPILADOR ATIVAS NO PROCESSO"
echo "-------------------------------------------------------------------"
echo "${PROC_ENV:-Nenhuma variável PAN_MESA_DEBUG ou MESA_* injetada}"
echo ""

# -------------------------------------------------------------------
# TESTE 4: Amostragem de Syscalls (strace) em todas as threads do processo
# -------------------------------------------------------------------
STRACE_BIN=$(adb shell "if [ -x /data/local/tmp/strace ]; then echo /data/local/tmp/strace; else which strace 2>/dev/null; fi" | tr -d '\r')

echo "-------------------------------------------------------------------"
echo "EVIDÊNCIA 4: CONTAGEM DE IOCTLS / FUTEX NO PROCESSO (PID: $PID)"
echo "-------------------------------------------------------------------"
if [ -n "$STRACE_BIN" ]; then
  if adb shell "su -c 'id'" 2>/dev/null | grep -q "uid=0"; then
    adb shell "su -c 'timeout 2 $STRACE_BIN -f -c -p $PID 2>&1'" | grep -vE 'attached|detached' | head -n 20 | tr -d '\r'
  else
    adb shell "timeout 2 $STRACE_BIN -f -c -p $PID 2>&1" | tail -n 18 | tr -d '\r'
  fi
else
  echo "strace não disponível no aparelho. Coletando estado de espera (wchan) das threads:"
  adb shell "for t in /proc/$PID/task/*; do echo \"\$(cat \$t/comm 2>/dev/null): \$(cat \$t/wchan 2>/dev/null)\"; done | grep -E 'GPU|Vulkan|Render'" | tr -d '\r'
fi
