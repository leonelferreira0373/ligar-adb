package app.ligaradb

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/**
 * Ao arrancar o telemóvel (opcional, desligado por omissão): volta a ligar a «Depuração sem fios», que o Android desliga sempre que
 * reinicia, e põe a vigia a correr (ver Vigia). Só funciona com a autorização do PC, e só um PC já emparelhado consegue entrar (o ADB sem fios usa chaves).
 */
class AoArrancar : BroadcastReceiver() {
    override fun onReceive(ctx: Context, intent: Intent) {
        if (Depuracao.automatico(ctx)) Depuracao.definir(ctx, true)
        Vigia.agendar(ctx) // e volta a vigiar (o agendamento não sobrevive ao reinício)
    }
}
