package app.ligaradb

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.compose.ui.platform.LocalLifecycleOwner
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import kotlin.concurrent.thread

/**
 * Ecrã único. De cima para baixo, na ordem em que se usa:
 *  1. Estado (rede, IP, depuração sem fios, permissão especial).
 *  2. Ligar a depuração sem fios (um toque se a app tiver a permissão; senão abre as definições).
 *  3. Ligar ao PC: ler o QR do PC (a app avisa-o) ou mostrar o QR deste telemóvel (a webcam do PC lê).
 *  4. Ligar sozinho ao arrancar (opcional).
 */
class MainActivity : ComponentActivity() {
    private var aviso by mutableStateOf("")
    private var mostrarQr by mutableStateOf(false)
    private var versao by mutableIntStateOf(0) // muda para reler o estado

    private val leitor = registerForActivityResult(ScanContract()) { r -> r.contents?.let { usarQrDoPc(it) } }

    /** O QR do PC chega pelo leitor da app ou como link (câmara normal do telemóvel): liga a depuração (se puder) e avisa o PC. */
    private fun usarQrDoPc(texto: String) {
        val pc = Qr.lerPc(texto)
        if (pc == null) { aviso = "Este QR não é da app «Ligar ADB» do PC."; return }
        val ip = Depuracao.ipWifi(this)
        if (ip == null) { aviso = "Ligue o telemóvel ao Wi-Fi (o mesmo do PC)."; return }
        if (!Depuracao.ligada(this)) Depuracao.definir(this, true)
        aviso = "A avisar o PC…"
        thread {
            val res = Qr.avisarPc(pc, ip, Depuracao.nomeDoAparelho())
            runOnUiThread { aviso = res.getOrElse { "Não consegui falar com o PC: ${it.message}. Estão na mesma rede Wi-Fi?" } }
        }
    }

    override fun onNewIntent(intent: android.content.Intent) {
        super.onNewIntent(intent)
        intent.dataString?.let { usarQrDoPc(it) }
    }

    private val camara = registerForActivityResult(ActivityResultContracts.RequestPermission()) { ok ->
        if (ok) abrirLeitor() else aviso = "Sem a câmara não dá para ler o QR. Use «Mostrar o meu QR» e a webcam do PC."
    }

    private fun abrirLeitor() {
        leitor.launch(ScanOptions().setDesiredBarcodeFormats(ScanOptions.QR_CODE).setPrompt("Aponte para o QR da app do PC").setBeepEnabled(false).setOrientationLocked(true))
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        Vigia.agendar(this) // garante a vigia (por exemplo, depois de actualizar a app)
        setContent { MaterialTheme { Ecra() } }
        if (savedInstanceState == null) intent?.dataString?.let { usarQrDoPc(it) }
    }

    @Composable
    private fun Ecra() {
        val ctx = this
        // reler o estado ao voltar das definições
        val dono = LocalLifecycleOwner.current
        DisposableEffect(dono) {
            val o = LifecycleEventObserver { _, e -> if (e == Lifecycle.Event.ON_RESUME) versao++ }
            dono.lifecycle.addObserver(o)
            onDispose { dono.lifecycle.removeObserver(o) }
        }
        @Suppress("UNUSED_EXPRESSION") versao
        val ip = Depuracao.ipWifi(ctx)
        val ligada = Depuracao.ligada(ctx)
        val programador = Depuracao.opcoesDeProgramador(ctx)
        val permissao = Depuracao.temPermissao(ctx)
        var auto by remember { mutableStateOf(Depuracao.automatico(ctx)) }

        Column(
            Modifier.fillMaxSize().background(Color(0xFFFDFDFD)).verticalScroll(rememberScrollState()).padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text("Ligar ADB", fontSize = 34.sp, fontWeight = FontWeight.Medium)
            Text("Liga este telemóvel ao ADB de um PC, sem cabo.", color = Color(0xFF727272))

            Cartao {
                Linha("Wi-Fi", ip ?: "sem Wi-Fi", ip != null)
                Linha("Opções de programador", if (programador) "ligadas" else "desligadas", programador)
                Linha("Depuração sem fios", if (ligada) "ligada" else "desligada", ligada)
                Linha("Ligar com um toque", if (permissao) "sim" else "falta autorização do PC", permissao)
            }

            if (!programador) Texto("Primeiro ative as Opções de programador: Definições → Acerca do telemóvel → toque 7 vezes em «Número de compilação».")

            Botao(if (ligada) "Desligar a depuração sem fios" else "Ligar a depuração sem fios") {
                if (!Depuracao.definir(ctx, !ligada)) {
                    aviso = "Ligue-a no ecrã que abriu. Para passar a ser um toque: ligue uma vez o ADB e, na app do PC, carregue em «Autorizar o telemóvel»."
                    Depuracao.abrirDefinicoes(ctx)
                } else versao++
            }

            Text("Ligar ao PC", fontSize = 20.sp, fontWeight = FontWeight.Medium)
            Texto("Na app «Ligar ADB» do PC, use um dos dois:")
            Botao("Ler o QR do PC") {
                if (checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) abrirLeitor()
                else camara.launch(Manifest.permission.CAMERA)
            }
            Botao(if (mostrarQr) "Esconder o meu QR" else "Mostrar o meu QR (para a webcam do PC)") { mostrarQr = !mostrarQr }
            if (mostrarQr) {
                if (ip == null) Texto("Ligue o Wi-Fi para mostrar o QR.")
                else {
                    val bmp = remember(ip) { Qr.imagem(Qr.doTelemovel(ip, Depuracao.nomeDoAparelho())) }
                    Image(bmp.asImageBitmap(), contentDescription = "QR deste telemóvel", modifier = Modifier.fillMaxWidth().aspectRatio(1f))
                    Texto("$ip · ${Depuracao.nomeDoAparelho()}")
                }
            }

            if (aviso.isNotEmpty()) Cartao { Text(aviso) }

            Text("Automático", fontSize = 20.sp, fontWeight = FontWeight.Medium)
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("Manter a depuração sem fios sempre ligada")
                    Text(
                        if (permissao) "O Android desliga-a ao reiniciar e quando o PC corta a ligação. Com isto ligado, volta logo sozinha. Só PCs já emparelhados conseguem entrar."
                        else "Precisa da autorização do PC (ver acima).",
                        fontSize = 13.sp, color = Color(0xFF727272),
                    )
                }
                Switch(checked = auto && permissao, enabled = permissao, onCheckedChange = {
                    auto = it
                    Depuracao.definirAutomatico(ctx, it)
                    if (it && !Depuracao.ligada(ctx)) Depuracao.definir(ctx, true)
                    Vigia.agendar(ctx)
                    versao++
                })
            }
            Texto("Também pode pôr o botão «ADB sem fios» nas definições rápidas: puxe o painel, toque no lápis e arraste-o.")
        }
    }

    @Composable private fun Cartao(conteudo: @Composable ColumnScope.() -> Unit) =
        Column(Modifier.fillMaxWidth().background(Color.White, RoundedCornerShape(16.dp)).padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp), content = conteudo)

    @Composable private fun Linha(nome: String, valor: String, bom: Boolean) = Row(Modifier.fillMaxWidth()) {
        Text(nome, Modifier.weight(1f)); Text(valor, color = if (bom) Color(0xFF0A7A3E) else Color(0xFFB3261E), fontWeight = FontWeight.Medium)
    }

    @Composable private fun Texto(t: String) = Text(t, color = Color(0xFF363636), fontSize = 14.sp)

    @Composable private fun Botao(t: String, onClick: () -> Unit) =
        Button(onClick = onClick, modifier = Modifier.fillMaxWidth().height(52.dp), shape = RoundedCornerShape(26.dp)) { Text(t) }
}
