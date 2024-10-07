import calendar
from datetime import datetime, timedelta
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app.decorators import requires_permission
from app.ferramentas.routes.ponto import get_user_list, get_user_by_id, get_months
from app.ferramentas import ferramentas_bp
from app.services.banco_horas import calculate_hours, get_monthly_time_entries, get_week_start_end_dates, get_weekly_time_entries

@ferramentas_bp.route('/banco_horas', methods=['GET'])
@login_required
@requires_permission('banco-horas')
def banco_horas():
    users = get_user_list()
    months = get_months()
    return render_template('ferramentas/banco_horas.html', months=months, users=users)

@ferramentas_bp.route('/banco_horas/relatorio')
@requires_permission('banco-horas')
@login_required

def banco_horas_relatorio():
    selected_user_id = request.args.get('user')
    selection_type = request.args.get('selection_type')
    selected_month = request.args.get('month', None)
    selected_week = request.args.get('week', None)

    if selected_user_id == 'todos':
        users = get_user_list()
    else:
        user = get_user_by_id(selected_user_id)
        users = [user]

    time_entries = []
    start_date = None
    end_date = None

    for user in users:
        if 'horario_entrada' not in user:
            user['horario_entrada'] = '00:00:00'
        if 'horario_almoco' not in user:
            user['horario_almoco'] = '00:00:00'
        if 'horario_retorno' not in user:
            user['horario_retorno'] = '00:00:00'
        if 'horario_saida' not in user:
            user['horario_saida'] = '00:00:00'

        total_worked_hours = 0
        total_lunch_hours = 0
        work_hours_diff = 0
        lunch_hours_diff = 0
        total_required_work_hours = 0
        total_required_lunch_hours = 0

        if selection_type == 'month':
            year, month = map(int, selected_month.split('-'))
            start_date = f"01/{month:02d}/{year}"
            end_date = f"{calendar.monthrange(year, month)[1]}/{month:02d}/{year}"
            time_entries_, total_worked_hours, total_lunch_hours, total_required_work_hours, total_required_lunch_hours, work_hours_diff, lunch_hours_diff = get_monthly_time_entries(str(user['_id']), year, month)
        elif selection_type == 'week':
            year, month = map(int, selected_month.split('-'))
            week_number = int(selected_week)
            start_date, end_date = get_week_start_end_dates(year, month, week_number)
            time_entries_, total_worked_hours, total_lunch_hours = get_weekly_time_entries(str(user['_id']), year, month, week_number)
            total_required_work_hours = 40
            total_required_lunch_hours = 5
            work_hours_diff = total_worked_hours - total_required_work_hours
            lunch_hours_diff = total_lunch_hours - total_required_lunch_hours

        print(f"start_date: {start_date}, end_date: {end_date}")
        # Adicione o cálculo de horas de trabalho e almoço para cada entrada de tempo
        for entry in time_entries_:
            worked_hours, lunch_hours = calculate_hours(entry['entry_time'], entry['exit_time'], entry['lunch_time'], entry['lunch_return_time'])
            entry['worked_hours'] = worked_hours
            entry['lunch_hours'] = lunch_hours
        # Garantir que sempre retornamos 9 valores
        time_entries.append((str(user['_id']), user['nome'], time_entries_, total_worked_hours, total_lunch_hours, work_hours_diff, lunch_hours_diff, total_required_work_hours, total_required_lunch_hours))

    return render_template('ferramentas/banco_relatorio.html', 
                           time_entries=time_entries, 
                           user_name=user['nome'] if selected_user_id != 'todos' else 'Todos', 
                           users=users,
                           start_date=start_date,
                           end_date=end_date)