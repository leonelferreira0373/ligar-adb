package app.ligaradb

import android.content.Intent
import android.service.quicksettings.Tile
import android.service.quicksettings.TileService

/** Botão «ADB sem fios» nas definições rápidas: um toque liga/desliga (com a autorização do PC); sem ela, abre as definições. */
class BotaoRapido : TileService() {
    override fun onStartListening() = mostrar()

    override fun onClick() {
        if (Depuracao.definir(this, !Depuracao.ligada(this))) {
            mostrar()
        } else {
            // sem a permissão especial: abrir a app (que explica e abre as definições)
            val i = Intent(this, MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            @Suppress("DEPRECATION") startActivityAndCollapse(i)
        }
    }

    private fun mostrar() {
        val t = qsTile ?: return
        t.state = if (Depuracao.ligada(this)) Tile.STATE_ACTIVE else Tile.STATE_INACTIVE
        t.subtitle = Depuracao.ipWifi(this) ?: "sem Wi-Fi"
        t.updateTile()
    }
}
