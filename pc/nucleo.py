"""Núcleo da app «Ligar ADB» do PC (sem interface): encontrar o adb, emparelhar por QR, encontrar a porta do telemóvel, ligar e religar,
o servidor que recebe o «estou aqui» da app do telemóvel e o leitor de QR. A interface (app.py) só chama isto.

Os QR (o mesmo formato na app Android):
  - emparelhar (o do próprio Android):  WIFI:T:ADB;S:<nome>;P:<código>;;   -> lido em «Depuração sem fios → Emparelhar com código QR»
  - do PC (a app do telemóvel lê):       ligaradb://pc?url=http://<ip-do-pc>:<porta>&chave=<chave>
  - do telemóvel (a webcam do PC lê):    ligaradb://tel?ip=<ip>&nome=<nome>
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import secrets
import shutil
import socket
import string
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SEM_JANELA = 0x08000000 if os.name == "nt" else 0
PASTA = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "LigarADB")
os.makedirs(PASTA, exist_ok=True)
CONFIG = os.path.join(PASTA, "aparelhos.json")
URL_PLATFORM_TOOLS = "https://dl.google.com/android/repository/platform-tools-latest-windows.zip"


# ---------------------------------------------------------------- adb ----------------------------------------------------------------
def encontrar_adb() -> str | None:
    """O adb do PATH, do Android SDK, ou o que esta app descarregou (pasta LigarADB/platform-tools)."""
    candidatos = [
        shutil.which("adb"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Android", "Sdk", "platform-tools", "adb.exe"),
        os.path.join(os.environ.get("ANDROID_HOME", ""), "platform-tools", "adb.exe"),
        os.path.join(PASTA, "platform-tools", "adb.exe"),
    ]
    for c in candidatos:
        if c and os.path.isfile(c):
            return c
    return None


def descarregar_adb(progresso=lambda t: None) -> str:
    """Descarrega as «Android SDK Platform-Tools» oficiais da Google para a pasta da app (só se o PC não tiver o adb)."""
    destino = os.path.join(PASTA, "platform-tools.zip")
    progresso("A descarregar as ferramentas do Android (Google)…")
    urllib.request.urlretrieve(URL_PLATFORM_TOOLS, destino)
    with zipfile.ZipFile(destino) as z:
        z.extractall(PASTA)
    os.remove(destino)
    adb = os.path.join(PASTA, "platform-tools", "adb.exe")
    if not os.path.isfile(adb):
        raise RuntimeError("o pacote da Google não trouxe o adb.exe")
    return adb


class Adb:
    def __init__(self, caminho: str):
        self.caminho = caminho
        self._ips: dict[str, str | None] = {}

    def correr(self, *args: str, tempo: float = 20) -> str:
        try:
            r = subprocess.run([self.caminho, *args], capture_output=True, text=True, timeout=tempo, creationflags=SEM_JANELA,
                               encoding="utf-8", errors="replace")
            return (r.stdout or "") + (r.stderr or "")
        except Exception as e:
            return f"erro: {e}"

    def aparelhos(self) -> list[dict]:
        """Os aparelhos ligados: [{serie, estado, modelo}]."""
        lista = []
        for linha in self.correr("devices", "-l").splitlines()[1:]:
            partes = linha.split()
            if len(partes) < 2:
                continue
            modelo = next((p.split(":", 1)[1] for p in partes if p.startswith("model:")), "")
            lista.append({"serie": partes[0], "estado": partes[1], "modelo": modelo.replace("_", " ")})
        return lista

    def ip_de(self, serie: str) -> str | None:
        """O IP de um aparelho. As ligações que o próprio adb faz pelo mDNS têm um nome («adb-…._adb-tls-connect._tcp»), não «ip:porta»."""
        m = re.match(r"(\d+\.\d+\.\d+\.\d+):\d+$", serie)
        if m:
            return m.group(1)
        if serie not in self._ips:
            r = self.correr("-s", serie, "shell", "ip -4 -o addr show wlan0", tempo=8)
            m = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", r)
            self._ips[serie] = m.group(1) if m else None
        return self._ips[serie]

    def ligado(self, ip: str) -> str | None:
        for a in self.aparelhos():
            if a["estado"] == "device" and self.ip_de(a["serie"]) == ip:
                return a["serie"]
        return None

    def limpar_mortos(self, ip: str) -> None:
        for a in self.aparelhos():
            if a["serie"].startswith(ip + ":") and a["estado"] != "device":
                self.correr("disconnect", a["serie"])

    def mdns(self) -> str:
        return self.correr("mdns", "services")


# ------------------------------------------------------------ rede e portas ------------------------------------------------------------
def ip_do_pc() -> str:
    """O IP do PC na rede local (a interface por onde sai o tráfego)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def portas_abertas(ip: str, de: int = 30000, ate: int = 50000) -> list[int]:
    """As portas TCP abertas no telemóvel na gama que o Android usa para a depuração sem fios (cerca de 3 s)."""
    async def tenta(p, sem, abertas):
        async with sem:
            try:
                _, w = await asyncio.wait_for(asyncio.open_connection(ip, p), 1.2)  # Wi-Fi lento: 0,4 s perdia portas
                abertas.append(p)
                w.close()
            except Exception:
                pass

    async def tudo():
        sem, abertas = asyncio.Semaphore(3000), []
        await asyncio.gather(*(tenta(p, sem, abertas) for p in range(de, ate)))
        return sorted(abertas)

    return asyncio.run(tudo())


def ligar(adb: Adb, ip: str, aviso=lambda t: None) -> str | None:
    """Liga o ADB ao telemóvel neste IP (já emparelhado). Devolve a série «ip:porta» ou None."""
    ja = adb.ligado(ip)
    if ja:
        return ja
    adb.limpar_mortos(ip)
    candidatos = []
    m = re.findall(r"_adb-tls-connect\S*\s+(\d+\.\d+\.\d+\.\d+:\d+)", adb.mdns())
    candidatos += [c for c in m if c.startswith(ip + ":")]
    if not candidatos:
        aviso(f"A procurar a porta do ADB em {ip}…")
        candidatos = [f"{ip}:{p}" for p in portas_abertas(ip)]
    for alvo in candidatos:
        if "connected to" in adb.correr("connect", alvo, tempo=15):
            for _ in range(12):  # logo a seguir a ligar passa uns instantes por «offline»
                if adb.ligado(ip):
                    lembrar(ip)
                    return alvo
                time.sleep(0.5)
        adb.correr("disconnect", alvo)
    return None


# -------------------------------------------------------- aparelhos conhecidos --------------------------------------------------------
def conhecidos() -> list[str]:
    try:
        return json.load(open(CONFIG, encoding="utf-8")).get("ips", [])
    except Exception:
        return []


def lembrar(ip: str) -> None:
    ips = [i for i in conhecidos() if i != ip]
    json.dump({"ips": [ip] + ips[:9]}, open(CONFIG, "w", encoding="utf-8"))


# ------------------------------------------------------------- emparelhar -------------------------------------------------------------
def novo_emparelhamento() -> tuple[str, str, str]:
    """(nome, código, texto do QR) para «Emparelhar dispositivo com código QR» do Android."""
    nome = "ligaradb-" + "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
    codigo = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
    return nome, codigo, f"WIFI:T:ADB;S:{nome};P:{codigo};;"


def esperar_emparelhamento(adb: Adb, nome: str, codigo: str, parar: threading.Event, aviso=lambda t: None, tempo: float = 300) -> str | None:
    """Espera que o telemóvel leia o QR (aparece no mDNS com o nome do QR), emparelha e liga. Devolve a série ligada ou None."""
    fim = time.time() + tempo
    while time.time() < fim and not parar.is_set():
        m = re.search(re.escape(nome) + r"\S*\s+_adb-tls-pairing\S*\s+(\d+\.\d+\.\d+\.\d+):(\d+)", adb.mdns())
        if m:
            ip, porta = m.group(1), m.group(2)
            aviso("Telemóvel encontrado. A emparelhar…")
            r = adb.correr("pair", f"{ip}:{porta}", codigo, tempo=30)
            if "Successfully paired" not in r:
                aviso("O emparelhamento falhou: " + r.strip()[:120])
                return None
            aviso("Emparelhado. A ligar…")
            return ligar(adb, ip, aviso)
        time.sleep(1.5)
    return None


# --------------------------------------------------- servidor: «estou aqui» do telemóvel ---------------------------------------------------
class ServidorPc:
    """Recebe POST /ola da app do telemóvel (depois de ela ler o QR do PC) e liga o ADB a esse IP."""

    def __init__(self, adb: Adb, aviso=lambda t: None, porta: int = 38180):
        self.adb, self.aviso, self.chave = adb, aviso, secrets.token_urlsafe(9)
        servidor = self

        class Pedido(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                if self.path != "/ola":
                    return self._responder(404, "não existe")
                try:
                    dados = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0) or 0)) or b"{}")
                except Exception:
                    return self._responder(400, "pedido inválido")
                if dados.get("chave") != servidor.chave:
                    return self._responder(403, "QR antigo: leia o QR que está agora no PC")
                ip = str(dados.get("ip", ""))
                if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", ip):
                    return self._responder(400, "IP inválido")
                servidor.aviso(f"{dados.get('nome') or 'Telemóvel'} ({ip}) pediu para ligar…")
                serie = ligar(servidor.adb, ip, servidor.aviso)
                if serie:
                    servidor.aviso(f"Ligado: {serie}")
                    return self._responder(200, f"Ligado ao PC ({serie}).")
                return self._responder(409, "O PC não encontrou o ADB: ligue a «Depuração sem fios» e, se for a 1.ª vez, emparelhe pelo QR de emparelhamento.")

            def _responder(self, codigo, mensagem):
                corpo = json.dumps({"mensagem": mensagem}, ensure_ascii=False).encode()
                self.send_response(codigo)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

        for p in range(porta, porta + 20):  # a primeira porta livre
            try:
                self.http = ThreadingHTTPServer(("0.0.0.0", p), Pedido)
                self.porta = p
                break
            except OSError:
                continue
        threading.Thread(target=self.http.serve_forever, daemon=True).start()

    def qr(self) -> str:
        url = f"http://{ip_do_pc()}:{self.porta}"
        return "ligaradb://pc?" + urllib.parse.urlencode({"url": url, "chave": self.chave})


# ------------------------------------------------------------- ler QR -------------------------------------------------------------
def ler_qr_do_telemovel(texto: str) -> dict | None:
    """«ligaradb://tel?ip=…&nome=…» -> {ip, nome}."""
    if not texto.startswith("ligaradb://tel?"):
        return None
    q = dict(urllib.parse.parse_qsl(texto.split("?", 1)[1]))
    if not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", q.get("ip", "")):
        return None
    return {"ip": q["ip"], "nome": q.get("nome", "")}


def decodificar(imagem) -> str | None:
    """Lê um QR de uma imagem (BGR do OpenCV). Devolve o texto ou None."""
    import cv2
    texto, _, _ = cv2.QRCodeDetector().detectAndDecode(imagem)
    return texto or None


def ler_pela_webcam(parar: threading.Event, tempo: float = 60) -> str | None:
    """Abre a webcam numa janela e devolve o primeiro QR da app do telemóvel que vir (ou None ao fim do tempo / Esc)."""
    import cv2
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW if os.name == "nt" else 0)
    if not cam.isOpened():
        return None
    fim, achado = time.time() + tempo, None
    try:
        while time.time() < fim and not parar.is_set():
            ok, quadro = cam.read()
            if not ok:
                continue
            texto = decodificar(quadro)
            cv2.imshow("Ligar ADB - mostre o QR do telemovel (Esc para sair)", quadro)
            if texto and ler_qr_do_telemovel(texto):
                achado = texto
                break
            if cv2.waitKey(1) == 27:
                break
    finally:
        cam.release()
        cv2.destroyAllWindows()
    return achado


# ------------------------------------------------------- app do telemóvel -------------------------------------------------------
PACOTE = "app.ligaradb"


def apk_incluido() -> str | None:
    """O APK da app Android, que vem junto com esta app (pasta do executável)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    c = os.path.join(base, "LigarADB.apk")
    return c if os.path.isfile(c) else None


def preparar_telemovel(adb: Adb, serie: str) -> str:
    """Instala a app Android (se faltar) e dá-lhe a autorização para ligar a depuração sem fios com um toque."""
    if PACOTE not in adb.correr("-s", serie, "shell", "pm", "list", "packages", PACOTE):
        apk = apk_incluido()
        if not apk:
            return "Não encontrei o APK junto da app."
        r = adb.correr("-s", serie, "install", "-r", apk, tempo=180)
        if "Success" not in r:
            return "A instalação falhou: " + r.strip()[:160]
    r = adb.correr("-s", serie, "shell", "pm", "grant", PACOTE, "android.permission.WRITE_SECURE_SETTINGS")
    if r.strip():
        return "Não consegui autorizar: " + r.strip()[:160]
    return "Pronto: a app «Ligar ADB» do telemóvel já liga a depuração sem fios com um toque."
