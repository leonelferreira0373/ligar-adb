# Guia de uso — Ligar ADB

Liga um telemóvel Android ao ADB de um PC Windows **sem cabo**, por QR, e mantém a ligação sozinha, mesmo depois de reiniciar o
telemóvel.

## Índice

1. [O que é preciso](#1-o-que-é-preciso)
2. [Instalar](#2-instalar)
3. [Primeira vez: emparelhar](#3-primeira-vez-emparelhar)
4. [Preparar o telemóvel (uma vez)](#4-preparar-o-telemóvel-uma-vez)
5. [Dia a dia](#5-dia-a-dia)
6. [A janela do PC, botão a botão](#6-a-janela-do-pc-botão-a-botão)
7. [A app do telemóvel, botão a botão](#7-a-app-do-telemóvel-botão-a-botão)
8. [Automático: o que acontece sozinho](#8-automático-o-que-acontece-sozinho)
9. [Problemas e soluções](#9-problemas-e-soluções)
10. [Segurança](#10-segurança)
11. [Desinstalar](#11-desinstalar)
12. [Perguntas frequentes](#12-perguntas-frequentes)

---

## 1. O que é preciso

- **PC** com Windows 10 ou 11.
- **Telemóvel** com Android 11 ou mais recente (é a partir do 11 que existe a «Depuração sem fios»).
- PC e telemóvel na **mesma rede Wi-Fi** (no PC também serve por cabo de rede, desde que seja a mesma rede).
- Não é preciso o Android Studio. Se o PC não tiver o ADB, a app oferece-se para descarregar as ferramentas oficiais da Google
  (Android SDK Platform-Tools, cerca de 7 MB).

## 2. Instalar

Descarregue os dois ficheiros da página [Releases](https://github.com/leonelferreira0373/ligar-adb/releases):

| Ficheiro | Onde | Como |
|---|---|---|
| `LigarADB.exe` | PC | Não precisa de instalação: guarde-o numa pasta (por exemplo `Documentos\LigarADB`) e abra-o. |
| `LigarADB.apk` | Telemóvel | Opcional: o botão «Preparar o telemóvel» da app do PC instala-o sozinho. À mão: copie para o telemóvel, abra e permita «instalar apps desconhecidas». |

**Firewall do Windows:** na primeira vez que abrir o `LigarADB.exe`, o Windows pode perguntar se deixa a app comunicar na rede.
Escolha **Redes privadas** e aceite. Sem isto, a app do telemóvel não consegue avisar o PC (o resto funciona).

**Aviso do SmartScreen:** como o `.exe` não está assinado por uma empresa, o Windows pode mostrar «O Windows protegeu o seu PC». Clique
em «Mais informações» → «Executar mesmo assim».

## 3. Primeira vez: emparelhar

Faz-se **uma só vez** por par telemóvel/PC.

1. **Ativar as Opções de programador** (se ainda não estiverem): Definições → Acerca do telemóvel → toque **7 vezes** em «Número de
   compilação».
2. Definições → Sistema → **Opções de programador** → **Depuração sem fios** → ligar. Se perguntar «Permitir a depuração sem fios
   nesta rede?», marque **Permitir sempre nesta rede** e aceite.
3. Ainda em «Depuração sem fios», toque em **Emparelhar dispositivo com código QR**.
4. No PC, abra o `LigarADB.exe` e aponte o telemóvel ao QR do cartão **«1.ª vez: emparelhar»**.
5. Em poucos segundos o cartão diz «Emparelhado. A ligar…» e depois «Ligado: …». O telemóvel aparece em **«Ligados agora»** no topo.

Se o QR não for lido a tempo, carregue em **Novo QR** e repita o passo 3.

## 4. Preparar o telemóvel (uma vez)

Com o telemóvel ligado (passo 3):

1. No PC, carregue em **«Preparar o telemóvel (instalar a app e autorizar o toque)»**. A app do PC:
   - instala a app «Ligar ADB» no telemóvel (se ainda não estiver);
   - dá-lhe a autorização especial `WRITE_SECURE_SETTINGS`, que é o que lhe permite **ligar a depuração sem fios sozinha**. Nenhuma
     app a pode pedir; só o ADB a pode dar, e é por isso que este passo é feito pelo PC.
2. No telemóvel, abra a app **Ligar ADB** e ligue **«Manter a depuração sem fios sempre ligada»**.
3. (Opcional) No PC, marque **«Arrancar com o Windows»**: a app passa a abrir minimizada sempre que liga o PC.

A partir daqui não é preciso fazer mais nada.

## 5. Dia a dia

Normalmente: **nada**. Ligue o PC e o telemóvel, e em menos de um minuto o telemóvel aparece em «Ligados agora» (ou em `adb devices`).

Se alguma vez precisar de forçar a ligação, há três caminhos, todos no cartão **«Dia a dia: ligar»**:

| Caminho | Como |
|---|---|
| **O telemóvel lê o QR do PC** | Na app do telemóvel: «Ler o QR do PC». Ou abra a **câmara normal** do telemóvel e aponte ao QR: o link `ligaradb://` abre a app sozinho. A app liga a depuração e avisa o PC, que liga o ADB. A app mostra «Ligado ao PC». |
| **O PC lê o QR do telemóvel** | Na app do telemóvel: «Mostrar o meu QR». No PC: «Ler o QR do telemóvel (webcam)» e mostre o ecrã do telemóvel à webcam. |
| **Pelo IP** | No PC: «Ligar pelo IP…» e escreva o IP que a app do telemóvel mostra (por exemplo `192.168.0.200`). |

Depois de ligado, use o ADB como sempre: `adb devices`, `adb shell`, Android Studio, scrcpy, etc.

## 6. A janela do PC, botão a botão

| Parte | O que faz |
|---|---|
| **Ligados agora** | Os aparelhos ligados ao ADB, actualizado a cada 4 segundos. |
| **1.ª vez: emparelhar** | O QR de emparelhamento do próprio Android. Fica à espera do telemóvel; quando ele lê o QR, emparelha e liga. **Novo QR** gera outro (com outro código). |
| **Dia a dia: ligar** | O QR do PC (para a app do telemóvel ou a câmara), o leitor do QR do telemóvel pela webcam e «Ligar pelo IP…». |
| **Preparar o telemóvel** | Instala a app Android e dá-lhe a autorização para ligar a depuração sozinha. |
| **Religar sozinho** | A cada 30 segundos, volta a ligar os telemóveis que já estiveram ligados (a porta muda sempre que a depuração liga; a app encontra-a). |
| **Arrancar com o Windows** | Cria/remove o atalho na pasta Arranque: a app abre minimizada ao iniciar sessão. |
| Linha de baixo | Mensagens: o que a app está a fazer, ou o que falhou e porquê. |

## 7. A app do telemóvel, botão a botão

| Parte | O que faz |
|---|---|
| **Estado** | Wi-Fi e IP, Opções de programador, Depuração sem fios, e «Ligar com um toque» (se já tem a autorização do PC). |
| **Ligar/Desligar a depuração sem fios** | Com a autorização: liga/desliga logo. Sem ela: abre o ecrã das definições certo. |
| **Ler o QR do PC** | Abre a câmara; ao ler o QR do PC, liga a depuração (se puder) e avisa o PC. Mostra a resposta. |
| **Mostrar o meu QR** | O QR deste telemóvel (IP e nome), para a webcam do PC. |
| **Manter a depuração sem fios sempre ligada** | Se o Android a desligar (ao reiniciar, ou quando o PC corta a ligação), a app volta a ligá-la logo. |
| **Botão «ADB sem fios» nas definições rápidas** | Puxe o painel de cima → lápis (editar) → arraste «ADB sem fios» para os botões. Um toque liga/desliga. |

## 8. Automático: o que acontece sozinho

- **O Android desliga a depuração sem fios** sempre que o telemóvel **reinicia** e, em muitos telemóveis, quando o PC **corta a
  ligação** ou o telemóvel **muda de rede**. Com «Manter sempre ligada», a app vigia a definição e volta a ligá-la. Não há
  notificação permanente nem gasto de bateria: o próprio Android acorda a app quando a definição muda.
- **A porta muda** de cada vez. A app do PC encontra-a (pelo anúncio do ADB na rede ou procurando as portas 30000–50000, cerca de 10 s)
  e liga.
- **Medido** (Unitel SMART 4G II, Android 15): depois de reiniciar o telemóvel, a rede voltou aos 32 s, a app ligou a depuração aos 71 s
  e o PC estava ligado aos 74 s, sem tocar em nada.
- Em telemóveis com cifra (todos os recentes), a app só pode correr depois do **primeiro desbloqueio** a seguir ao reinício: se tiver
  PIN, desbloqueie uma vez.

## 9. Problemas e soluções

| Sintoma | Causa provável | Solução |
|---|---|---|
| O cartão «1.ª vez» fica em «À espera do telemóvel…» | Telemóvel e PC em redes diferentes, ou o telemóvel não leu o QR | Mesma rede Wi-Fi (atenção a redes de convidados e a dados móveis). Carregue em «Novo QR» e leia-o em «Emparelhar dispositivo com código QR». |
| «Não encontrei o ADB em …» | A depuração sem fios está desligada, ou o telemóvel nunca foi emparelhado com este PC | Ligue-a (app do telemóvel ou definições). Se for a 1.ª vez neste PC, emparelhe (secção 3). |
| A app do telemóvel diz «Não consegui falar com o PC» | Firewall do Windows a bloquear, ou redes diferentes | Painel de Controlo → Firewall do Windows → Permitir uma app → `LigarADB.exe` em **Privada**. Confirme que o Wi-Fi do PC está como **rede privada**. |
| A app do telemóvel diz «QR antigo» | Leu um QR de uma janela que já foi fechada | Leia o QR que está agora no PC. |
| «Ligar com um toque: falta autorização do PC» | A autorização não foi dada (ou a app foi reinstalada) | Ligue o ADB e carregue em «Preparar o telemóvel» no PC. |
| Depois de reiniciar o telemóvel, nada liga | O telemóvel ainda não foi desbloqueado, ou o «Manter sempre ligada» está desligado | Desbloqueie uma vez; confirme o interruptor na app. |
| O telemóvel não aparece por **cabo USB** (nem o pedido de depuração) | Cabo só de carga, porta USB, ou modo USB «só carregar» | Outro cabo (de dados), outra porta, e na notificação USB escolha «Transferência de ficheiros». Esta app não precisa de cabo. |
| A webcam não abre | Outra app a usar a câmara, ou sem permissão do Windows | Feche a outra app; Definições → Privacidade → Câmara → permitir apps de ambiente de trabalho. Alternativa: o telemóvel lê o QR do PC. |
| `adb devices` mostra um nome estranho (`adb-…._adb-tls-connect._tcp`) | O próprio ADB ligou pelo anúncio na rede | Está ligado e funciona; é só outro nome. |

## 10. Segurança

- O ADB sem fios só aceita PCs **emparelhados** (chaves criptográficas trocadas no passo 3). Outro PC na mesma rede não entra.
- «Manter sempre ligada» deixa a depuração ligada em redes Wi-Fi onde a tiver permitido. Em redes públicas ou desconhecidas,
  desligue-a (botão na app ou nas definições rápidas).
- Para retirar o acesso a um PC: Opções de programador → **Depuração sem fios** → toque no PC em «Dispositivos emparelhados» →
  Esquecer. Ou «Revogar autorizações de depuração USB».
- A app do PC só ouve na rede local (porta 38180 ou seguinte) e só aceita o pedido de um telemóvel que tenha lido o QR actual
  (chave aleatória, nova a cada abertura).
- O código é aberto (MIT): pode ler tudo em [github.com/leonelferreira0373/ligar-adb](https://github.com/leonelferreira0373/ligar-adb).

## 11. Desinstalar

- **PC:** desmarque «Arrancar com o Windows», feche a app e apague o `LigarADB.exe`. Os dados da app estão em
  `%LOCALAPPDATA%\LigarADB` (lista de telemóveis e, se a app o descarregou, o ADB): pode apagar a pasta.
- **Telemóvel:** desinstale a app «Ligar ADB» como qualquer outra. A autorização especial desaparece com ela.

## 12. Perguntas frequentes

**Porque é que a app não emparelha sozinha, sem o QR do Android?**
Por segurança, só o próprio Android pode emparelhar um PC. A app do PC mostra o QR no formato do Android e trata do resto.

**Funciona com mais do que um telemóvel?**
Sim. Emparelhe cada um (secção 3); a app do PC lembra-se dos últimos 10 e religa todos.

**E com o Android Studio / scrcpy?**
Sim: depois de ligado, o telemóvel é um aparelho ADB normal.

**O IP do telemóvel muda.**
A app do PC procura o telemóvel pelo anúncio do ADB na rede e pela lista de IPs que já conheceu. Se o router mudar o IP com frequência,
reserve um IP fixo para o telemóvel no router (DHCP reservation).
