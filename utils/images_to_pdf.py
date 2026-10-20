from PIL import Image
import io
import base64


def imagesB64_to_pdfB64(images_base64: list):
    """
    Convierte una lista de imágenes en base64 a un PDF en base64
    
    Args:
        images_base64: Lista de strings base64 de imágenes (resultado de base64.b64encode(screenshotByte).decode('utf-8'))
        
    Returns:
        str: PDF en formato base64
    """
    try:
        images = []
        
        for img_base64 in images_base64:
            # Decodificar base64 a bytes
            image_bytes = base64.b64decode(img_base64)
            
            # Convertir bytes a imagen PIL
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convertir a RGB si es necesario (PDF solo soporta RGB)
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            elif image.mode != 'RGB':
                image = image.convert('RGB')
                
            images.append(image)
        
        # Crear PDF en memoria
        pdf_buffer = io.BytesIO()
        
        if len(images) == 1:
            # PDF de una sola página
            images[0].save(
                pdf_buffer, 
                format='PDF', 
                resolution=100.0,
                quality=95
            )
        else:
            # PDF con múltiples páginas
            images[0].save(
                pdf_buffer,
                format='PDF',
                resolution=100.0,
                save_all=True,
                append_images=images[1:],
                quality=95
            )
        
        # Obtener bytes del PDF y convertir a base64
        pdf_bytes = pdf_buffer.getvalue()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        return pdf_base64
        
    except Exception as e:
        print(f"Error convirtiendo base64 images a PDF: {str(e)}")
        return None