"""Testes de ponta a ponta com um telemóvel real ligado (adb sem fios). Correr: python testes_ponta_a_ponta.py
1. QR do PC: gerar -> ler (OpenCV) -> igual; e a app Android interpreta-o (link ligaradb://pc).
2. QR do telemóvel: a app mostra-o, captura-se o ecrã do telemóvel, o PC lê-o como leria pela webcam -> IP certo.
3. Fluxo «o telemóvel avisa o PC»: desliga-se o ADB, a app do telemóvel abre o link do QR do PC, avisa o servidor do PC, e o PC volta
   a ligar o ADB sozinho (procurando a porta).
"""
import os
import re
import subprocess
import sys
import time

import cv2
import numpy as np
import qrcode

import nucleo

ok = lambda nome: print(f"  OK  {nome}")


def falha(nome, info=""):
    print(f"  FALHOU  {nome} {info}")
    sys.exit(1)


adb = nucleo.Adb(nucleo.encontrar_adb())
tel = next((a for a in adb.aparelhos() if a["estado"] == "device" and adb.ip_de(a["serie"])), None)
if not tel:
    falha("há um telemóvel ligado sem fios", "(ligue a Depuração sem fios)")
serie, ip = tel["serie"], adb.ip_de(tel["serie"])
print(f"telemóvel: {tel['modelo']} {serie}")

# 1) QR do PC
srv = nucleo.ServidorPc(adb, aviso=lambda t: print("     servidor:", t))
texto = srv.qr()
img = np.array(qrcode.make(texto, box_size=8, border=2).convert("RGB"))[:, :, ::-1].copy()
if nucleo.decodificar(img) != texto:
    falha("QR do PC lido de volta")
ok(f"QR do PC gera e lê-se: {texto}")

# 2) QR do telemóvel: abrir a app, carregar em «Mostrar o meu QR», capturar o ecrã e ler
adb.correr("-s", serie, "shell", "am", "start", "-n", "app.ligaradb/.MainActivity")
time.sleep(2.5)
xml = adb.correr("-s", serie, "exec-out", "uiautomator", "dump", "/dev/tty")
m = re.search(r'text="Mostrar o meu QR[^"]*"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml)
if m:  # (se já estiver à vista, o botão diz «Esconder o meu QR»)
    x, y = (int(m.group(1)) + int(m.group(3))) // 2, (int(m.group(2)) + int(m.group(4))) // 2
    adb.correr("-s", serie, "shell", "input", "tap", str(x), str(y))
elif "Esconder o meu QR" not in xml:
    falha("encontrar o botão «Mostrar o meu QR»")
time.sleep(1.5)
adb.correr("-s", serie, "shell", "input", "swipe", "360", "1300", "360", "500", "300")  # o QR fica por baixo: subir
time.sleep(1.2)
png = subprocess.run([adb.caminho, "-s", serie, "exec-out", "screencap", "-p"], capture_output=True, creationflags=nucleo.SEM_JANELA).stdout
ecra = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
cv2.imwrite(os.path.join(os.path.dirname(__file__), "teste_qr_do_telemovel.png"), ecra)
lido = nucleo.decodificar(ecra)
info = nucleo.ler_qr_do_telemovel(lido or "")
if not info or info["ip"] != ip:
    falha("QR do telemóvel lido pelo PC", f"(lido: {lido!r})")
ok(f"QR do telemóvel lido pelo PC (como pela webcam): {info}")

# 3a) a app do telemóvel recebe o QR do PC (como link, igual ao que a câmara faria), avisa o PC e mostra a resposta
recebidos = []
srv.aviso = lambda t: (recebidos.append(t), print("     servidor:", t))
adb.correr("-s", serie, "shell", "am", "start", "-a", "android.intent.action.VIEW", "-d", f'"{texto}"')
fim = time.time() + 30
resposta = ""
while time.time() < fim and "Ligado ao PC" not in resposta:
    time.sleep(1.5)
    xml = adb.correr("-s", serie, "exec-out", "uiautomator", "dump", "/dev/tty")
    m = re.search(r'text="(Ligado ao PC[^"]*|Não consegui[^"]*|O PC não[^"]*)"', xml)
    resposta = m.group(1) if m else ""
if not any("pediu para ligar" in r for r in recebidos):
    falha("o servidor do PC recebeu o aviso da app")
if "Ligado ao PC" not in resposta:
    falha("a app mostra a resposta do PC", f"(vê: {resposta!r})")
ok(f"a app avisou o PC e mostra a resposta: «{resposta}»")

# 3b) o ADB cai e o PC volta a ligar sozinho (procura a porta nova do telemóvel)
for a in adb.aparelhos():
    if adb.ip_de(a["serie"]) == ip:
        adb.correr("disconnect", a["serie"])
time.sleep(1)
if adb.ligado(ip):
    falha("desligar o ADB para o teste")
serie2 = nucleo.ligar(adb, ip, aviso=lambda t: print("     ", t))
if not serie2 or not adb.ligado(ip):
    falha("o PC religa sozinho")
ok(f"o PC religou sozinho: {serie2}")
print("tudo OK")
