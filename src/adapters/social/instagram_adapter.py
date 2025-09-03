# src/adapters/social/instagram_adapter.py

"""
Módulo do Adaptador de Publicação no Instagram.

Este arquivo contém a implementação concreta da `SocialMediaPublisherPort`
para interagir com a API de Publicação de Conteúdo do Instagram Graph.

Ele utiliza uma classe interna `_InstagramPublisherInternal`, adaptada
diretamente da FONTE ÚNICA DA VERDADE, para encapsular as chamadas
de baixo nível à API.
"""

import logging
import time
from typing import Any, Dict, List, Optional

import requests

from src.core.domain.entities import Post
from src.core.domain.enums import MediaType, PostType
from src.ports.social_publisher import SocialMediaPublisherPort

logger = logging.getLogger(__name__)


# --- Exceções Internas e Públicas (Baseadas na FONTE ÚNICA DA VERDADE) ---

class _InstagramApiError(Exception):
    """Exceção interna para erros específicos da API do Instagram."""
    def __init__(self, message, code=None, subcode=None, user_title=None, user_msg=None):
        super().__init__(message)
        self.code = code
        self.subcode = subcode
        self.user_title = user_title
        self.user_msg = user_msg

    def __str__(self):
        return (f"{super().__str__()} (Code: {self.code}, Subcode: {self.subcode}, "
                f"Title: '{self.user_title}', Message: '{self.user_msg}')")

class InstagramPublicationError(Exception):
    """Exceção pública levantada pelo adaptador em caso de falha na publicação."""
    pass


# --- Classe Interna de Lógica da API (Baseada na FONTE ÚNICA DA VERDADE) ---

class _InstagramPublisherInternal:
    """
    Classe interna que encapsula a lógica de interação com a Instagram Graph API.
    Adaptada diretamente do código de exemplo fornecido.
    """
    def __init__(self, account_id: str, access_token: str, api_version: str = "v20.0"):
        if not account_id or not access_token:
            raise ValueError("ID da conta do Instagram e token de acesso são obrigatórios.")
        self.account_id = account_id
        self.access_token = access_token
        self.base_url = f"https://graph.facebook.com/{api_version}"
        logger.info(f"_InstagramPublisherInternal inicializado para a conta ID: {self.account_id}")
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        all_params = {'access_token': self.access_token, **(params or {})}
        try:
            logger.debug(f"Fazendo requisição: {method} {url} com params: {params}")
            response = requests.request(method, url, params=all_params, timeout=180)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json().get('error', {})
            logger.error(f"Erro HTTP da API do Instagram: {e.response.status_code} - {error_data}")
            raise _InstagramApiError(
                message=error_data.get('message', 'Erro desconhecido da API'),
                code=error_data.get('code'), subcode=error_data.get('error_subcode'),
                user_title=error_data.get('error_user_title'), user_msg=error_data.get('error_user_msg')
            ) from e
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão/rede ao chamar a API do Instagram: {e}")
            raise

    def _create_media_container(self, media_url: str, media_type: str, caption: str, is_carousel_item: bool = False) -> str:
        endpoint = f"/{self.account_id}/media"
        params = {
            'caption': caption,
            'is_carousel_item': is_carousel_item
        }
        if media_type == 'IMAGE':
            params['image_url'] = media_url
        else: # VIDEO ou REELS
            params['media_type'] = 'VIDEO'
            params['video_url'] = media_url
        
        response = self._make_request('POST', endpoint, params=params)
        container_id = response.get('id')
        if not container_id:
            raise _InstagramApiError(f"Falha ao criar contêiner de mídia. Resposta: {response}")
        logger.info(f"Contêiner de mídia ({media_type}) criado com sucesso. ID: {container_id}")
        return container_id

    def _wait_for_container_status(self, container_id: str) -> bool:
        start_time = time.time()
        while time.time() - start_time < 180: # 3 min timeout
            response = self._make_request('GET', f"/{container_id}", params={'fields': 'status_code'})
            status = response.get('status_code')
            logger.debug(f"Status do contêiner {container_id}: {status}")
            if status == 'FINISHED':
                logger.info(f"Contêiner {container_id} processado e pronto.")
                return True
            if status in ('ERROR', 'EXPIRED'):
                raise _InstagramApiError(f"Processamento do contêiner {container_id} falhou com status '{status}'.")
            time.sleep(10)
        raise _InstagramApiError(f"Timeout esperando pelo contêiner {container_id}.")

    def _publish_container(self, creation_id: str) -> str:
        endpoint = f"/{self.account_id}/media_publish"
        params = {'creation_id': creation_id}
        response = self._make_request('POST', endpoint, params=params)
        media_id = response.get('id')
        if not media_id:
            raise _InstagramApiError(f"Falha na publicação do contêiner {creation_id}. Resposta: {response}")
        logger.info(f"Conteúdo publicado com sucesso! Media ID: {media_id}")
        return media_id

    def publish_single_image(self, image_url: str, caption: str) -> str:
        container_id = self._create_media_container(image_url, 'IMAGE', caption)
        self._wait_for_container_status(container_id)
        return self._publish_container(container_id)

    def publish_video(self, video_url: str, caption: str) -> str:
        container_id = self._create_media_container(video_url, 'VIDEO', caption)
        self._wait_for_container_status(container_id)
        return self._publish_container(container_id)
        
    def publish_carousel(self, items: List[Dict[str, str]], caption: str) -> str:
        if not 2 <= len(items) <= 10:
            raise ValueError(f"Carrossel deve ter entre 2 e 10 itens, mas {len(items)} foram fornecidos.")
        
        child_container_ids = []
        for item in items:
            media_type = 'IMAGE' if item['type'] == MediaType.IMAGE else 'VIDEO'
            container_id = self._create_media_container(item['url'], media_type, caption, is_carousel_item=True)
            child_container_ids.append(container_id)
        
        for cid in child_container_ids:
            self._wait_for_container_status(cid)
            
        carousel_params = {
            'media_type': 'CAROUSEL',
            'caption': caption,
            'children': ",".join(child_container_ids)
        }
        response = self._make_request('POST', f"/{self.account_id}/media", params=carousel_params)
        carousel_container_id = response.get('id')
        if not carousel_container_id:
            raise _InstagramApiError(f"Falha ao criar contêiner de carrossel. Resposta: {response}")

        self._wait_for_container_status(carousel_container_id)
        return self._publish_container(carousel_container_id)


# --- Adaptador Público que implementa a Porta ---

class InstagramAdapter(SocialMediaPublisherPort):
    """
    Adaptador que implementa a `SocialMediaPublisherPort` para o Instagram.

    Este adaptador atua como uma fachada (Facade), utilizando uma classe interna
    (`_InstagramPublisherInternal`) para lidar com as complexidades da API,
    e mapeia a entidade de domínio `Post` para as chamadas de publicação corretas.
    """

    def __init__(self, account_id: str, access_token: str):
        """
        Inicializa o adaptador do Instagram.

        Args:
            account_id (str): ID da Conta Profissional do Instagram.
            access_token (str): Token de Acesso da Meta com as permissões necessárias.
        """
        try:
            self._publisher = _InstagramPublisherInternal(
                account_id=account_id,
                access_token=access_token
            )
        except ValueError as e:
            raise InstagramPublicationError(f"Erro de configuração do adaptador: {e}") from e

    async def publish(self, post: Post) -> str:
        """
        Publica um post do nosso domínio no Instagram.

        Mapeia o `post.post_type` para a função de publicação apropriada.

        Args:
            post (Post): A entidade `Post` a ser publicada.

        Returns:
            str: O ID da publicação no Instagram.

        Raises:
            InstagramPublicationError: Se ocorrer qualquer erro durante o processo.
            NotImplementedError: Se o `post.post_type` não for suportado.
        """
        logger.info(f"Iniciando publicação no Instagram para o post ID: {post.id} (Tipo: {post.post_type.value})")
        
        try:
            if post.post_type == PostType.SINGLE_IMAGE:
                if not post.media:
                    raise InstagramPublicationError("Post de imagem única não contém mídia.")
                image_url = post.media[0].url
                return self._publisher.publish_single_image(image_url, post.text_content)
            
            elif post.post_type == PostType.CAROUSEL:
                if len(post.media) < 2:
                    raise InstagramPublicationError("Post de carrossel deve conter ao menos 2 mídias.")
                items = [{'type': m.media_type, 'url': m.url} for m in post.media]
                return self._publisher.publish_carousel(items, post.text_content)

            elif post.post_type == PostType.VIDEO:
                if not post.media:
                    raise InstagramPublicationError("Post de vídeo não contém mídia.")
                video_url = post.media[0].url
                return self._publisher.publish_video(video_url, post.text_content)

            else:
                raise NotImplementedError(f"O tipo de post '{post.post_type.value}' não é suportado pelo InstagramAdapter.")

        except (_InstagramApiError, requests.exceptions.RequestException, ValueError) as e:
            logger.error(f"Falha ao publicar post ID {post.id} no Instagram: {e}", exc_info=True)
            raise InstagramPublicationError(f"Erro na API do Instagram: {e}") from e