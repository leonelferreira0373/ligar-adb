package app.ligaradb

import android.graphics.Bitmap
import com.google.zxing.BarcodeFormat
import com.google.zxing.EncodeHintType
import com.google.zxing.qrcode.QRCodeWriter
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLDecoder
import java.net.URLEncoder

/**
 * Os dois QR que o sistema usa (o mesmo formato na app do PC):
 *  - QR do TELEMÓVEL (este mostra, a webcam do PC lê):  ligaradb://tel?ip=192.168.0.200&nome=Unitel%20SMART
 *  - QR do PC (o PC mostra, esta app lê):               ligaradb://pc?url=http://192.168.0.10:38180&chave=abc123
 * Ao ler o QR do PC, a app diz ao PC «estou aqui» (POST /ola com o IP e o nome) e o PC liga o ADB.
 */
object Qr {
    fun doTelemovel(ip: String, nome: String): String =
        "ligaradb://tel?ip=${enc(ip)}&nome=${enc(nome)}"

    data class Pc(val url: String, val chave: String)

    fun lerPc(texto: String): Pc? {
        if (!texto.startsWith("ligaradb://pc?")) return null
        val q = texto.substringAfter("?").split("&").associate { it.substringBefore("=") to dec(it.substringAfter("=", "")) }
        val url = q["url"] ?: return null
        val chave = q["chave"] ?: return null
        if (!url.startsWith("http://")) return null
        return Pc(url.trimEnd('/'), chave)
    }

    /** Avisa o PC (em segundo plano). Devolve a mensagem do PC, ou o erro. */
    fun avisarPc(pc: Pc, ip: String, nome: String): Result<String> = runCatching {
        val c = URL("${pc.url}/ola").openConnection() as HttpURLConnection
        c.requestMethod = "POST"
        c.connectTimeout = 4000
        c.readTimeout = 25000 // o PC só responde depois de tentar ligar o ADB
        c.doOutput = true
        c.setRequestProperty("Content-Type", "application/json")
        val corpo = JSONObject().put("ip", ip).put("nome", nome).put("chave", pc.chave).toString()
        c.outputStream.use { it.write(corpo.toByteArray()) }
        val resposta = (if (c.responseCode in 200..299) c.inputStream else c.errorStream).bufferedReader().readText()
        c.disconnect()
        JSONObject(resposta).optString("mensagem", resposta)
    }

    fun imagem(texto: String, lado: Int = 720): Bitmap {
        val m = QRCodeWriter().encode(texto, BarcodeFormat.QR_CODE, lado, lado, mapOf(EncodeHintType.MARGIN to 2))
        val px = IntArray(lado * lado) { i -> if (m[i % lado, i / lado]) 0xFF000000.toInt() else 0xFFFFFFFF.toInt() }
        return Bitmap.createBitmap(px, lado, lado, Bitmap.Config.ARGB_8888)
    }

    private fun enc(s: String) = URLEncoder.encode(s, "UTF-8")
    private fun dec(s: String) = URLDecoder.decode(s, "UTF-8")
}
