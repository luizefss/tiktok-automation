import time
import random
import os
import json
from datetime import datetime
import shutil # Importado para remover diretório temporário

# Tentar importar Selenium, fallback se não tiver Chrome
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException, StaleElementReferenceException
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ Selenium não disponível. Funcionalidades de posting real serão limitadas.")
except WebDriverException as e:
    SELENIUM_AVAILABLE = False
    print(f"⚠️ Erro ao inicializar Selenium/WebDriver: {e}. Verifique sua instalação do Chrome/ChromeDriver.")


# Importar configurações de um arquivo separado
try:
    from tiktok_config import TIKTOK_CONFIG, POSTING_CONFIG
except ImportError:
    print("❌ Arquivo tiktok_config.py não encontrado. Crie-o com suas credenciais para o primeiro login.")
    TIKTOK_CONFIG = {}
    POSTING_CONFIG = {}

class TikTokPoster:
    def __init__(self, config=None):
        self.driver = None
        self.wait = None
        self.is_logged_in = False
        self.config = TIKTOK_CONFIG if config is None else config
        self.selenium_available = SELENIUM_AVAILABLE

        self.posts_log_file = "../data/posts_log.json"
        os.makedirs("../data", exist_ok=True)

        self.session_file = "../data/tiktok_session.json"
        os.makedirs("../data", exist_ok=True)

    def verificar_chrome_instalado(self):
        """Verifica se Chrome está instalado"""
        chrome_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/usr/bin/chromium-browser',
            '/snap/bin/chromium',
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe', # Windows default
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe' # Windows (x86)
        ]

        for path in chrome_paths:
            if os.path.exists(path):
                print(f"✅ Chrome encontrado: {path}")
                return path
        print("❌ Chrome não encontrado no sistema.")
        return None

    def criar_driver_para_producao(self, user_data_dir=None):
        """Driver otimizado para produção real"""
        if not self.selenium_available:
            print("❌ Selenium não está disponível. Não é possível criar o driver.")
            return False

        try:
            print("🤖 Configurando driver para produção...")

            chrome_path = self.verificar_chrome_instalado()
            if not chrome_path:
                print("💡 Para instalar Chrome no Linux:")
                print("sudo apt update && sudo apt install google-chrome-stable -y")
                return False

            chrome_options = Options()
            chrome_options.binary_location = chrome_path

            # Configurações anti-detecção
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Configurações de performance e para VPS
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            # Mantenha esta linha COMENTADA para depurar (ver o navegador)
            # Descomente-a para rodar em produção (sem interface gráfica em VPS)
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--window-size=1366,768')

            # User agent realista (pode ser atualizado periodicamente)
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            chrome_options.add_argument('--disable-notifications') # Desabilita pop-ups de notificação

            # Adicionar esta linha para usar um diretório de dados de usuário temporário
            if user_data_dir:
                chrome_options.add_argument(f'--user-data-dir={user_data_dir}')

            # --- CORREÇÃO AQUI: APONTAR DIRETAMENTE PARA O EXECUTÁVEL DO CHROMEDRIVER ---
            # Use o caminho EXATO do chromedriver que você confirmou via 'python3 -c ...'
            _specific_chromedriver_path = '/root/.wdm/drivers/chromedriver/linux64/138.0.7204.183/chromedriver-linux64/chromedriver'

            # Remover a linha de 'ChromeDriverManager().install()'
            # service = Service(ChromeDriverManager().install()) # REMOVA OU COMENTE ESTA LINHA

            # Use o caminho direto:
            service = Service(executable_path=_specific_chromedriver_path)
            # --- FIM DA CORREÇÃO ---

            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Script anti-detecção (executado após a criação do driver)
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en'],
                });
            """)

            self.wait = WebDriverWait(self.driver, 20)

            print("✅ Driver de produção criado!")
            return True

        except Exception as e:
            print(f"❌ Erro ao criar driver: {e}")
            return False

    def carregar_sessao(self):
        """Carrega cookies da sessão salva e os adiciona ao driver."""
        if not os.path.exists(self.session_file):
            print("💾 Nenhum arquivo de sessão encontrado.")
            return False

        try:
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)

            if not session_data.get('cookies'):
                print("💾 Arquivo de sessão vazio ou corrompido.")
                os.remove(self.session_file)
                return False

            print("💾 Carregando cookies de sessão...")
            self.driver.get("https://www.tiktok.com")
            self.esperar_humano(1, 2)

            for cookie in session_data['cookies']:
                if 'expiry' in cookie and not isinstance(cookie['expiry'], (int, float)):
                    del cookie['expiry']
                elif 'expiry' in cookie:
                    cookie['expiry'] = int(cookie['expiry'])

                if 'domain' in cookie and cookie['domain'] and not cookie['domain'].startswith('.'):
                    cookie['domain'] = '.' + cookie['domain'].lstrip('.')
                elif 'domain' not in cookie or not cookie['domain']:
                     cookie['domain'] = '.tiktok.com'

                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    print(f"⚠️ Erro ao adicionar cookie {cookie.get('name')}: {e}")
                    continue

            print("✅ Cookies carregados. Verificando status do login...")
            self.driver.get("https://www.tiktok.com")
            self.esperar_humano(3, 5)

            if self.verificar_login_sucesso():
                self.is_logged_in = True
                print("✅ Sessão restaurada com sucesso!")
                return True
            else:
                print("❌ Sessão restaurada, mas login não é válido. Os cookies podem estar expirados.")
                os.remove(self.session_file)
                return False

        except Exception as e:
            print(f"❌ Erro ao carregar sessão: {e}")
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            return False

    def fazer_login_automatico(self, email=None, password=None, login_method='email'):
        """
        Login automático real no TikTok.
        Prioriza carregar cookies. Se falhar, tenta login via email/senha ou Google.
        """
        if not self.driver:
            print("❌ Driver não iniciado. Não é possível fazer login.")
            return False

        if self.is_logged_in:
            print("✅ Já logado.")
            return True

        # Tentar carregar sessão salva primeiro
        if self.carregar_sessao():
            return True

        print("🔐 Tentando login com credenciais...")
        if not email or not password:
            print("❌ Credenciais (email e senha) não fornecidas para login inicial. Você deve fornecê-las para o primeiro login.")
            return False

        try:
            if login_method == 'email':
                print("✨ Tentando login via Email/Senha...")
                self.driver.get("https://www.tiktok.com/login/phone-or-email/email")
                self.esperar_humano(2, 3)

                # --- NOVO: Tentar alternar para iframe de login ---
                try:
                    # Tentar encontrar o iframe pelo name, id, ou seletor genérico
                    iframe_selectors = [
                        By.CSS_SELECTOR, "iframe[src*='login']",
                        By.ID, "login-iframe",
                        By.NAME, "tiktok-login-iframe" # Exemplo, verificar no inspecionar
                    ]
                    iframe_found = False
                    for i in range(0, len(iframe_selectors), 2):
                        selector_type = iframe_selectors[i]
                        selector_value = iframe_selectors[i+1]
                        try:
                            iframe = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((selector_type, selector_value))
                            )
                            self.driver.switch_to.frame(iframe)
                            print(f"✅ Alternou para iframe de login: {selector_value}")
                            iframe_found = True
                            break
                        except TimeoutException:
                            continue
                        except NoSuchElementException:
                            continue
                        except Exception as e:
                            print(f"⚠️ Erro ao tentar alternar para iframe {selector_value}: {e}")
                            continue

                    if not iframe_found:
                        print("ℹ️ Nenhum iframe de login encontrado ou necessário. Continuando no contexto principal.")

                except Exception as e:
                    print(f"❌ Erro geral ao tentar lidar com iframe: {e}")
                # --- FIM NOVO: Tentar alternar para iframe de login ---


                # --- SELETORES ATUALIZADOS PARA EMAIL E SENHA BASEADOS NO SEU HTML ---
                # Input Email: <input type="text" ... name="username" class="tiktok-11to27l-InputContainer etcs7ny1">
                email_field_selectors = [
                    "input[name='username']", # Mais robusto: usa o atributo 'name'
                    "input[type='text'][placeholder*='E-mail']", # Combina tipo e placeholder
                    "input[type='text'][autocomplete='webauthn']", # Atributo autocomplete
                    "input.tiktok-11to27l-InputContainer[type='text']", # Combina classe e tipo
                    "input[type='text']" # Genérico
                ]
                email_field = None
                for selector in email_field_selectors:
                    try:
                        email_field = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if email_field.is_displayed() and email_field.is_enabled():
                            print(f"✅ Campo de email encontrado com seletor: {selector}")
                            break
                        else:
                            email_field = None
                    except TimeoutException: # Ignorar TimeoutException e tentar o próximo seletor
                        continue
                    except StaleElementReferenceException: # Lidar com elemento obsoleto após um carregamento
                        continue
                    except Exception as e:
                        print(f"⚠️ Erro ao procurar campo de email com {selector}: {e}")
                        continue

                if not email_field:
                    print("❌ Campo de email para login tradicional não encontrado")
                    # Tentar voltar ao contexto padrão se estava em iframe e não encontrou
                    try: self.driver.switch_to.default_content()
                    except: pass
                    return False

                print("📧 Digitando email (login tradicional)...")
                self.digitar_como_humano(email_field, email)
                self.esperar_humano(1, 2)

                # Input Senha: <input type="password" ... autocomplete="new-password" class="tiktok-wv3bkt-InputContainer etcs7ny1">
                password_field_selectors = [
                    "input[type='password'][autocomplete='new-password']", # Mais robusto: tipo e autocomplete
                    "input[type='password'][placeholder*='Senha']", # Combina tipo e placeholder
                    "input.tiktok-wv3bkt-InputContainer[type='password']", # Combina classe e tipo
                    "input[type='password']" # Genérico
                ]
                password_field = None
                for selector in password_field_selectors:
                    try:
                        password_field = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if password_field.is_displayed() and password_field.is_enabled():
                            print(f"✅ Campo de senha encontrado com seletor: {selector}")
                            break
                        else:
                            password_field = None
                    except TimeoutException:
                        continue
                    except StaleElementReferenceException:
                        continue
                    except Exception as e:
                        print(f"⚠️ Erro ao procurar campo de senha com {selector}: {e}")
                        continue

                if not password_field:
                    print("❌ Campo de senha para login tradicional não encontrado")
                    # Tentar voltar ao contexto padrão se estava em iframe e não encontrou
                    try: self.driver.switch_to.default_content()
                    except: pass
                    return False

                print("🔑 Digitando senha (login tradicional)...")
                self.digitar_como_humano(password_field, password)
                self.esperar_humano(1, 2)

                # Botão Entrar: <button type="submit" data-e2e="login-button" class="e1w6iovg0 tiktok-11sviba-Button-StyledButton ehk74z00">Entrar</button>
                login_button_selectors = [
                    "button[data-e2e='login-button']", # Mais forte: atributo data-e2e
                    "button[type='submit']", # Fallback, importante!
                    "//button[contains(text(), 'Entrar')]", # XPath por texto (português)
                    "//button[contains(text(), 'Log in')]", # XPath por texto (inglês)
                    "button.tiktok-11sviba-Button-StyledButton" # Classe do botão
                ]

                login_button = None
                for selector in login_button_selectors:
                    try:
                        if selector.startswith('//'):
                            # Para XPath, usar EC.element_to_be_clickable diretamente com WebDriverWait
                            login_button = WebDriverWait(self.driver, 10).until( # Aumentado o timeout para botão
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            login_button = WebDriverWait(self.driver, 10).until( # Aumentado o timeout para botão
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        if login_button.is_enabled() and login_button.is_displayed():
                            print(f"✅ Botão de login encontrado com seletor: {selector}")
                            break
                        else:
                            login_button = None
                    except TimeoutException:
                        continue
                    except StaleElementReferenceException:
                        continue
                    except Exception as e:
                        print(f"⚠️ Erro ao procurar botão de login com {selector}: {e}")
                        continue

                if not login_button:
                    print("❌ Botão de login tradicional não encontrado")
                    # Tentar voltar ao contexto padrão se estava em iframe e não encontrou
                    try: self.driver.switch_to.default_content()
                    except: pass
                    return False

                print("🚀 Clicando em login (tradicional)...")
                # Scrolar para o botão antes de clicar para garantir visibilidade
                self.driver.execute_script("arguments[0].scrollIntoView(true);", login_button)
                self.esperar_humano(0.5, 1) # Pequena pausa após o scroll
                self.clicar_como_humano(login_button)
                self.esperar_humano(5, 8) # Espera para o carregamento da próxima página/estado

                # --- NOVO: Capturar tela para depuração (MANTIDO) ---
                screenshot_path = "../data/login_debug_screenshot.png"
                try:
                    self.driver.save_screenshot(screenshot_path)
                    print(f"📸 Screenshot salva em: {os.path.abspath(screenshot_path)}")
                except Exception as e:
                    print(f"❌ Erro ao salvar screenshot: {e}")
                # --- FIM NOVO ---

                # Voltar ao contexto principal após a interação com o iframe (se tiver entrado em um)
                try:
                    self.driver.switch_to.default_content()
                    print("✅ Voltou ao contexto principal do navegador.")
                except Exception as e:
                    print(f"⚠️ Erro ao tentar voltar ao contexto principal: {e}")

            elif login_method == 'google':
                print("✨ Tentando login via Google...")
                self.driver.get("https://www.tiktok.com/login")
                self.esperar_humano(3, 5)

                google_button_selectors = [
                    "//button[contains(., 'Continuar com Google')]",
                    "//div[contains(@class, 'login-button') and contains(., 'Google')]",
                    "button[data-e2e='google-button']",
                    "//div[text()='Continuar com Google']"
                ]

                google_button = None
                for selector in google_button_selectors:
                    try:
                        if selector.startswith('//'):
                            google_button = WebDriverWait(self.driver, 10).until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                        else:
                            google_button = WebDriverWait(self.driver, 10).until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                            )
                        if google_button.is_enabled() and google_button.is_displayed():
                            break
                        else:
                            google_button = None
                    except:
                        continue

                if not google_button:
                    print("❌ Botão 'Continuar com Google' não encontrado no TikTok.")
                    return False

                self.clicar_como_humano(google_button)
                self.esperar_humano(5, 10)

                original_window = self.driver.current_window_handle
                all_windows = self.driver.window_handles
                google_window = None

                for window_handle in all_windows:
                    if window_handle != original_window:
                        self.driver.switch_to.window(window_handle)
                        if "accounts.google.com" in self.driver.current_url:
                            google_window = window_handle
                            break
                        else:
                            try:
                                self.driver.close()
                            except:
                                pass
                            self.driver.switch_to.window(original_window)
                            all_windows = self.driver.window_handles

                if not google_window:
                    print("❌ Não foi possível encontrar a janela de login do Google.")
                    self.driver.switch_to.window(original_window)
                    return False

                print("🌐 Navegando na página de login do Google...")
                self.esperar_humano(3, 5)

                try:
                    email_google_field = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[name='identifier']"))
                    )
                    self.digitar_como_humano(email_google_field, email)
                    self.clicar_como_humano(self.driver.find_element(By.ID, "identifierNext") or self.driver.find_element(By.XPATH, "//button[contains(., 'Próxima')]"))
                    self.esperar_humano(3, 5)

                    password_google_field = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password'], input[name='password']"))
                    )
                    self.digitar_como_humano(password_google_field, password)
                    self.clicar_como_humano(self.driver.find_element(By.ID, "passwordNext") or self.driver.find_element(By.XPATH, "//button[contains(., 'Próxima')]"))
                    self.esperar_humano(5, 10)
                except TimeoutException:
                    print("❌ Timeout durante login no Google. Pode ser 2FA ou CAPTCHA.")
                    try: self.driver.close()
                    except: pass
                    self.driver.switch_to.window(original_window)
                    return False
                except NoSuchElementException:
                    print("❌ Elemento de login do Google não encontrado. Pode ser 2FA ou CAPTCHA.")
                    try: self.driver.close()
                    except: pass
                    self.driver.switch_to.window(original_window)
                    return False

                self.driver.switch_to.window(original_window)
                self.esperar_humano(5, 10)

            else:
                print("❌ Método de login inválido. Use 'email' ou 'google'.")
                return False

            if self.verificar_login_sucesso():
                print("✅ Login realizado com sucesso no TikTok!")
                self.is_logged_in = True
                self.salvar_sessao()
                return True
            else:
                print("❌ Login falhou no TikTok - verificar credenciais, método ou captcha/2FA.")
                return False

        except TimeoutException:
            print("❌ Tempo limite excedido durante o login. Elemento não encontrado ou página lenta.")
            return False
        except Exception as e:
            print(f"❌ Erro geral no login: {e}")
            return False

    def verificar_login_sucesso(self):
        """Verifica se o login foi bem-sucedido"""
        try:
            success_indicators = [
                "//a[contains(@href, '/upload')]",
                "//div[@data-e2e='nav-upload']",
                "//button[contains(text(), 'Upload')]",
                "[data-e2e='profile-icon']",
                "//img[contains(@alt, 'Perfil do usuário')]",
                "//div[contains(@class, 'DivMainContainer')]"
            ]

            for indicator in success_indicators:
                try:
                    if indicator.startswith('//'):
                        element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, indicator))
                        )
                    else:
                        element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, indicator))
                        )
                    if element and element.is_displayed():
                        print(f"✅ Indicador de login de sucesso encontrado: {indicator}")
                        return True
                except:
                    continue

            current_url = self.driver.current_url
            if "login" not in current_url.lower() and "signup" not in current_url.lower() and "captcha" not in current_url.lower():
                print(f"✅ URL atual não é de login/signup/captcha: {current_url}")
                return True

            return False

        except Exception as e:
            print(f"⚠️ Erro ao verificar login: {e}")
            return False

    def postar_video_real(self, video_file, titulo, hashtags=None):
        """Posting real no TikTok"""
        # A lógica de video_file precisa ser passada para postar_video_real se não estiver no init ou em uma variável global
        # Vou assumir que 'video_file' é um parâmetro necessário aqui.
        print("💡 NOTA: O método 'postar_video_real' requer 'video_file' como argumento.")
        print("Por favor, certifique-se de que o vídeo está sendo passado corretamente.")

        if not self.selenium_available:
            print("❌ Selenium não está disponível. Não é possível fazer posting real.")
            # self.simular_posting(video_file, titulo, hashtags, status="simulated_no_selenium")
            return False
        if not self.driver:
            print("❌ Driver não iniciado. Não é possível fazer posting real.")
            # self.simular_posting(video_file, titulo, hashtags, status="simulated_no_driver")
            return False

        try:
            print(f"📤 INICIANDO POSTING REAL: {os.path.basename(video_file)}")

            if not self.is_logged_in:
                print("❌ Não está logado. Tentando login antes de postar...")
                email = self.config.get('email')
                password = self.config.get('password')
                login_method = self.config.get('login_method', 'email')
                if not self.fazer_login_automatico(email, password, login_method=login_method):
                    print("❌ Falha ao tentar login para posting. Abortando posting real.")
                    return False


            print("🌐 Navegando para upload...")
            self.driver.get("https://www.tiktok.com/creator-center/upload")
            self.esperar_humano(3, 5)

            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file'], [data-e2e='upload-btn']"))
                )
                print("✅ Página de upload carregada")
            except:
                print("❌ Página de upload não carregou ou seletor mudou.")
                try:
                    upload_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-e2e='nav-upload'], button[data-e2e='upload-btn'], a[href*='/upload']"))
                    )
                    self.clicar_como_humano(upload_button)
                    self.esperar_humano(3, 5)
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
                    )
                    print("✅ Página de upload carregada via botão")
                except Exception as e_upload_btn:
                    print(f"❌ Não foi possível carregar página de upload. Erro: {e_upload_btn}")
                    self.registrar_post(video_file, titulo, hashtags, status="failed_upload_page")
                    return False


            if not self.fazer_upload_real(video_file):
                self.registrar_post(video_file, titulo, hashtags, status="failed_upload_file")
                return False

            if not self.aguardar_processamento():
                self.registrar_post(video_file, titulo, hashtags, status="failed_processing")
                return False

            if not self.preencher_dados_post(titulo, hashtags):
                self.registrar_post(video_file, titulo, hashtags, status="failed_caption")
                return False

            if not self.publicar_video_real():
                self.registrar_post(video_file, titulo, hashtags, status="failed_publish")
                return False

            print("🎉 VÍDEO POSTADO COM SUCESSO NO TIKTOK!")
            self.registrar_post(video_file, titulo, hashtags, status="posted")
            return True

        except Exception as e:
            print(f"❌ Erro no posting real: {e}")
            self.registrar_post(video_file, titulo, hashtags, status="failed_general")
            return False

    def fazer_upload_real(self, video_file):
        """Upload real do arquivo"""
        try:
            print("📁 Fazendo upload do arquivo...")

            file_input_selectors = [
                "input[type='file']",
                "input[accept*='video']",
                "[data-e2e='upload-input']",
                "//input[@type='file']",
                "//input[contains(@accept, 'video')]"
            ]

            file_input = None
            for selector in file_input_selectors:
                try:
                    if selector.startswith('//'):
                        file_input = self.driver.find_element(By.XPATH, selector)
                    else:
                        file_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue

            if not file_input:
                print("❌ Input de upload não encontrado")
                return False

            file_input.send_keys(os.path.abspath(video_file))
            print("✅ Arquivo enviado")
            self.esperar_humano(2, 4)

            return True

        except Exception as e:
            print(f"❌ Erro no upload: {e}")
            return False

    def aguardar_processamento(self):
        """Aguarda processamento do vídeo"""
        try:
            print("⏳ Aguardando processamento...")

            for i in range(60):
                try:
                    complete_indicators = [
                        "textarea[placeholder*='caption']",
                        "textarea[placeholder*='describe']",
                        "[data-e2e='caption-input']",
                        "//textarea[contains(@placeholder, 'Caption')]",
                        "//p[contains(text(), '100%')]",
                        "//div[contains(@class, 'progress-bar') and @data-e2e='video-upload-progress']//div[contains(@class, '100%')]",
                    ]

                    found_indicator = False
                    for indicator in complete_indicators:
                        try:
                            if indicator.startswith('//'):
                                element = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, indicator))
                                )
                            else:
                                element = WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.CSS_SELECTOR, indicator))
                                )
                            if element and element.is_displayed():
                                found_indicator = True
                                break
                        except:
                            continue

                    if found_indicator:
                        print("✅ Processamento concluído!")
                        self.esperar_humano(1, 2)
                        return True

                    print(f"⏳ Processando... ({i+1}/60)")
                    time.sleep(5)

                except TimeoutException:
                    continue
                except Exception as inner_e:
                    print(f"⚠️ Erro durante espera do processamento: {inner_e}")
                    continue

            print("❌ Timeout no processamento")
            return False

        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
            return False

    def preencher_dados_post(self, titulo, hashtags):
        """Preenche dados do post"""
        try:
            print("📝 Preenchendo dados do post...")

            texto_completo = titulo
            if hashtags:
                hashtags_text = " ".join(hashtags)
                if not texto_completo.endswith('\n') and not texto_completo.endswith(' '):
                    texto_completo += "\n"
                texto_completo += hashtags_text


            caption_selectors = [
                "textarea[placeholder*='caption']",
                "textarea[placeholder*='describe']",
                "[data-e2e='caption-input']",
                "div[contenteditable='true']",
                "//div[@role='textbox']",
                "//span[contains(text(), 'Legenda')]/following-sibling::div",
                "//div[contains(@class, 'DraftEditor-root')]"
            ]

            caption_field = None
            for selector in caption_selectors:
                try:
                    if selector.startswith('//'):
                        caption_field = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                    else:
                        caption_field = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                    if caption_field.is_displayed() and caption_field.is_enabled():
                        break
                    else:
                        caption_field = None
                except:
                    continue

            if not caption_field:
                print("❌ Campo de caption não encontrado ou não interativo")
                return False

            if caption_field.tag_name == 'textarea' or caption_field.tag_name == 'input':
                caption_field.clear()
            else:
                self.driver.execute_script("arguments[0].innerHTML = '';", caption_field)

            self.esperar_humano(0.5, 1)
            self.digitar_como_humano(caption_field, texto_completo)

            print("✅ Dados preenchidos!")
            return True

        except Exception as e:
            print(f"❌ Erro ao preencher dados: {e}")
            return False

    def publicar_video_real(self):
        """Publica o vídeo"""
        try:
            print("🚀 Publicando vídeo...")

            publish_selectors = [
                "button[data-e2e='publish-button']",
                "//button[contains(text(), 'Post')]",
                "//button[contains(text(), 'Publish')]",
                "//button[contains(text(), 'Publicar')]",
                "//button[contains(text(), 'Publicar vídeo')]",
                "//button[@type='submit' and contains(., 'Post')]",
            ]

            publish_button = None
            for selector in publish_selectors:
                try:
                    if selector.startswith('//'):
                        publish_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        publish_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    if publish_button.is_enabled() and publish_button.is_displayed():
                        break
                    else:
                        publish_button = None
                except:
                    continue

            if not publish_button:
                print("❌ Botão de publicar não encontrado ou desabilitado")
                return False

            self.clicar_como_humano(publish_button)
            self.esperar_humano(3, 5)

            print("⏳ Aguardando confirmação de publicação...")
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.not_in_url("creator-center/upload")
                )
                print("✅ Redirecionamento após publicação detectado.")
            except TimeoutException:
                print("⚠️ Não houve redirecionamento rápido após publicação. Verificando manualmente...")
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Seu vídeo foi publicado')] | //div[contains(text(), 'Video uploaded')] | //a[contains(@href, 'tiktok.com/@')]"))
                    )
                    print("✅ Mensagem de sucesso ou link de perfil encontrado!")
                except:
                    print("⚠️ Nenhuma confirmação explícita de publicação encontrada. Assumindo sucesso.")


            print("✅ Vídeo publicado!")
            return True

        except Exception as e:
            print(f"❌ Erro ao publicar: {e}")
            return False

    def simular_posting(self, video_file, titulo, hashtags=None, status="simulated"):
        """Simula posting para teste (sem Selenium ou em caso de erro real)"""
        try:
            print(f"🎬 SIMULANDO POSTING (sem navegador ou fallback)")
            print(f"📁 Vídeo: {os.path.basename(video_file)}")
            print(f"📝 Título: {titulo}")
            if hashtags:
                print(f"🏷️ Hashtags: {' '.join(hashtags)}")

            print("⏳ Simulando upload...")
            for i in range(5):
                time.sleep(1)
                print(f"   Upload: {(i+1)*20}%")

            self.registrar_post(video_file, titulo, hashtags, status=status)

            print("✅ POST SIMULADO COM SUCESSO!")
            print("💡 Para posting real, certifique-se de que Chrome/Selenium estão configurados e suas credenciais em tiktok_config.py.")

            return True

        except Exception as e:
            print(f"❌ Erro na simulação: {e}")
            return False

    def posting_manual_instructions(self, video_file, titulo, hashtags=None):
        """Instruções para posting manual"""
        print("\n" + "="*60)
        print("📱 INSTRUÇÕES PARA POSTING MANUAL NO TIKTOK")
        print("="*60)

        print(f"📁 Vídeo pronto: {video_file}")
        print(f"📝 Título sugerido: {titulo}")
        if hashtags:
            print(f"🏷️ Hashtags: {' '.join(hashtags)}")

        print("\n🎯 PASSOS MANUAIS:")
        print("1. Abra TikTok no celular ou web")
        print("2. Clique em '+' (Criar)")
        print("3. Faça upload do vídeo")
        print("4. Cole o título e hashtags")
        print("5. Publique o vídeo")

        print(f"\n📍 Localização do vídeo:")
        print(f"   {os.path.abspath(video_file)}")

        self.registrar_post(video_file, titulo, hashtags, status="manual_pending")

        print("\n✅ Instruções geradas! Vídeo registrado como 'pendente manual'")

    def registrar_post(self, video_file, titulo, hashtags, status="posted"):
        """Registra post no log"""
        try:
            post_data = {
                'timestamp': datetime.now().isoformat(),
                'video_file': os.path.basename(video_file),
                'video_path': video_file,
                'titulo': titulo,
                'hashtags': hashtags or [],
                'status': status,
                'file_size_mb': round(os.path.getsize(video_file) / 1024 / 1024, 2) if os.path.exists(video_file) else 0
            }

            posts_log = []
            if os.path.exists(self.posts_log_file):
                with open(self.posts_log_file, 'r', encoding='utf-8') as f:
                    try:
                        posts_log = json.load(f)
                    except json.JSONDecodeError:
                        print("⚠️ Erro ao ler posts_log.json. Criando novo log.")
                        posts_log = []

            posts_log.append(post_data)

            if len(posts_log) > 100:
                posts_log = posts_log[-100:]

            with open(self.posts_log_file, 'w', encoding='utf-8') as f:
                json.dump(posts_log, f, indent=2, ensure_ascii=False)

            print("📊 Post registrado no log!")

        except Exception as e:
            print(f"⚠️ Erro ao registrar post: {e}")

    def listar_posts_pendentes(self):
        """Lista posts pendentes de posting manual"""
        try:
            if not os.path.exists(self.posts_log_file):
                print("📋 Nenhum post registrado ainda")
                return []

            with open(self.posts_log_file, 'r', encoding='utf-8') as f:
                try:
                    posts_log = json.load(f)
                except json.JSONDecodeError:
                    print("⚠️ Erro ao ler posts_log.json. Nenhum post pendente encontrado.")
                    return []

            posts_pendentes = [p for p in posts_log if p.get('status') == 'manual_pending']

            if posts_pendentes:
                print(f"📋 {len(posts_pendentes)} POSTS PENDENTES:")
                print("="*50)

                for i, post in enumerate(posts_pendentes, 1):
                    print(f"{i}. {post['titulo']}")
                    print(f"   📁 {post['video_file']}")
                    print(f"   🕐 {post['timestamp']}")
                    print(f"   🏷️ {' '.join(post.get('hashtags', []))}")
                    print(f"   📍 Caminho: {post['video_path']}")
                    print()
            else:
                print("✅ Nenhum post pendente")

            return posts_pendentes

        except Exception as e:
            print(f"❌ Erro ao listar posts: {e}")
            return []

    def esperar_humano(self, min_sec=1, max_sec=3):
        """Simula tempo de espera humano"""
        wait_time = random.uniform(min_sec, max_sec)
        time.sleep(wait_time)

    def clicar_como_humano(self, element):
        """Clique humanizado"""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            self.esperar_humano(0.5, 1)

            element.click()
            self.esperar_humano(0.5, 1.5)

        except Exception as e:
            print(f"⚠️ Erro no clique: {e}. Tentando via JavaScript.")
            try:
                self.driver.execute_script("arguments[0].click();", element)
                self.esperar_humano(0.5, 1.5)
            except Exception as js_e:
                print(f"❌ Falha no clique JavaScript também: {js_e}")
                raise

    def digitar_como_humano(self, element, text):
        """Digitação humanizada"""
        try:
            element.click()
            self.esperar_humano(0.2, 0.5)

            for char in text:
                element.send_keys(char)
                time.sleep(random.uniform(0.05, 0.2))

            self.esperar_humano(0.3, 0.8)

        except Exception as e:
            print(f"⚠️ Erro na digitação: {e}. Tentando digitar tudo de uma vez.")
            try:
                if element.tag_name == 'textarea' or element.tag_name == 'input':
                    element.clear()
                    element.send_keys(text)
                else:
                    self.driver.execute_script("arguments[0].innerHTML = arguments[1];", element, text)
                self.esperar_humano(0.3, 0.8)
            except Exception as fb_e:
                print(f"❌ Falha na digitação fallback também: {fb_e}")
                raise


    def salvar_sessao(self):
        """Salva sessão para reutilizar"""
        try:
            session_data = {
                'cookies': self.driver.get_cookies(),
                'current_url': self.driver.current_url,
                'timestamp': datetime.now().isoformat(),
                'is_logged_in': self.is_logged_in
            }

            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            print("💾 Sessão salva!")

        except Exception as e:
            print(f"⚠️ Erro ao salvar sessão: {e}")

    def fechar(self):
        """Fecha o driver se existir"""
        try:
            if self.driver:
                self.driver.quit()
                print("🔒 Driver fechado")
        except:
            pass

# Teste do sistema
if __name__ == "__main__":
    print("🧪 TESTANDO TIKTOK POSTER")
    print("==================================================")

    EMAIL_TIKTOK = TIKTOK_CONFIG.get('email')
    SENHA_TIKTOK = TIKTOK_CONFIG.get('password')
    LOGIN_METHOD = TIKTOK_CONFIG.get('login_method', 'email')

    # Definir o diretório temporário para o perfil do Chrome
    temp_user_data_dir = os.path.join(os.getcwd(), 'chrome_temp_profile')

    poster = TikTokPoster()

    videos_dir = "../media/videos"
    ultimo_video = None
    if os.path.exists(videos_dir):
        videos = [f for f in os.listdir(videos_dir) if f.endswith('.mp4')]
        if videos:
            ultimo_video = os.path.join(videos_dir, sorted(videos)[-1])
            print(f"🎥 Último vídeo encontrado: {os.path.basename(ultimo_video)}")
        else:
            print("❌ Nenhum vídeo encontrado em ../media/videos para teste.")
    else:
        print("❌ Pasta de vídeos '../media/videos' não encontrada.")


    print("\n🎯 OPÇÕES DE TESTE:")
    print("1. Simular posting (sem navegador)")
    print("2. Instruções para posting manual")
    print("3. Tentar posting automático real (prioriza cookies, pede credenciais se necessário)")
    print("4. Listar posts pendentes")
    print("5. Testar login automático (prioriza cookies, pede credenciais se necessário)")


    opcao = input("\nEscolha uma opção (1-5): ").strip()

    try:
        if opcao == "1":
            if ultimo_video:
                poster.simular_posting(
                    ultimo_video,
                    "Teste de Vídeo Automático (Simulado) 🔥",
                    ["#teste", "#automation", "#viral"]
                )
            else:
                print("⚠️ Não há vídeo para simular. Gere um vídeo primeiro.")

        elif opcao == "2":
            if ultimo_video:
                poster.posting_manual_instructions(
                    ultimo_video,
                    "Vídeo Incrível Gerado por IA! 🤖",
                    ["#ia", "#viral", "#curiosidades"]
                )
            else:
                print("⚠️ Não há vídeo para instruções manuais. Gere um vídeo primeiro.")

        elif opcao == "3":
            if not poster.selenium_available:
                print("❌ Selenium não está disponível. Não é possível tentar posting automático.")
            elif not ultimo_video:
                print("⚠️ Nenhum vídeo encontrado para posting automático. Gere um vídeo primeiro.")
            else:
                if poster.criar_driver_para_producao(user_data_dir=temp_user_data_dir):
                    print("✅ Driver criado.")
                    if not poster.fazer_login_automatico(EMAIL_TIKTOK, SENHA_TIKTOK, login_method=LOGIN_METHOD):
                        print("❌ Falha no login para posting automático. Verifique as credenciais ou o arquivo de sessão.")
                        poster.fechar()
                        exit(1)

                    print("✅ Logado. Tentando posting real...")
                    # Certifique-se de que ultimo_video é passado aqui
                    success = poster.postar_video_real(
                        ultimo_video, # <<-- Certifique-se que o vídeo é passado para o método
                        "Vídeo Incrível Gerado por IA! 🤖🔥",
                        ["#ia", "#viral", "#automation", "#fyp", "#brasil"]
                    )
                    if success:
                        print("🎉 Posting automático finalizado com sucesso!")
                    else:
                        print("❌ Posting automático falhou.")
                else:
                    print("❌ Falha ao criar driver. Posting automático não disponível.")

        elif opcao == "4":
            poster.listar_posts_pendentes()

        elif opcao == "5":
            if not poster.selenium_available:
                print("❌ Selenium não está disponível. Não é possível testar login automático.")
            else:
                if poster.criar_driver_para_producao(user_data_dir=temp_user_data_dir):
                    print(f"✅ Driver criado. Testando login com método: {LOGIN_METHOD}")
                    if poster.fazer_login_automatico(EMAIL_TIKTOK, SENHA_TIKTOK, login_method=LOGIN_METHOD):
                        print("✅ Teste de login automático bem-sucedido!")
                    else:
                        print("❌ Teste de login automático falhou. Verifique as credenciais ou o arquivo de sessão.")
                else:
                    print("❌ Falha ao criar driver para teste de login.")

        else:
            print("❌ Opção inválida")

    except KeyboardInterrupt:
        print("\n⚠️ Interrompido pelo usuário")
    finally:
        poster.fechar()
        # Limpar o diretório temporário após a execução (garante limpeza)
        if os.path.exists(temp_user_data_dir):
            try:
                shutil.rmtree(temp_user_data_dir)
                print(f"🧹 Diretório temporário {temp_user_data_dir} limpo.")
            except Exception as e:
                print(f"❌ Erro ao limpar diretório temporário {temp_user_data_dir}: {e}")