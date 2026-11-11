"""«Ligar ADB» para Windows: liga um telemóvel Android ao ADB sem cabo, por QR.

Uma janela, de cima para baixo, pela ordem em que se usa:
  1. Aparelhos ligados agora.
  2. Primeira vez: o QR de EMPARELHAMENTO do Android (lido em Depuração sem fios → Emparelhar com código QR). Emparelha e liga sozinha.
  3. Dia a dia: o QR do PC (lido pela app «Ligar ADB» do telemóvel, ou pela câmara normal) e o leitor pela webcam do QR do telemóvel.
  4. Preparar o telemóvel: instala a app Android e dá-lhe a autorização de ligar a depuração com um toque.
  5. Religar sozinho (aparelhos já ligados antes) e arrancar com o Windows.
"""
from __future__ import annotations

import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import qrcode
from PIL import ImageTk

import nucleo

FUNDO, TINTA, SUAVE, LINHA = "#FDFDFD", "#0A0A0A", "#727272", "#DFDFDF"
ARRANQUE = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "Ligar ADB.vbs")


def imagem_qr(texto: str, lado: int = 210) -> ImageTk.PhotoImage:
    img = qrcode.make(texto, box_size=8, border=2).convert("RGB").resize((lado, lado))
    return ImageTk.PhotoImage(img)


class App(tk.Tk):
    def __init__(self, adb: nucleo.Adb, oculto: bool):
        super().__init__()
        self.adb = adb
        self.title("Ligar ADB")
        self.configure(bg=FUNDO)
        self.parar = threading.Event()
        self.estilo()

        self.servidor = nucleo.ServidorPc(adb, aviso=self.avisar)
        self.nome, self.codigo, self.qr_par = nucleo.novo_emparelhamento()

        topo = tk.Frame(self, bg=FUNDO)
        topo.pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(topo, text="Ligar ADB", font=("Segoe UI", 24, "bold"), bg=FUNDO, fg=TINTA).pack(anchor="w")
        tk.Label(topo, text="Liga o telemóvel ao ADB sem cabo. PC e telemóvel na mesma rede Wi-Fi.", font=("Segoe UI", 10), bg=FUNDO, fg=SUAVE).pack(anchor="w")

        self.lista = tk.Label(self, text="", font=("Segoe UI", 11), bg="white", fg=TINTA, anchor="w", justify="left", padx=14, pady=10)
        self.lista.pack(fill="x", padx=24)

        corpo = tk.Frame(self, bg=FUNDO)
        corpo.pack(fill="both", expand=True, padx=24, pady=12)
        corpo.columnconfigure((0, 1), weight=1, uniform="c")

        # --- 1.ª vez: emparelhar
        c1 = self.cartao(corpo, 0, "1.ª vez: emparelhar",
                         "No telemóvel: Opções de programador → Depuração sem fios → Emparelhar dispositivo com código QR. Leia este QR.")
        self.img_par = imagem_qr(self.qr_par)
        self.lbl_par = tk.Label(c1, image=self.img_par, bg="white")
        self.lbl_par.pack(pady=6)
        self.estado_par = tk.Label(c1, text="À espera do telemóvel…", font=("Segoe UI", 10), bg="white", fg=SUAVE, wraplength=360, justify="left")
        self.estado_par.pack(anchor="w")
        ttk.Button(c1, text="Novo QR", command=self.novo_par).pack(anchor="w", pady=(6, 0))

        # --- dia a dia: QR do PC e webcam
        c2 = self.cartao(corpo, 1, "Dia a dia: ligar",
                         "Na app «Ligar ADB» do telemóvel: «Ler o QR do PC» (ou aponte a câmara normal). Ou mostre o QR do telemóvel à webcam.")
        self.img_pc = imagem_qr(self.servidor.qr())
        tk.Label(c2, image=self.img_pc, bg="white").pack(pady=6)
        ttk.Button(c2, text="Ler o QR do telemóvel (webcam)", command=self.webcam).pack(anchor="w")
        ttk.Button(c2, text="Ligar pelo IP…", command=self.pelo_ip).pack(anchor="w", pady=(6, 0))

        # --- rodapé: preparar, automático, avisos
        baixo = tk.Frame(self, bg=FUNDO)
        baixo.pack(fill="x", padx=24, pady=(0, 16))
        ttk.Button(baixo, text="Preparar o telemóvel (instalar a app e autorizar o toque)", command=self.preparar).pack(side="left")
        self.auto = tk.BooleanVar(value=True)
        ttk.Checkbutton(baixo, text="Religar sozinho", variable=self.auto).pack(side="left", padx=16)
        self.arranque = tk.BooleanVar(value=os.path.exists(ARRANQUE))
        ttk.Checkbutton(baixo, text="Arrancar com o Windows", variable=self.arranque, command=self.mudar_arranque).pack(side="left")
        self.aviso = tk.Label(self, text="", font=("Segoe UI", 10), bg=FUNDO, fg=TINTA, anchor="w", wraplength=840, justify="left")
        self.aviso.pack(fill="x", padx=24, pady=(0, 12))

        self.protocol("WM_DELETE_WINDOW", self.sair)
        threading.Thread(target=self.esperar_par, daemon=True).start()
        threading.Thread(target=self.vigiar, daemon=True).start()
        self.atualizar_lista()
        # a janela mede-se pelo conteúdo (com a escala do Windows a 125 % ou 150 % nada fica cortado)
        self.update_idletasks()
        self.minsize(self.winfo_reqwidth(), self.winfo_reqheight())
        if oculto:
            self.iconify()

    # ---------------- aparência
    def estilo(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TButton", font=("Segoe UI", 10), padding=(14, 8), background="white", foreground=TINTA, bordercolor=LINHA)
        s.configure("TCheckbutton", font=("Segoe UI", 10), background=FUNDO, foreground=TINTA)

    def cartao(self, pai, coluna, titulo, texto):
        f = tk.Frame(pai, bg="white", highlightbackground=LINHA, highlightthickness=1, padx=16, pady=14)
        f.grid(row=0, column=coluna, sticky="nsew", padx=(0, 12) if coluna == 0 else (12, 0))
        tk.Label(f, text=titulo, font=("Segoe UI", 14, "bold"), bg="white", fg=TINTA).pack(anchor="w")
        tk.Label(f, text=texto, font=("Segoe UI", 10), bg="white", fg=SUAVE, wraplength=360, justify="left").pack(anchor="w", pady=(4, 0))
        return f

    # ---------------- avisos (de qualquer thread)
    def avisar(self, texto: str):
        self.after(0, lambda: self.aviso.config(text=texto))

    def atualizar_lista(self):
        def ler():
            aps = self.adb.aparelhos()
            txt = "Ligados agora: " + (", ".join(f"{a['modelo'] or a['serie']} ({a['serie']})" for a in aps if a["estado"] == "device") or "nenhum")
            self.after(0, lambda: self.lista.config(text=txt))
        threading.Thread(target=ler, daemon=True).start()
        if not self.parar.is_set():
            self.after(4000, self.atualizar_lista)

    # ---------------- emparelhar
    def esperar_par(self):
        nome, codigo = self.nome, self.codigo
        serie = nucleo.esperar_emparelhamento(self.adb, nome, codigo, self.parar,
                                              aviso=lambda t: self.after(0, lambda: self.estado_par.config(text=t)), tempo=3600)
        if nome != self.nome:  # entretanto pediu-se um QR novo
            return
        texto = f"Ligado: {serie}" if serie else "Não apareceu nenhum telemóvel. Carregue em «Novo QR» e tente outra vez."
        self.after(0, lambda: self.estado_par.config(text=texto))

    def novo_par(self):
        self.nome, self.codigo, self.qr_par = nucleo.novo_emparelhamento()
        self.img_par = imagem_qr(self.qr_par)
        self.lbl_par.config(image=self.img_par)
        self.estado_par.config(text="À espera do telemóvel…")
        threading.Thread(target=self.esperar_par, daemon=True).start()

    # ---------------- dia a dia
    def webcam(self):
        def ler():
            self.avisar("A abrir a webcam… mostre o QR da app do telemóvel («Mostrar o meu QR»).")
            texto = nucleo.ler_pela_webcam(self.parar)
            tel = nucleo.ler_qr_do_telemovel(texto) if texto else None
            if not tel:
                return self.avisar("Não li nenhum QR do telemóvel (ou não há webcam).")
            self.ligar_ip(tel["ip"], tel["nome"])
        threading.Thread(target=ler, daemon=True).start()

    def pelo_ip(self):
        janela = tk.Toplevel(self, bg=FUNDO, padx=16, pady=16)
        janela.title("Ligar pelo IP")
        tk.Label(janela, text="IP do telemóvel (aparece na app «Ligar ADB»):", bg=FUNDO).pack(anchor="w")
        e = ttk.Entry(janela, width=24)
        e.pack(anchor="w", pady=8)
        e.focus()
        ttk.Button(janela, text="Ligar", command=lambda: (self.ligar_ip(e.get().strip(), ""), janela.destroy())).pack(anchor="w")

    def ligar_ip(self, ip: str, nome: str):
        def ir():
            self.avisar(f"A ligar a {nome or ip}…")
            serie = nucleo.ligar(self.adb, ip, self.avisar)
            self.avisar(f"Ligado: {serie}" if serie else f"Não encontrei o ADB em {ip}. A «Depuração sem fios» está ligada? Já emparelhou este telemóvel?")
        threading.Thread(target=ir, daemon=True).start()

    def preparar(self):
        aps = [a for a in self.adb.aparelhos() if a["estado"] == "device"]
        if not aps:
            return messagebox.showinfo("Ligar ADB", "Ligue primeiro o telemóvel (emparelhar ou QR).")
        def ir():
            for a in aps:
                self.avisar(f"A preparar {a['modelo'] or a['serie']}…")
                self.avisar(nucleo.preparar_telemovel(self.adb, a["serie"]))
        threading.Thread(target=ir, daemon=True).start()

    # ---------------- automático
    def vigiar(self):
        """A cada 30 s, religa os telemóveis que já estiveram ligados (a porta muda sempre que a depuração liga)."""
        while not self.parar.wait(30):
            if not self.auto.get():
                continue
            for ip in nucleo.conhecidos():
                if not self.adb.ligado(ip):
                    serie = nucleo.ligar(self.adb, ip)
                    if serie:
                        self.avisar(f"Religado sozinho: {serie}")

    def mudar_arranque(self):
        if self.arranque.get():
            exe = sys.executable if getattr(sys, "frozen", False) else f'{sys.executable.replace("python.exe", "pythonw.exe")}" "{os.path.abspath(__file__)}'
            with open(ARRANQUE, "w", encoding="utf-8") as f:
                f.write(f'CreateObject("WScript.Shell").Run """{exe}"" --oculto", 0, False\n')
        elif os.path.exists(ARRANQUE):
            os.remove(ARRANQUE)

    def sair(self):
        self.parar.set()
        self.destroy()


def main():
    if os.name == "nt":  # nítido em ecrãs com escala (125 %, 150 %): o Windows não estica a janela
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    caminho = nucleo.encontrar_adb()
    if not caminho:
        raiz = tk.Tk()
        raiz.withdraw()
        if not messagebox.askyesno("Ligar ADB", "Este PC não tem o ADB (Android Platform-Tools).\nDescarregar agora as ferramentas oficiais da Google (cerca de 7 MB)?"):
            return
        caminho = nucleo.descarregar_adb()
        raiz.destroy()
    adb = nucleo.Adb(caminho)
    adb.correr("start-server", tempo=30)
    App(adb, oculto="--oculto" in sys.argv).mainloop()


if __name__ == "__main__":
    main()
