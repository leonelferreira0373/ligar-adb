# Ligar ADB

Liga um telemóvel Android ao ADB de um PC Windows **sem cabo**, por QR, e mantém a ligação sozinha.

> **English:** Connect an Android phone to ADB on a Windows PC **without a cable**, using QR codes, and keep the connection alive
> automatically (Android turns wireless debugging off on reboot and, on many phones, when the PC disconnects; the phone app turns it
> back on and the PC app reconnects). Download `LigarADB.exe` (PC) and `LigarADB.apk` (Android 11+) from
> [Releases](https://github.com/leonelferreira0373/ligar-adb/releases). MIT licensed.

## Descarregar

Na página [Releases](https://github.com/leonelferreira0373/ligar-adb/releases): **`LigarADB.exe`** (Windows, já traz o APK dentro) e
**`LigarADB.apk`** (Android 11 ou mais recente). Na 1.ª vez, o Windows pode pedir para deixar passar a app na firewall: aceite em
«Redes privadas» (a app do telemóvel fala com a do PC na rede local).

**Guia de uso completo:** [docs/GUIA.md](docs/GUIA.md) (instalar, emparelhar, dia a dia, cada botão, automático, problemas e soluções, segurança, desinstalar, perguntas).

## As duas apps

| | O que faz |
|---|---|
| **PC** (`pc/dist/LigarADB.exe`, um só ficheiro, com o APK dentro) | QR de emparelhamento (1.ª vez) · QR do PC para a app do telemóvel · leitor do QR do telemóvel pela webcam · ligar pelo IP · religar sozinho · arrancar com o Windows · instalar e autorizar a app no telemóvel · descarrega o ADB oficial da Google se o PC não o tiver |
| **Android** (`android/`, `app.ligaradb`, Android 11+) | Estado (Wi-Fi, IP, depuração) · ligar/desligar a depuração sem fios num toque · leitor do QR do PC · QR do telemóvel · botão nas definições rápidas · **manter a depuração sempre ligada** (volta sozinha quando o Android a desliga) |

## Como se usa

1. **1.ª vez:** no telemóvel, Opções de programador → Depuração sem fios → *Emparelhar dispositivo com código QR*, e ler o QR «1.ª vez» do PC. A app do PC emparelha e liga sozinha.
2. Na app do PC: **Preparar o telemóvel** (instala a app Android e dá-lhe a autorização `WRITE_SECURE_SETTINGS`).
3. Na app do telemóvel: ligar **Manter a depuração sem fios sempre ligada**.
4. Dia a dia não é preciso fazer nada. Se for preciso: ler o QR «Dia a dia» do PC com a app (ou a câmara normal) ou mostrar o QR do telemóvel à webcam.

## Porque é preciso o «manter ligada»

O Android desliga a depuração sem fios ao reiniciar e, em muitos telemóveis, quando o PC corta a ligação (medido no Unitel SMART 4G II, Android 15: a porta fecha em menos de 4 s). A app vigia a definição (`JobScheduler` com gatilho de conteúdo em `adb_wifi_enabled`, sem notificação permanente) e volta a ligá-la. A porta muda de cada vez; o PC encontra-a (mDNS do adb, ou procura nas portas 30000–50000).

Segurança: só PCs já **emparelhados** (chaves do ADB) conseguem entrar. Desligar o «manter ligada» devolve o comportamento normal do Android.

## Formato dos QR

- emparelhar (o do Android): `WIFI:T:ADB;S:<nome>;P:<código>;;`
- do PC: `ligaradb://pc?url=http://<ip-do-pc>:<porta>&chave=<chave>` → a app faz `POST /ola` com `{ip, nome, chave}` e o PC liga
- do telemóvel: `ligaradb://tel?ip=<ip>&nome=<nome>`

## Construir

- Android: `cd android && gradlew assembleRelease` → `app/build/outputs/apk/release/app-release.apk`
- PC: copiar o APK para `pc/LigarADB.apk`, depois `cd pc && python -m PyInstaller --noconfirm --onefile --windowed --name LigarADB --icon icone.ico --add-data "LigarADB.apk;." --hidden-import nucleo app.py`

## Testes de ponta a ponta

Com um telemóvel ligado sem fios: `cd pc && python testes_ponta_a_ponta.py` (QR do PC, QR do telemóvel lido do ecrã do telemóvel, aviso da app ao PC, religar).
Testado a 2026-11-11 no Unitel SMART 4G II (Android 15): tudo OK; cortar a ligação → o telemóvel desliga a depuração → a app volta a ligá-la → o PC religa sozinho.

## Licença

MIT. Ver [LICENSE](LICENSE).
