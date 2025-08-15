# /var/www/tiktok-automation/backend/trending_content_system.py

from config_manager import get_config
import requests
import json
import os
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv
import hashlib
from typing import List, Dict, Optional
import re
from collections import Counter
import logging
import time

# Configurar logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Importa a configuração global

# Carrega as configurações globais
config = get_config()


class RateLimiter:
    """Sistema de controle de rate limiting para APIs"""

    def __init__(self):
        self.api_calls = {}
        self.limits = {
            'youtube': {'calls': 0, 'max_per_hour': 100, 'last_reset': datetime.now()},
            'news': {'calls': 0, 'max_per_hour': 500, 'last_reset': datetime.now()},
            'reddit': {'calls': 0, 'max_per_hour': 60, 'last_reset': datetime.now()},
            'twitter': {'calls': 0, 'max_per_hour': 300, 'last_reset': datetime.now()}
        }

    def can_make_request(self, api_name: str) -> bool:
        """Verifica se pode fazer uma requisição para a API"""
        if api_name not in self.limits:
            return True

        limit_info = self.limits[api_name]
        now = datetime.now()

        # Reset contador se passou 1 hora
        if now - limit_info['last_reset'] > timedelta(hours=1):
            limit_info['calls'] = 0
            limit_info['last_reset'] = now

        # Verificar se ainda pode fazer requests
        if limit_info['calls'] >= limit_info['max_per_hour']:
            logger.warning(
                f"Rate limit atingido para {api_name}. Calls: {limit_info['calls']}")
            return False

        return True

    def record_request(self, api_name: str):
        """Registra uma requisição feita"""
        if api_name in self.limits:
            self.limits[api_name]['calls'] += 1
            logger.debug(
                f"{api_name} API: {self.limits[api_name]['calls']}/{self.limits[api_name]['max_per_hour']} calls")

    def wait_if_needed(self, api_name: str, min_interval: float = 1.0):
        """Adiciona delay entre requests se necessário"""
        time.sleep(min_interval)


class TrendingContentSystem:
    def __init__(self):
        # Rate limiter
        self.rate_limiter = RateLimiter()

        # Diretórios de cache
        self.data_dir = config.BASE_DIR / 'data'
        self.trends_cache_file = self.data_dir / 'trending_cache.json'
        self.used_topics_file = self.data_dir / 'used_topics.json'
        self.keywords_cache_file = self.data_dir / 'keywords_cache.json'

        # Configurações de cache AUMENTADAS para reduzir chamadas
        self.max_cache_hours = config.TRENDING_MAX_CACHE_HOURS
        self.max_used_topics = config.TRENDING_MAX_USED_TOPICS

        # APIs
        self.news_api_key = config.NEWS_API_KEY
        self.youtube_api_key = config.YOUTUBE_API_KEY
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

        # Categorias e palavras-chave para TikTok
        self.categorias_virais = {
            'curiosidades': {
                'keywords': ['sabia que', 'você não sabia', 'fato curioso', 'incrível', 'surpreendente'],
                'weight': 1.2
            },
            'ciencia': {
                'keywords': ['ciência', 'pesquisa', 'descoberta', 'experimento', 'estudo', 'cientistas'],
                'weight': 1.1
            },
            'tecnologia': {
                'keywords': ['tecnologia', 'inteligência artificial', 'ia', 'robô', 'inovação', 'futuro'],
                'weight': 1.3
            },
            'historia': {
                'keywords': ['história', 'antigo', 'passado', 'civilização', 'arqueologia', 'descoberto'],
                'weight': 1.0
            },
            'natureza': {
                'keywords': ['natureza', 'animal', 'planeta', 'oceano', 'floresta', 'meio ambiente'],
                'weight': 1.1
            },
            'espaço': {
                'keywords': ['espaço', 'nasa', 'planeta', 'estrela', 'galáxia', 'universo', 'astronauta'],
                'weight': 1.2
            },
            'misterios': {
                'keywords': ['mistério', 'inexplicável', 'enigma', 'estranho', 'bizarro', 'sobrenatural'],
                'weight': 1.4
            }
        }

        # Palavras que aumentam viralidade MAXIMIZADA para TikTok
        self.viral_boosters = [
            'incrível', 'chocante', 'surpreendente', 'bizarro', 'misterioso',
            'secreto', 'revelado', 'descoberto', 'nunca antes visto', 'impressionante',
            'inacreditável', 'extraordinário', 'fascinante', 'assustador', 'único',
            # NOVOS BOOSTERS ESPECÍFICOS PARA TIKTOK
            'explodiu', 'viral', 'bomba', 'destruiu', 'arrasou', 'histórico',
            'primeira vez', 'record mundial', 'impossível', 'lendário', 'épico',
            'vai te deixar', 'não acredita', 'mudou tudo', 'revolucionou',
            'ninguém esperava', 'todos ficaram', 'mundo parou', 'sem palavras'
        ]

        # Palavras a evitar (conteúdo sensível)
        self.blacklist_words = [
            'morte', 'morreu', 'acidente', 'tragédia', 'violência', 'crime',
            'política', 'polêmico', 'controvérsia', 'escândalo', 'covid', 'pandemia'
        ]

        # NOVO: Filtros para conteúdo musical
        self.music_blacklist = [
            # Termos musicais genéricos
            'feat', 'ft', 'featuring', 'música', 'musica', 'song', 'album', 'álbum',
            'single', 'ep', 'clipe', 'clip', 'videoclipe', 'lançamento oficial',
            'official video', 'official music', 'lyric video', 'letra',
            # Gêneros musicais
            'sertanejo', 'funk', 'forró', 'pagode', 'samba', 'rap', 'hip hop',
            'pop', 'rock', 'eletrônica', 'dance', 'reggae', 'country',
            # Termos de produção musical
            'remix', 'cover', 'acústico', 'ao vivo', 'live', 'show', 'tour',
            'dj', 'mc', 'producer', 'beat', 'instrumental', 'karaoke',
            # Padrões comuns de títulos musicais
            'lança', 'novo hit', 'sucesso', 'top charts', 'hits', 'playlist'
        ]

        # Padrões regex para detectar música
        self.music_patterns = [
            r'@\w+',  # Menções de artistas (@artista)
            r'\b\w+\s*&\s*\w+',  # Colaborações (Artista & Artista)
            r'\b\w+\s*,\s*@\w+',  # Listas de artistas
            r'MC\s+\w+',  # MCs
            r'DJ\s+\w+',  # DJs
            r'\([^)]*[Cc]lipe[^)]*\)',  # (Clipe Oficial)
            r'\([^)]*[Oo]fficial[^)]*\)',  # (Official Video)
            r'\b[A-Z]{2,}\s+MANDA\b',  # Padrão "OS BRUTO MANDA"
            r'\bMEU\s+\w+\s+É\b',  # Padrão "MEU ... É"
        ]

        # Criar diretório de dados se não existir
        os.makedirs(self.data_dir, exist_ok=True)

        logger.info("Sistema de Trending Content inicializado")

    def obter_trending_topics(self) -> List[Dict]:
        """Obtém trending topics de múltiplas fontes"""
        # Verificar cache primeiro
        cached_trends = self._carregar_cache()
        if cached_trends:
            logger.info(
                f"Usando cache com {len(cached_trends)} trending topics")
            return cached_trends

        logger.info("Buscando novos trending topics...")
        all_trends = []

        # Coletar de todas as fontes disponíveis
        sources = [
            ("Reddit", self._buscar_reddit_trends),
            ("YouTube", self._buscar_youtube_trends),
            ("News API", self._buscar_news_trends),
            ("Twitter", self._buscar_twitter_trends),
            ("Google Trends", self._buscar_google_trends_rss)
        ]

        for source_name, source_func in sources:
            try:
                trends = source_func()
                if trends:
                    all_trends.extend(trends)
                    logger.info(f"✅ {len(trends)} trends de {source_name}")
            except Exception as e:
                logger.warning(f"⚠️ Erro ao buscar {source_name}: {str(e)}")

        # Se não conseguiu nenhum trend, usar fallback
        if not all_trends:
            logger.warning("Nenhuma API disponível, usando fallback topics")
            all_trends = self._gerar_fallback_topics()

        # Processar e filtrar trends
        trending_topics = self._processar_trends(all_trends)

        # Salvar em cache
        self._salvar_cache(trending_topics)

        logger.info(
            f"Total de {len(trending_topics)} trending topics processados")
        return trending_topics

    def _buscar_reddit_trends(self) -> List[Dict]:
        """Busca posts populares do Reddit Brasil"""
        if not self.reddit_client_id or not self.reddit_client_secret:
            return []

        # Verificar rate limit
        if not self.rate_limiter.can_make_request('reddit'):
            logger.warning("Reddit API: Rate limit atingido, pulando busca")
            return []

        try:
            # Delay para evitar spam
            self.rate_limiter.wait_if_needed('reddit', 2.0)

            # Autenticar no Reddit
            auth_url = "https://www.reddit.com/api/v1/access_token"
            auth_data = {
                'grant_type': 'client_credentials'
            }
            auth_response = requests.post(
                auth_url,
                auth=(self.reddit_client_id, self.reddit_client_secret),
                data=auth_data,
                headers={'User-Agent': 'TikTokBot/1.0'},
                timeout=10
            )

            self.rate_limiter.record_request('reddit')

            if auth_response.status_code != 200:
                return []

            token = auth_response.json()['access_token']

            # Buscar posts populares
            headers = {
                'Authorization': f'bearer {token}',
                'User-Agent': 'TikTokBot/1.0'
            }

            trends = []
            subreddits = ['brasil', 'InternetBrasil',
                          'todayilearned', 'science', 'technology']

            for subreddit in subreddits:
                # Verificar rate limit antes de cada subreddit
                if not self.rate_limiter.can_make_request('reddit'):
                    logger.warning(
                        f"Reddit API: Rate limit atingido em {subreddit}")
                    break

                self.rate_limiter.wait_if_needed('reddit', 1.0)

                url = f"https://oauth.reddit.com/r/{subreddit}/hot"
                params = {'limit': 5}  # Reduzido de 10 para 5

                response = requests.get(
                    url, headers=headers, params=params, timeout=10)
                self.rate_limiter.record_request('reddit')

                if response.status_code == 200:
                    data = response.json()

                    for post in data['data']['children']:
                        post_data = post['data']
                        if post_data['score'] > 100:  # Posts com boa pontuação
                            trends.append({
                                'topic': post_data['title'],
                                'source': 'reddit',
                                'score': min(100, 50 + (post_data['score'] // 100)),
                                'url': f"https://reddit.com{post_data['permalink']}",
                                'categoria': self._categorizar_topico(post_data['title'])
                            })

            return trends

        except Exception as e:
            logger.error(f"Erro Reddit API: {e}")
            return []

    def _buscar_youtube_trends(self) -> List[Dict]:
        """Busca vídeos trending no YouTube Brasil"""
        if not self.youtube_api_key:
            return []

        # Verificar rate limit
        if not self.rate_limiter.can_make_request('youtube'):
            logger.warning("YouTube API: Rate limit atingido, pulando busca")
            return []

        try:
            self.rate_limiter.wait_if_needed('youtube', 1.0)

            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                'part': 'snippet,statistics',
                'chart': 'mostPopular',
                'regionCode': 'BR',
                'maxResults': 15,  # Reduzido de 25 para 15
                'key': self.youtube_api_key
            }

            response = requests.get(url, params=params, timeout=15)
            self.rate_limiter.record_request('youtube')

            if response.status_code == 200:
                data = response.json()
                trends = []

                for video in data.get('items', []):
                    title = video['snippet']['title']
                    view_count = int(video['statistics'].get('viewCount', 0))

                    # Filtrar vídeos relevantes
                    if view_count > 50000 and not self._contem_blacklist(title) and not self._eh_conteudo_musical(title):
                        # Score baseado em visualizações
                        score = min(95, 60 + (view_count // 100000))

                        trends.append({
                            'topic': title,
                            'source': 'youtube',
                            'score': score,
                            'views': view_count,
                            'video_id': video['id'],
                            'categoria': self._categorizar_topico(title)
                        })

                return trends
            else:
                logger.warning(
                    f"YouTube API retornou status {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Erro YouTube API: {e}")
            return []

    def _buscar_news_trends(self) -> List[Dict]:
        """Busca notícias trending no Brasil com parâmetros otimizados"""
        if not self.news_api_key:
            return []

        # Verificar rate limit
        if not self.rate_limiter.can_make_request('news'):
            logger.warning("News API: Rate limit atingido, pulando busca")
            return []

        try:
            # Endpoint otimizado com múltiplas consultas virais
            url = "https://newsapi.org/v2/everything"

            # CONSULTAS ESTRATÉGICAS PARA CONTEÚDO VIRAL (REDUZIDAS)
            consultas_virais = [
                # Reduzido de 5 para 3 consultas para economizar requests
                '+descoberta +científica OR +tecnologia +revolucionária',
                '+mistério OR +fenômeno +inexplicável OR +descoberta +arqueológica',
                '+nasa OR +espaço OR +planeta OR +astronomia'
            ]

            all_trends = []

            for i, consulta in enumerate(consultas_virais):
                # Verificar rate limit antes de cada consulta
                if not self.rate_limiter.can_make_request('news'):
                    logger.warning(
                        f"News API: Rate limit atingido na consulta {i+1}")
                    break

                self.rate_limiter.wait_if_needed('news', 0.5)

                params = {
                    'q': consulta,
                    'language': 'pt',  # Português
                    'sortBy': 'popularity',  # Mais populares primeiro
                    'searchIn': 'title,description',  # Buscar no título e descrição
                    'pageSize': 8,  # Reduzido de 10 para 8
                    'apiKey': self.news_api_key,
                    # Últimos 7 dias para garantir relevância
                    'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                }

                response = requests.get(url, params=params, timeout=15)
                self.rate_limiter.record_request('news')

                if response.status_code == 200:
                    data = response.json()

                    for article in data.get('articles', []):
                        title = article.get('title', '')
                        description = article.get('description', '')

                        if title and not self._contem_blacklist(title) and not self._eh_conteudo_musical(title):
                            # Combinar título e descrição para melhor contexto
                            full_text = f"{title} {description or ''}"

                            # Score baseado na popularidade da fonte
                            score = 75

                            # Boost se contém palavras virais no título
                            if any(palavra in title.lower() for palavra in self.viral_boosters):
                                score += 10

                            # Boost se é de fonte confiável
                            source_name = article.get(
                                'source', {}).get('name', '').lower()
                            if any(fonte in source_name for fonte in ['bbc', 'cnn', 'g1', 'folha', 'estadao']):
                                score += 5

                            all_trends.append({
                                'topic': title,
                                'source': 'news',
                                'score': min(score, 95),
                                'url': article.get('url'),
                                'published_at': article.get('publishedAt'),
                                'categoria': self._categorizar_topico(full_text),
                                'source_name': article.get('source', {}).get('name', 'Desconhecido')
                            })
                elif response.status_code == 429:
                    logger.warning("News API: Rate limit detectado (429)")
                    break
                else:
                    logger.warning(
                        f"News API: Status {response.status_code} na consulta {i+1}")

            return all_trends

        except Exception as e:
            logger.error(f"Erro News API: {e}")
            return []

    def _buscar_twitter_trends(self) -> List[Dict]:
        """Busca trending topics do Twitter Brasil"""
        if not self.twitter_bearer_token:
            return []

        # Verificar rate limit
        if not self.rate_limiter.can_make_request('twitter'):
            logger.warning("Twitter API: Rate limit atingido, pulando busca")
            return []

        try:
            self.rate_limiter.wait_if_needed('twitter', 1.0)

            # WOEID do Brasil = 23424768
            url = "https://api.twitter.com/1.1/trends/place.json"
            headers = {
                'Authorization': f'Bearer {self.twitter_bearer_token}'
            }
            params = {'id': 23424768}  # Brasil

            response = requests.get(
                url, headers=headers, params=params, timeout=15)

            self.rate_limiter.record_request('twitter')

            if response.status_code == 200:
                data = response.json()
                trends = []

                if data and len(data) > 0:
                    # Reduzido de 20 para 15
                    for trend in data[0].get('trends', [])[:15]:
                        name = trend['name']

                        # Filtrar hashtags e mentions
                        if not name.startswith('#') and not name.startswith('@'):
                            if not self._contem_blacklist(name):
                                tweet_volume = trend.get('tweet_volume', 0)
                                score = min(
                                    90, 70 + (tweet_volume // 10000)) if tweet_volume else 70

                                trends.append({
                                    'topic': name,
                                    'source': 'twitter',
                                    'score': score,
                                    'tweet_volume': tweet_volume,
                                    'categoria': self._categorizar_topico(name)
                                })

                return trends
            else:
                logger.warning(
                    f"Twitter API retornou status {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Erro Twitter API: {e}")
            return []

    def _buscar_google_trends_rss(self) -> List[Dict]:
        """Busca Google Trends via RSS (não requer API key)"""
        try:
            import feedparser

            url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=BR"
            feed = feedparser.parse(url)

            trends = []
            for entry in feed.entries[:15]:
                title = entry.title

                if not self._contem_blacklist(title):
                    trends.append({
                        'topic': title,
                        'source': 'google_trends',
                        'score': 85,
                        'published': entry.get('published'),
                        'categoria': self._categorizar_topico(title)
                    })

            return trends

        except Exception as e:
            logger.error(f"Erro Google Trends RSS: {e}")
            return []

    def _gerar_fallback_topics(self) -> List[Dict]:
        """Gera tópicos de fallback baseados em templates SUPER VIRAIS para TikTok"""
        # TEMPLATES COMPROVADAMENTE VIRAIS
        templates_virais = [
            "5 {categoria} que vão EXPLODIR sua mente",
            "O SEGREDO {categoria} que NINGUÉM te conta",
            "CIENTISTAS descobrem {categoria} IMPOSSÍVEL",
            "A VERDADE sobre {categoria} que vai te CHOCAR",
            "Por que {categoria} está deixando TODOS em choque?",
            "O MISTÉRIO de {categoria} FINALMENTE revelado",
            "ISSO vai MUDAR tudo sobre {categoria}",
            "RECORD MUNDIAL: {categoria} nunca visto antes",
            "VIRAL: {categoria} que DESTRUIU a internet",
            "BIZARRO: {categoria} que ninguém consegue explicar",
            "LENDÁRIO: {categoria} que fez história",
            "ÉPICO: {categoria} mais impressionante do mundo"
        ]

        # TÓPICOS ESPECÍFICOS ULTRA VIRAIS
        topicos_ultra_virais = [
            "buracos negros que comem galáxias",
            "civilizações perdidas no oceano",
            "animais que voltaram da extinção",
            "fenômenos que a ciência não explica",
            "invenções que mudaram a humanidade",
            "lugares proibidos no Google Maps",
            "descobertas que reescreveram a história",
            "recordes humanos impossíveis",
            "experimentos científicos secretos",
            "tecnologias que vêm do futuro",
            "mistérios do espaço profundo",
            "códigos antigos nunca decifrados",
            "criaturas das profundezas do mar",
            "dimensões paralelas comprovadas",
            "energia infinita descoberta"
        ]

        trends = []
        for _ in range(15):  # Mais tópicos de fallback
            template = random.choice(templates_virais)
            topico = random.choice(topicos_ultra_virais)

            # Escolher categoria com maior peso viral
            categoria_viral = random.choices(
                list(self.categorias_virais.keys()),
                weights=[info['weight']
                         for info in self.categorias_virais.values()]
            )[0]

            title = template.replace('{categoria}', topico)

            trends.append({
                'topic': title,
                'source': 'fallback_viral',
                # Scores mais altos para fallback
                'score': random.randint(75, 95),
                'categoria': categoria_viral,
                'is_viral_template': True
            })

        return trends

    def _categorizar_topico(self, texto: str) -> str:
        """Categoriza um tópico baseado em palavras-chave"""
        texto_lower = texto.lower()
        scores = {}

        for categoria, info in self.categorias_virais.items():
            score = 0
            for keyword in info['keywords']:
                if keyword in texto_lower:
                    score += info['weight']

            if score > 0:
                scores[categoria] = score

        if scores:
            return max(scores, key=scores.get)

        return 'curiosidades'  # Categoria padrão

    def _contem_blacklist(self, texto: str) -> bool:
        """Verifica se o texto contém palavras da blacklist"""
        texto_lower = texto.lower()
        return any(word in texto_lower for word in self.blacklist_words)

    def _eh_conteudo_musical(self, texto: str) -> bool:
        """Detecta se o conteúdo é musical/artístico"""
        texto_lower = texto.lower()

        # Verificar palavras musicais ESPECÍFICAS com delimitadores
        music_keywords_found = []
        for word in self.music_blacklist:
            # Usar delimitadores de palavra para evitar falsos positivos
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, texto_lower):
                music_keywords_found.append(word)

        # Se encontrou palavras musicais, verificar se não é falso positivo
        if music_keywords_found:
            # Palavras que podem ser ambíguas (como "tecnologia")
            ambiguous_words = ['tecnologia', 'inteligência',
                               'artificial', 'descoberta', 'ciência']

            # Se só tem palavras ambíguas e não tem outros indicadores musicais, não é música
            if all(word in ambiguous_words for word in music_keywords_found):
                # Verificar se tem outros indicadores musicais fortes
                has_strong_music_indicators = (
                    any(re.search(r'\b' + re.escape(pattern) + r'\b', texto_lower)
                        for pattern in ['feat', 'ft', 'featuring', 'clipe', 'lançamento']) or
                    re.search(r'@\w+', texto) or  # Menções
                    re.search(r'\bmc\s+\w+', texto_lower) or  # MCs
                    re.search(r'\bdj\s+\w+', texto_lower)     # DJs
                )
                if not has_strong_music_indicators:
                    return False
            else:
                return True

        # Verificar padrões regex FORTES
        strong_music_patterns = [
            r'@\w+',  # Menções de artistas (@artista)
            r'\bMC\s+\w+',  # MCs
            r'\bDJ\s+\w+',  # DJs
            r'\([^)]*[Cc]lipe[^)]*\)',  # (Clipe Oficial)
            r'\([^)]*[Oo]fficial[^)]*\)',  # (Official Video)
            r'\([^)]*[Ll]ançamento[^)]*\)',  # (Lançamento Oficial)
            r'\bfeat\b|\bft\b|\bfeaturing\b',  # Colaborações
        ]

        for pattern in strong_music_patterns:
            if re.search(pattern, texto, re.IGNORECASE):
                return True

        # Verificar estrutura típica: "ARTISTA - MÚSICA (Clipe)"
        if re.search(r'\w+\s*-\s*[A-Z\s]+\([^)]*[Cc]lipe[^)]*\)', texto):
            return True

        # Padrão "MEU ... É" (muito comum no funk)
        if re.search(r'\bMEU\s+\w+\s+É\b', texto, re.IGNORECASE):
            return True

        return False

    def _processar_trends(self, all_trends: List[Dict]) -> List[Dict]:
        """Processa, filtra e rankeia trends"""
        # Filtrar trends válidos
        trends_validos = []

        for trend in all_trends:
            # Validações básicas
            if (len(trend['topic']) < 10 or
                len(trend['topic']) > 150 or
                self._contem_blacklist(trend['topic']) or
                    self._eh_conteudo_musical(trend['topic'])):  # NOVO: Filtrar música
                continue

            # Calcular score viral
            trend['viral_score'] = self._calcular_score_viral(trend)

            # Adicionar timestamp
            trend['timestamp'] = datetime.now().isoformat()

            trends_validos.append(trend)

        # Remover duplicatas
        trends_unicos = self._remover_duplicatas(trends_validos)

        # Ordenar por score viral
        trends_ranqueados = sorted(
            trends_unicos, key=lambda x: x['viral_score'], reverse=True)

        # Retornar top 20
        return trends_ranqueados[:20]

    def _calcular_score_viral(self, trend: Dict) -> float:
        """Calcula score de viralidade OTIMIZADO para TikTok"""
        score = trend.get('score', 50)
        texto = trend['topic'].lower()

        # BOOST MASSIVO por palavras virais (aumentado de 1.2 para 1.5)
        viral_multiplier = 1.0
        for palavra in self.viral_boosters:
            if palavra in texto:
                viral_multiplier *= 1.4  # Boost maior para viral boosters

        score *= viral_multiplier

        # SUPER BOOST por categoria (aumentar peso dos mistérios)
        categoria = trend.get('categoria', 'curiosidades')
        if categoria in self.categorias_virais:
            categoria_weight = self.categorias_virais[categoria]['weight']
            # Mistérios recebem boost extra
            if categoria == 'misterios':
                categoria_weight *= 1.3  # Boost adicional para mistérios
            score *= categoria_weight

        # BOOST PREMIUM por fonte (Google Trends é ouro)
        source_weights = {
            'google_trends': 1.4,    # Máximo boost - Google Trends é viral
            'youtube': 1.3,          # YouTube trends são altamente virais
            'reddit': 1.25,          # Reddit tem conteúdo engajado
            'twitter': 1.2,          # Twitter trends são rápidos
            'news': 1.1,             # News é mais conservadora
            'fallback_viral': 1.35,  # Fallback viral recebe boost alto
            'fallback': 0.9          # Fallback normal recebe penalidade
        }

        source = trend.get('source', 'fallback')
        score *= source_weights.get(source, 1.0)

        # BOOST por números no título (listas funcionam no TikTok)
        if re.search(r'\b\d+\b', trend['topic']):
            score *= 1.15

        # BOOST por palavras em MAIÚSCULA (chamam atenção)
        maiusculas = len(re.findall(r'\b[A-Z]{2,}\b', trend['topic']))
        if maiusculas > 0:
            score *= (1.1 + (maiusculas * 0.05))  # Cada palavra em caps = +5%

        # BOOST por pontos de exclamação (emoção)
        exclamacoes = trend['topic'].count('!')
        if exclamacoes > 0:
            score *= (1.05 + (exclamacoes * 0.03))

        # PENALIDADE por tamanho (títulos muito longos performam pior no TikTok)
        if len(trend['topic']) > 70:  # Reduzido de 80 para 70
            score *= 0.85
        elif len(trend['topic']) < 30:  # Muito curtos também perdem
            score *= 0.9

        # BOOST especial para templates virais comprovados
        if trend.get('is_viral_template'):
            score *= 1.2

        return min(100, score)

    def _remover_duplicatas(self, trends: List[Dict]) -> List[Dict]:
        """Remove trends duplicados ou muito similares"""
        trends_unicos = []
        topics_vistos = set()

        for trend in trends:
            # Criar hash do tópico normalizado
            topico_norm = re.sub(r'[^\w\s]', '', trend['topic'].lower())
            palavras = set(topico_norm.split())

            # Verificar similaridade
            is_duplicate = False
            for topico_visto in topics_vistos:
                palavras_visto = set(topico_visto.split())

                # Se compartilham mais de 50% das palavras, considerar duplicata
                intersecao = len(palavras.intersection(palavras_visto))
                uniao = len(palavras.union(palavras_visto))

                if uniao > 0 and (intersecao / uniao) > 0.5:
                    is_duplicate = True
                    break

            if not is_duplicate:
                trends_unicos.append(trend)
                topics_vistos.add(topico_norm)

        return trends_unicos

    def obter_trending_com_filtros(self, categoria=None, min_score=70, limit=20) -> List[Dict]:
        """Versão melhorada com filtros específicos para frontend"""
        try:
            todos_topics = self.obter_trending_topics()

            # Aplicar filtros
            topics_filtrados = todos_topics

            if categoria:
                topics_filtrados = [
                    t for t in topics_filtrados if t['categoria'] == categoria]

            if min_score:
                topics_filtrados = [t for t in topics_filtrados if t.get(
                    'viral_score', 0) >= min_score]

            # Ordenar por score viral
            topics_filtrados = sorted(
                topics_filtrados, key=lambda x: x.get('viral_score', 0), reverse=True)

            # Limitar resultados
            return topics_filtrados[:limit]

        except Exception as e:
            logger.error(f"Erro ao aplicar filtros: {e}")
            return []

    def get_trending_por_categoria(self) -> Dict[str, List[Dict]]:
        """Retorna trending topics agrupados por categoria"""
        try:
            todos_topics = self.obter_trending_topics()

            topics_por_categoria = {}
            for categoria in self.categorias_virais.keys():
                cat_topics = [
                    t for t in todos_topics if t['categoria'] == categoria]
                # Ordenar por score viral
                cat_topics = sorted(cat_topics, key=lambda x: x.get(
                    'viral_score', 0), reverse=True)
                # Top 5 por categoria
                topics_por_categoria[categoria] = cat_topics[:5]

            return topics_por_categoria

        except Exception as e:
            logger.error(f"Erro ao agrupar por categoria: {e}")
            return {}

    def gerar_titulo_viral(self, topico_base: str, categoria: str = None) -> str:
        """Gera título viral otimizado baseado em um tópico"""
        try:
            # Templates específicos por categoria
            templates_categoria = {
                'misterios': [
                    "O MISTÉRIO de {topico} que EXPLODIU a internet!",
                    "BIZARRO: {topico} que NINGUÉM consegue explicar!",
                    "INEXPLICÁVEL: {topico} deixa cientistas em CHOQUE!"
                ],
                'tecnologia': [
                    "IA REVELA: {topico} vai REVOLUCIONAR tudo!",
                    "FUTURO: {topico} que parece IMPOSSÍVEL!",
                    "TECNOLOGIA: {topico} que mudou o MUNDO!"
                ],
                'ciencia': [
                    "CIENTISTAS descobrem {topico} IMPOSSÍVEL!",
                    "EXPERIÊNCIA com {topico} deu MUITO errado!",
                    "DESCOBERTA: {topico} reescreve a ciência!"
                ]
            }

            # Templates gerais virais
            templates_gerais = [
                "5 fatos sobre {topico} que vão EXPLODIR sua mente!",
                "A VERDADE sobre {topico} que NINGUÉM te conta!",
                "VIRAL: {topico} que DESTRUIU a internet!",
                "PRIMEIRA VEZ: {topico} nunca visto antes!",
                "RECORD: {topico} mais INSANO do planeta!"
            ]

            # Escolher template
            if categoria and categoria in templates_categoria:
                templates = templates_categoria[categoria]
            else:
                templates = templates_gerais

            titulo = random.choice(templates).format(topico=topico_base)

            return titulo

        except Exception as e:
            logger.error(f"Erro ao gerar título viral: {e}")
            return topico_base

    def avaliar_potencial_viral(self, texto: str) -> Dict:
        """Avalia o potencial viral de um texto/título"""
        try:
            score = 50  # Score base
            detalhes = {
                'score_base': 50,
                'boosts': [],
                'penalidades': [],
                'recomendacoes': []
            }

            texto_lower = texto.lower()

            # Verificar viral boosters
            viral_count = 0
            for palavra in self.viral_boosters:
                if palavra in texto_lower:
                    viral_count += 1
                    score += 8
                    detalhes['boosts'].append(
                        f"Palavra viral: '{palavra}' (+8)")

            # Verificar categoria
            categoria = self._categorizar_topico(texto)
            categoria_weight = self.categorias_virais[categoria]['weight']
            categoria_boost = (categoria_weight - 1) * 100
            score += categoria_boost
            detalhes['boosts'].append(
                f"Categoria '{categoria}': +{categoria_boost:.1f}")

            # Verificar estrutura
            if re.search(r'\b\d+\b', texto):
                score += 10
                detalhes['boosts'].append("Contém números (+10)")

            maiusculas = len(re.findall(r'\b[A-Z]{2,}\b', texto))
            if maiusculas > 0:
                boost = maiusculas * 5
                score += boost
                detalhes['boosts'].append(
                    f"Palavras em CAPS: {maiusculas} (+{boost})")

            exclamacoes = texto.count('!')
            if exclamacoes > 0:
                boost = exclamacoes * 3
                score += boost
                detalhes['boosts'].append(
                    f"Exclamações: {exclamacoes} (+{boost})")

            # Penalidades
            if len(texto) > 70:
                penalidade = 10
                score -= penalidade
                detalhes['penalidades'].append(
                    f"Muito longo: {len(texto)} chars (-{penalidade})")
                detalhes['recomendacoes'].append(
                    "Reduza o tamanho do título para 70 caracteres")

            if len(texto) < 30:
                penalidade = 5
                score -= penalidade
                detalhes['penalidades'].append(
                    f"Muito curto: {len(texto)} chars (-{penalidade})")
                detalhes['recomendacoes'].append(
                    "Aumente o tamanho do título para pelo menos 30 caracteres")

            # Verificar blacklist
            blacklist_encontrada = []
            for palavra in self.blacklist_words:
                if palavra in texto_lower:
                    blacklist_encontrada.append(palavra)
                    score -= 20
                    detalhes['penalidades'].append(
                        f"Palavra sensível: '{palavra}' (-20)")

            if blacklist_encontrada:
                detalhes['recomendacoes'].append(
                    "Evite palavras sensíveis para melhor alcance")

            # Recomendações gerais
            if viral_count == 0:
                detalhes['recomendacoes'].append(
                    "Adicione palavras virais como: INCRÍVEL, CHOCANTE, DESCOBERTO")

            if maiusculas == 0:
                detalhes['recomendacoes'].append(
                    "Use algumas palavras em MAIÚSCULA para chamar atenção")

            if exclamacoes == 0:
                detalhes['recomendacoes'].append(
                    "Adicione pontos de exclamação para mais emoção!")

            detalhes['score_final'] = max(0, min(100, score))
            detalhes['categoria_detectada'] = categoria
            detalhes['viral_words_count'] = viral_count

            return detalhes

        except Exception as e:
            logger.error(f"Erro ao avaliar potencial viral: {e}")
            return {'score_final': 0, 'erro': str(e)}

    def obter_topico_para_roteiro(self) -> Dict:
        """Obtém o próximo tópico trending para criar roteiro"""
        try:
            # Obter todos os trending topics
            trending_topics = self.obter_trending_topics()

            if not trending_topics:
                logger.warning("Nenhum trending topic disponível")
                return self._gerar_fallback_topics()[0]

            # Carregar tópicos já usados
            used_topics = self._carregar_topicos_usados()

            # Filtrar tópicos não usados
            topics_disponiveis = []
            for topic in trending_topics:
                topic_hash = self._gerar_hash_topico(topic['topic'])
                if topic_hash not in used_topics:
                    topics_disponiveis.append(topic)

            # Se todos foram usados, resetar lista
            if not topics_disponiveis:
                logger.info("Todos os topics foram usados, resetando lista")
                self._limpar_topicos_usados()
                topics_disponiveis = trending_topics

            # Escolher o melhor tópico disponível
            topico_escolhido = topics_disponiveis[0]

            # Marcar como usado
            self._marcar_topico_usado(topico_escolhido['topic'])

            # Adicionar informações extras
            topico_escolhido['keywords'] = self._extrair_keywords(
                topico_escolhido['topic'])
            topico_escolhido['hook_suggestion'] = self._gerar_hook_suggestion(
                topico_escolhido)

            logger.info(f"Tópico escolhido: {topico_escolhido['topic']}")
            logger.info(f"Categoria: {topico_escolhido['categoria']}")
            logger.info(f"Score Viral: {topico_escolhido['viral_score']}")

            return topico_escolhido

        except Exception as e:
            logger.error(f"Erro ao obter tópico: {e}")
            return self._gerar_fallback_topics()[0]

    def _extrair_keywords(self, texto: str) -> List[str]:
        """Extrai palavras-chave relevantes do texto"""
        # Remover pontuação e converter para lowercase
        texto_limpo = re.sub(r'[^\w\s]', '', texto.lower())
        palavras = texto_limpo.split()

        # Remover stopwords básicas
        stopwords = {'o', 'a', 'de', 'da', 'do', 'em', 'no',
                     'na', 'que', 'e', 'é', 'para', 'com', 'um', 'uma'}
        palavras_filtradas = [
            p for p in palavras if p not in stopwords and len(p) > 2]

        # Contar frequência
        word_freq = Counter(palavras_filtradas)

        # Retornar top 5 palavras
        return [word for word, _ in word_freq.most_common(5)]

    def _gerar_hook_suggestion(self, topico: Dict) -> str:
        """Gera sugestão de hook ULTRA VIRAL para TikTok"""
        # HOOKS COMPROVADAMENTE VIRAIS
        hooks_ultra_virais = [
            "VOCÊ NÃO VAI ACREDITAR no que descobriram sobre {keyword}!",
            "A VERDADE sobre {keyword} que NINGUÉM te conta...",
            "CIENTISTAS em CHOQUE: {keyword} desafia tudo!",
            "ISSO vai MUDAR tudo que você sabe sobre {keyword}!",
            "Por que {keyword} está deixando TODOS sem palavras?",
            "O MISTÉRIO de {keyword} que EXPLODIU a internet!",
            "PRIMEIRA VEZ na história: {keyword} impressionante!",
            "VIRAL: {keyword} que NINGUÉM consegue explicar!",
            "RECORD MUNDIAL: {keyword} nunca visto antes!",
            "BIZARRO: {keyword} que desafia a ciência!",
            "ÉPICO: {keyword} mais INSANO do planeta!",
            "CHOCANTE: {keyword} que mudou TUDO!",
            "LENDÁRIO: {keyword} que fez HISTÓRIA!",
            "IMPOSSÍVEL: {keyword} que quebrou a internet!"
        ]

        # HOOKS por categoria específica
        hooks_por_categoria = {
            'misterios': [
                "O MISTÉRIO de {keyword} que NINGUÉM consegue resolver!",
                "INEXPLICÁVEL: {keyword} que desafia a ciência!",
                "BIZARRO: {keyword} que vai te dar ARREPIOS!"
            ],
            'tecnologia': [
                "IA REVELA: {keyword} vai REVOLUCIONAR tudo!",
                "FUTURO: {keyword} que parece IMPOSSÍVEL!",
                "TECNOLOGIA: {keyword} que mudou o MUNDO!"
            ],
            'ciencia': [
                "CIENTISTAS descobrem {keyword} IMPOSSÍVEL!",
                "EXPERIÊNCIA com {keyword} deu MUITO errado!",
                "DESCOBERTA: {keyword} reescreve a ciência!"
            ],
            'espaço': [
                "NASA ESCONDE: {keyword} no espaço é REAL!",
                "ASTRONAUTAS veem {keyword} IMPOSSÍVEL!",
                "ESPAÇO: {keyword} que NASA não quer que você saiba!"
            ]
        }

        keywords = topico.get('keywords', [])
        categoria = topico.get('categoria', 'curiosidades')

        if keywords:
            keyword = keywords[0].upper() if len(
                keywords[0]) > 3 else keywords[0]
        else:
            # Extrair palavra principal do tópico
            palavras = topico['topic'].split()
            palavra_principal = max(palavras, key=len) if palavras else "ISSO"
            keyword = palavra_principal.upper()

        # Escolher hook baseado na categoria
        if categoria in hooks_por_categoria:
            hook_templates = hooks_por_categoria[categoria] + \
                hooks_ultra_virais
        else:
            hook_templates = hooks_ultra_virais

        hook = random.choice(hook_templates).format(keyword=keyword)

        # Adicionar emojis para mais impacto visual
        emoji_por_categoria = {
            'misterios': '🔮',
            'tecnologia': '🤖',
            'ciencia': '🧬',
            'espaço': '🚀',
            'curiosidades': '🤯',
            'natureza': '🌊',
            'historia': '🏛️'
        }

        emoji = emoji_por_categoria.get(categoria, '⚡')
        hook = f"{emoji} {hook}"

        return hook

    def _gerar_hash_topico(self, topico: str) -> str:
        """Gera hash único para um tópico"""
        topico_norm = re.sub(r'[^\w\s]', '', topico.lower()).strip()
        return hashlib.md5(topico_norm.encode()).hexdigest()

    def _carregar_cache(self) -> Optional[List[Dict]]:
        """Carrega cache de trending topics"""
        try:
            if self.trends_cache_file.exists():
                with open(self.trends_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)

                # Verificar validade do cache
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                if datetime.now() - cache_time < timedelta(hours=self.max_cache_hours):
                    return cache_data['trends']

            return None
        except Exception as e:
            logger.error(f"Erro ao carregar cache: {e}")
            return None

    def _salvar_cache(self, trends: List[Dict]):
        """Salva trends em cache"""
        try:
            cache_data = {
                'timestamp': datetime.now().isoformat(),
                'trends': trends
            }

            with open(self.trends_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")

    def _carregar_topicos_usados(self) -> set:
        """Carrega lista de hashes de tópicos já usados"""
        try:
            if self.used_topics_file.exists():
                with open(self.used_topics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data.get('used_hashes', []))
            return set()
        except Exception as e:
            logger.error(f"Erro ao carregar tópicos usados: {e}")
            return set()

    def _marcar_topico_usado(self, topico: str):
        """Marca tópico como usado"""
        try:
            used_hashes = self._carregar_topicos_usados()
            topic_hash = self._gerar_hash_topico(topico)
            used_hashes.add(topic_hash)

            # Converter para lista e manter apenas os últimos N
            used_list = list(used_hashes)
            if len(used_list) > self.max_used_topics:
                used_list = used_list[-self.max_used_topics:]

            with open(self.used_topics_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'used_hashes': used_list,
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Erro ao marcar tópico usado: {e}")

    def _limpar_topicos_usados(self):
        """Limpa lista de tópicos usados"""
        try:
            with open(self.used_topics_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'used_hashes': [],
                    'last_updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
            logger.info("Lista de tópicos usados foi resetada")
        except Exception as e:
            logger.error(f"Erro ao limpar tópicos: {e}")

    def get_analytics(self) -> Dict:
        """Retorna analytics sobre os trending topics"""
        try:
            trends = self.obter_trending_topics()
            used_topics = self._carregar_topicos_usados()

            # Análise por categoria
            categoria_count = Counter(t['categoria'] for t in trends)

            # Análise por fonte
            source_count = Counter(t['source'] for t in trends)

            # Score médio por categoria
            categoria_scores = {}
            for cat in self.categorias_virais.keys():
                cat_trends = [t for t in trends if t['categoria'] == cat]
                if cat_trends:
                    categoria_scores[cat] = sum(
                        t['viral_score'] for t in cat_trends) / len(cat_trends)

            return {
                'total_trends': len(trends),
                'used_topics': len(used_topics),
                'trends_by_category': dict(categoria_count),
                'trends_by_source': dict(source_count),
                'avg_score_by_category': categoria_scores,
                'top_viral_score': max(t['viral_score'] for t in trends) if trends else 0,
                'cache_age_hours': self._get_cache_age()
            }

        except Exception as e:
            logger.error(f"Erro ao gerar analytics: {e}")
            return {}

    def _get_cache_age(self) -> float:
        """Retorna idade do cache em horas"""
        try:
            if self.trends_cache_file.exists():
                with open(self.trends_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    cache_time = datetime.fromisoformat(
                        cache_data['timestamp'])
                    age = datetime.now() - cache_time
                    return age.total_seconds() / 3600
            return 0
        except:
            return 0
