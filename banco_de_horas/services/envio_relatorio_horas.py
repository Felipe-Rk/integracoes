
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime, timedelta
import logging
from app.models.user import User
from app.services.banco_horas import get_weekly_time_entries
from app.services.chat import MensagemService
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = None

ids_para_ignorar = ["65c4d261db7865f8ac22bc85"]

def formatar_relatorio_horas(entries, total_worked_hours, total_lunch_hours, inicio_semana, fim_semana):
    horas_trabalho_esperadas = 40.0
    horas_almoco_esperadas = 5.0

    saldo_trabalho = total_worked_hours - horas_trabalho_esperadas
    saldo_almoco = total_lunch_hours - horas_almoco_esperadas

    relatorio = (
        f"Relatório de Horas Semanal\n"
        f"De {inicio_semana.strftime('%d/%m/%Y')} até {fim_semana.strftime('%d/%m/%Y')}\n"
        f"Horas semanais necessárias: 40h de trabalho | 5h de almoço\n"
        f"Banco de horas: {'+' if saldo_trabalho >= 0 else ''}{saldo_trabalho:.2f} horas de trabalho, {'+' if saldo_almoco >= 0 else ''}{saldo_almoco:.2f} horas de almoço\n"
    )

    relatorio += "\nHorários em desacordo:\n"
    for entry in entries:
        if entry['total_worked_hours'] < 7.83 or entry['total_lunch_hours'] < 0.91 or entry['total_lunch_hours'] > 1.16:
            worked_hours_str = decimal_hours_to_time_string(entry['total_worked_hours'])
            lunch_hours_str = decimal_hours_to_time_string(entry['total_lunch_hours'])
            relatorio += (
                f"- {entry['entry_date_br']}: "
                f"{worked_hours_str} trabalhadas, "
                f"{lunch_hours_str} de almoço\n"
            )

    return relatorio

def enviar_relatorio_semanal_para_todos():
    id_remetente = "6644e34411af901b0d8e8eab"

    hoje = datetime.now().date()
    inicio_semana_anterior = hoje - timedelta(days=hoje.weekday() + 7)
    fim_semana_anterior = inicio_semana_anterior + timedelta(days=6)  # De segunda a domingo

    # Recupera todos os usuários
    todos_usuarios = User.objects()

    for usuario in todos_usuarios:
        id_destinatario = str(usuario.id)

        # Verifica se o ID está na lista de IDs a serem ignorados
        if id_destinatario in ids_para_ignorar:
            logging.info(f"Pulado envio de relatório para {usuario.nome} (ID: {id_destinatario}).")
            continue

        entries, total_worked_hours, total_lunch_hours = get_weekly_time_entries(
            id_destinatario, 
            inicio_semana_anterior.year, 
            inicio_semana_anterior.month, 
            (inicio_semana_anterior.day - 1) // 7 + 1
        )

        relatorio = formatar_relatorio_horas(entries,total_worked_hours, total_lunch_hours, inicio_semana_anterior, fim_semana_anterior)

        MensagemService.postar_mensagem(
            texto_mensagem=relatorio,
            id_destinatario=id_destinatario,
            id_remetente=id_remetente
        )
    logging.info("Envio de relatórios semanais concluído.") 

def decimal_hours_to_time_string(decimal_hours):
    total_minutes = int(decimal_hours * 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}:{minutes:02d}"

# Agendamento da tarefa
def agendar_tarefa():
    global scheduler
    if scheduler is None:
        scheduler = BackgroundScheduler(executors={'default': ThreadPoolExecutor(1)})  # Limita a execução de tarefas a uma única instância
        if not scheduler.get_jobs():  # Verifica se a tarefa já está agendada
            scheduler.add_job(enviar_relatorio_semanal_para_todos, 'cron', day_of_week='mon', hour=9)
            scheduler.start()
            logging.info("Tarefa agendada para envio semanal de relatórios.")
    else:
        logging.info("Tarefa já foi agendada anteriormente.")

