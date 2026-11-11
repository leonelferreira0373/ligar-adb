package app.ligaradb

import android.Manifest
import android.content.ActivityNotFoundException
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.ConnectivityManager
import android.net.LinkProperties
import android.net.NetworkCapabilities
import android.os.Build
import android.provider.Settings
import java.net.Inet4Address

/**
 * Tudo o que a app sabe e faz sobre a «Depuração sem fios» do Android e a rede.
 *
 * Ler o estado é livre (Settings.Global é legível por qualquer app). LIGAR/DESLIGAR precisa da permissão especial
 * WRITE_SECURE_SETTINGS, que nenhuma app pode pedir sozinha: a app do PC dá-a uma vez por ADB. Sem ela, a app abre o ecrã
 * das definições certo e o utilizador liga à mão.
 */
object Depuracao {
    /** A chave do Android para a «Depuração sem fios» (Android 11+). */
    private const val CHAVE = "adb_wifi_enabled"
    private const val PREFS = "ligar_adb"

    fun ligada(ctx: Context): Boolean = Settings.Global.getInt(ctx.contentResolver, CHAVE, 0) == 1

    fun opcoesDeProgramador(ctx: Context): Boolean =
        Settings.Global.getInt(ctx.contentResolver, Settings.Global.DEVELOPMENT_SETTINGS_ENABLED, 0) == 1

    fun temPermissao(ctx: Context): Boolean =
        ctx.checkSelfPermission(Manifest.permission.WRITE_SECURE_SETTINGS) == PackageManager.PERMISSION_GRANTED

    /** Liga ou desliga. Devolve false se a app não tiver a permissão especial (então usar [abrirDefinicoes]). */
    fun definir(ctx: Context, ligar: Boolean): Boolean {
        if (!temPermissao(ctx)) return false
        return try {
            Settings.Global.putInt(ctx.contentResolver, CHAVE, if (ligar) 1 else 0)
        } catch (e: SecurityException) {
            false
        }
    }

    /** Abre o ecrã da «Depuração sem fios» (ou, se o fabricante o esconder, as Opções de programador). */
    fun abrirDefinicoes(ctx: Context) {
        val diretos = listOf(
            Intent("android.settings.ADB_WIRELESS_SETTINGS"),
            Intent().setComponent(ComponentName("com.android.settings", "com.android.settings.Settings\$WirelessDebuggingActivity")),
            Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS),
        )
        for (i in diretos) {
            try {
                ctx.startActivity(i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                return
            } catch (_: ActivityNotFoundException) {
            } catch (_: SecurityException) {
            }
        }
        ctx.startActivity(Intent(Settings.ACTION_SETTINGS).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }

    /** O IPv4 do telemóvel na rede Wi-Fi actual (null fora do Wi-Fi). */
    fun ipWifi(ctx: Context): String? {
        val cm = ctx.getSystemService(ConnectivityManager::class.java) ?: return null
        val rede = cm.activeNetwork ?: return null
        val cap = cm.getNetworkCapabilities(rede) ?: return null
        if (!cap.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) && !cap.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET)) return null
        val lp: LinkProperties = cm.getLinkProperties(rede) ?: return null
        return lp.linkAddresses.map { it.address }.filterIsInstance<Inet4Address>().firstOrNull()?.hostAddress
    }

    fun nomeDoAparelho(): String = "${Build.MANUFACTURER} ${Build.MODEL}".trim()

    /** «Ligar sozinho ao arrancar» (opcional). */
    fun automatico(ctx: Context): Boolean = ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean("auto", false)
    fun definirAutomatico(ctx: Context, sim: Boolean) =
        ctx.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putBoolean("auto", sim).apply()
}
