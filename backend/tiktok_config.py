# tiktok_config.py

# Configurações da conta TikTok (usando credenciais do Google para o login)
TIKTOK_CONFIG = {
    'email': 'leoportaldoigarape@gmail.com',
    'password': 'Aninhasz1!!!',
    'login_method': 'email', # <-- Define que o login será via Google
    'backup_email': '',  # Opcional, pode deixar vazio se não for usar
    'phone': '',         # Opcional, pode deixar vazio se não for usar
}

# Configurações de posting (podem ser ajustadas conforme sua estratégia)
POSTING_CONFIG = {
    'horarios_otimos': ['09:00', '15:00', '21:00'],  # Horários de maior engajamento
    'max_posts_dia': 3,
    'intervalo_minimo_horas': 4,
    'hashtags_obrigatorias': ['#fyp', '#viral', '#brasil'],
    'categorias_permitidas': ['curiosidades', 'ciencia', 'historia', 'tecnologia']
}