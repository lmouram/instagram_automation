# src/core/application/use_cases/edit_image.py

"""
Caso de Uso: Editar Imagem e Renderizar Texto.

Este módulo contém o caso de uso responsável por aplicar edições visuais a uma
imagem base e renderizar texto sobre ela, produzindo a imagem final para o post.
Ele encapsula a lógica de manipulação de imagem com Pillow e a renderização
baseada em template com Playwright.
"""

import base64
import logging
from io import BytesIO

from jinja2 import Environment, FileSystemLoader
from PIL import Image
from playwright.async_api import async_playwright

from src.core.application.contracts import ThemeContract
from src.core.domain.entities import RunContext
from src.ports.state_repository import StateRepositoryPort

logger = logging.getLogger(__name__)


async def edit_image_use_case(
    image_bytes: bytes,
    title: str,
    theme: ThemeContract,
    context: RunContext,
    state_repo: StateRepositoryPort,
) -> bytes:
    """
    Aplica uma máscara a uma imagem, salva o resultado e renderiza o título
    sobre ela usando um template HTML e Playwright.

    Este caso de uso é uma unidade de trabalho atômica que transforma uma imagem
    bruta em um post visual finalizado, seguindo as especificações de um tema.

    Args:
        image_bytes (bytes): Os dados binários da imagem original.
        title (str): O título a ser renderizado na imagem.
        theme (ThemeContract): O DTO do tema contendo todos os parâmetros visuais.
        context (RunContext): O contexto da execução do workflow.
        state_repo (StateRepositoryPort): A porta para salvar artefatos intermediários.

    Returns:
        bytes: Os dados binários da imagem final renderizada no formato
               especificado pelo tema (ex: JPEG, WEBP).
    """
    logger.info(f"Iniciando caso de uso 'edit_image' para o tema '{theme.theme_name}'.")

    # --- 1. Aplicar Máscara de Escurecimento ---
    logger.debug("Aplicando máscara de escurecimento na imagem base.")
    try:
        with Image.open(BytesIO(image_bytes)) as image:
            image_rgba = image.convert("RGBA")
            mask = Image.new("RGBA", image_rgba.size, (0, 0, 0, int(255 * theme.mask_opacity)))
            masked_image = Image.alpha_composite(image_rgba, mask)
    except Exception as e:
        logger.error("Falha ao aplicar a máscara na imagem.", exc_info=True)
        raise IOError(f"Não foi possível processar a imagem com Pillow: {e}") from e

    # --- 2. Salvar Imagem Intermediária com Máscara ---
    masked_buffer = BytesIO()
    # Converte para RGB para salvar como JPEG
    masked_image.convert("RGB").save(masked_buffer, format='JPEG', quality=95)
    masked_image_bytes = masked_buffer.getvalue()

    await state_repo.save_artifact(
        context, "post-image-masked.jpg", masked_image_bytes
    )
    logger.info("Imagem com máscara salva no estado atômico.")

    # --- 3. Preparar Ativos para Renderização ---
    logger.debug("Preparando ativos para renderização com Playwright.")
    # Codificar imagem com máscara e fonte em Base64 para embutir no HTML
    background_b64 = base64.b64encode(masked_image_bytes).decode('utf-8')
    
    try:
        with open(theme.font_title_path, "rb") as f:
            font_b64 = base64.b64encode(f.read()).decode('utf-8')
    except IOError as e:
        logger.error(f"Não foi possível ler o arquivo de fonte: {theme.font_title_path}", exc_info=True)
        raise

    # --- 4. Renderizar Imagem Final com Playwright ---
    logger.info("Iniciando renderização com Playwright...")
    try:
        env = Environment(loader=FileSystemLoader(theme.template_single_post_path.parent))
        template = env.get_template(theme.template_single_post_path.name)

        html_str = template.render(
            title=title,
            font_title_b64=font_b64,
            background_image_b64=background_b64,
            viewport_width=theme.viewport_width,
            viewport_height=theme.viewport_height
        )
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={
                'width': theme.viewport_width,
                'height': theme.viewport_height
            })
            await page.set_content(html_str, wait_until="networkidle")
            # Gera PNG para máxima estabilidade e qualidade, mantendo o canal alfa se houver
            screenshot_bytes_png = await page.screenshot(type='png')
            await browser.close()
        
        logger.info("Renderização com Playwright concluída com sucesso.")
    except Exception as e:
        logger.error("Ocorreu um erro durante a renderização com Playwright.", exc_info=True)
        # Recomenda-se instalar o playwright com `playwright install` se houver erro aqui
        raise RuntimeError(f"Falha na renderização com Playwright: {e}") from e

    # --- 5. Converter para o Formato de Saída Final ---
    logger.debug(f"Convertendo screenshot PNG para o formato final: {theme.output_format}")
    try:
        with Image.open(BytesIO(screenshot_bytes_png)) as final_image:
            # Garante que a imagem está em modo RGB para salvar em formatos como JPEG
            if final_image.mode == 'RGBA':
                final_image = final_image.convert('RGB')
            
            final_buffer = BytesIO()
            final_image.save(
                final_buffer,
                format=theme.output_format,
                quality=theme.output_quality
            )
            final_image_bytes = final_buffer.getvalue()
    except Exception as e:
        logger.error("Falha ao converter a imagem final para o formato de saída.", exc_info=True)
        raise IOError(f"Falha na conversão final da imagem: {e}") from e

    logger.info(f"Caso de uso 'edit_image' concluído. Tamanho final: {len(final_image_bytes) / 1024:.2f} KB.")
    return final_image_bytes