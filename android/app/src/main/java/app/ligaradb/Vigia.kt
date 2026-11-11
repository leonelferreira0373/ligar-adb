package app.ligaradb

import android.app.job.JobInfo
import android.app.job.JobParameters
import android.app.job.JobScheduler
import android.app.job.JobService
import android.content.ComponentName
import android.content.Context
import android.provider.Settings

/**
 * «Manter sempre ligada»: o Android desliga a «Depuração sem fios» ao reiniciar e (em muitos telemóveis) quando o PC corta a ligação.
 * Com o automático ligado, esta tarefa acorda sempre que a definição MUDA (gatilho de conteúdo do JobScheduler, sem serviço nem
 * notificação permanentes) e volta a ligá-la. Depois de correr, volta a agendar-se (os gatilhos de conteúdo são de uma só vez).
 */
class Vigia : JobService() {
    override fun onStartJob(params: JobParameters?): Boolean {
        if (Depuracao.automatico(this) && !Depuracao.ligada(this)) Depuracao.definir(this, true)
        agendar(this)
        return false
    }

    override fun onStopJob(params: JobParameters?) = true

    companion object {
        private const val ID = 7301

        /** Agenda (ou cancela, com o automático desligado) a vigia da definição. */
        fun agendar(ctx: Context) {
            val js = ctx.getSystemService(JobScheduler::class.java) ?: return
            if (!Depuracao.automatico(ctx) || !Depuracao.temPermissao(ctx)) {
                js.cancel(ID)
                return
            }
            val uri = Settings.Global.getUriFor("adb_wifi_enabled")
            val job = JobInfo.Builder(ID, ComponentName(ctx, Vigia::class.java))
                .addTriggerContentUri(JobInfo.TriggerContentUri(uri, 0))
                .setTriggerContentUpdateDelay(500)
                .setTriggerContentMaxDelay(3000)
                .build()
            js.schedule(job)
        }
    }
}
