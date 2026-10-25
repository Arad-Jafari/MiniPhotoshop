from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
import os
import json
import tempfile
import uuid
from .utils import ImageProcessor


# ============================================
# MAIN PAGE
# ============================================

def index(request):
    """Render the photo editor page"""
    context = {'is_authenticated': request.user.is_authenticated}
    if request.user.is_authenticated:
        context['username'] = request.user.get_username()
    else:
        context['username'] = ''
    return render(request, 'editor/index.html', context)


def _normalize_effects(raw_effects):
    normalized = []
    for effect_item in raw_effects or []:
        if isinstance(effect_item, str):
            normalized.append({'name': effect_item, 'params': {}})
        elif isinstance(effect_item, dict):
            if not effect_item.get('name'):
                continue
            normalized.append({
                'name': effect_item.get('name'),
                'params': effect_item.get('params', {}) or {}
            })
    return normalized


def _save_image_to_storage(image, filename):
    file_ext = os.path.splitext(filename)[1].lower() or '.jpg'
    encoded = ImageProcessor.imencode_bytes(image, file_ext)
    return default_storage.save(f'uploads/{filename}', ContentFile(encoded))


def serve_media(request, media_path):
    try:
        file_obj = default_storage.open(media_path)
        content = file_obj.read()
        mime_type = 'application/octet-stream'
        if media_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp')):
            mime_type = {
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.webp': 'image/webp',
                '.bmp': 'image/bmp',
            }.get(os.path.splitext(media_path)[1].lower(), mime_type)
        return HttpResponse(content, content_type=mime_type)
    except Exception:
        return HttpResponseNotFound('Media not found')


def _apply_effect_list(image, raw_effects):
    filter_params = {
        'blur': False,
        'kernel_size_blur': 5,
        'gaussian_blur': False,
        'kernel_size_gaussian': 5,
        'sharpen': False,
        'median_blur': False,
        'kernel_size_median': 5,
        'flip': False,
        'flip_code': 1,
        'rotate': False,
        'angle': 90,
        'auto_crop': True,
        'resize': False,
        'width': None,
        'height': None,
        'brightness': False,
        'brightness_value': 30,
        'contrast': False,
        'contrast_value': 1.5,
        'grayscale': False,
        'sepia': False,
        'gaussian_noise': False,
        'sigma': 20,
    }

    for effect_item in _normalize_effects(raw_effects):
        effect_name = effect_item.get('name')
        effect_values = effect_item.get('params', {}) or {}
        if not effect_name:
            continue

        filter_params[effect_name] = True

        if effect_name == 'blur':
            filter_params['kernel_size_blur'] = int(effect_values.get('kernel_size_blur', 5))
        elif effect_name == 'gaussian_blur':
            filter_params['kernel_size_gaussian'] = int(effect_values.get('kernel_size_gaussian', 5))
        elif effect_name == 'median_blur':
            filter_params['kernel_size_median'] = int(effect_values.get('kernel_size_median', 5))
        elif effect_name == 'flip':
            filter_params['flip_code'] = int(effect_values.get('flip_code', 1))
        elif effect_name == 'rotate':
            filter_params['angle'] = int(effect_values.get('angle', 90))
            ac = effect_values.get('auto_crop')
            if ac is not None:
                if isinstance(ac, str):
                    filter_params['auto_crop'] = ac.lower() in ('1', 'true', 'yes', 'y')
                else:
                    filter_params['auto_crop'] = bool(ac)
        elif effect_name == 'resize':
            width = effect_values.get('width')
            height = effect_values.get('height')
            if width is None or height is None:
                raise ValueError('Resize needs both width and height.')
            filter_params['width'] = int(width)
            filter_params['height'] = int(height)
        elif effect_name == 'brightness':
            filter_params['brightness_value'] = int(effect_values.get('brightness_value', 30))
        elif effect_name == 'contrast':
            filter_params['contrast_value'] = float(effect_values.get('contrast_value', 1.5))
        elif effect_name == 'gaussian_noise':
            filter_params['sigma'] = int(effect_values.get('sigma', 20))

    return ImageProcessor.apply_filters(image, **filter_params)


# ============================================
# API: UPLOAD IMAGE (USES IMREAD)
# ============================================

@csrf_exempt
def upload_image(request):
    """
    Upload image - saves to disk and reads with imread
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'})

    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=403)

    try:
        uploaded_file = request.FILES.get('image')
        if not uploaded_file:
            return JsonResponse({'status': 'error', 'message': 'No image provided'})

        allowed_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        file_mime = (uploaded_file.content_type or '').lower()
        allowed_mimes = {'image/jpeg', 'image/png', 'image/webp', 'image/bmp'}

        if file_ext not in allowed_exts and file_mime not in allowed_mimes:
            return JsonResponse({
                'status': 'error',
                'message': 'Unsupported file format. Please upload JPG, JPEG, PNG, WEBP, or BMP images.'
            }, status=400)

        filename = f"{uuid.uuid4().hex}{file_ext or '.jpg'}"
        image_bytes = uploaded_file.read()
        ImageProcessor.imread(image_bytes)

        stored_name = default_storage.save(f'uploads/{filename}', ContentFile(image_bytes))

        request.session['image_name'] = stored_name
        request.session['image_path'] = ''
        request.session['original_image_name'] = stored_name
        request.session['original_image_path'] = ''
        request.session['image_filename'] = filename
        request.session['original_image_filename'] = filename
        request.session['filter_history'] = []

        return JsonResponse({
            'status': 'success',
            'message': 'Image uploaded',
            'filename': filename,
            'image_url': default_storage.url(stored_name)
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ============================================
# API: APPLY FILTERS (USES IMREAD + IMWRITE)
# ============================================

@csrf_exempt
def apply_filters(request):
    """
    Apply one or more effects to the current image.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'})

    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=403)

    try:
        data = json.loads(request.body)

        raw_effects = data.get('effects') or []
        if isinstance(raw_effects, str):
            raw_effects = [raw_effects]

        if not raw_effects:
            effect = data.get('effect')
            if effect:
                raw_effects = [{'name': effect, 'params': data.get('params', {})}]

        if not raw_effects:
            return JsonResponse({'status': 'error', 'message': 'No effect selected.'})

        image_name = request.session.get('image_name') or request.session.get('image_path')
        if not image_name:
            return JsonResponse({'status': 'error', 'message': 'No image found. Please upload first.'})

        with default_storage.open(image_name, 'rb') as fh:
            img = ImageProcessor.imread(fh.read())
        result_img, applied = _apply_effect_list(img, raw_effects)

        original_filename = request.session.get('image_filename', 'result.jpg')
        _, original_ext = os.path.splitext(original_filename)
        original_ext = original_ext.lower() or '.jpg'
        unique_filename = f'edited_{uuid.uuid4().hex}{original_ext}'
        saved_name = _save_image_to_storage(result_img, unique_filename)

        session_history = request.session.get('filter_history', []) or []
        session_history.extend(_normalize_effects(raw_effects))
        request.session['filter_history'] = session_history
        request.session['image_name'] = saved_name
        request.session['image_path'] = ''
        request.session['image_filename'] = unique_filename

        return JsonResponse({
            'status': 'success',
            'applied_filters': applied,
            'image_url': default_storage.url(saved_name)
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@csrf_exempt
def remove_filter(request):
    """Remove a single filter and reapply the remaining ones to the original image."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'})

    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=403)

    try:
        data = json.loads(request.body)
        history = list(request.session.get('filter_history', []) or [])
        if not history:
            return JsonResponse({'status': 'error', 'message': 'No filters to remove.'})

        index = data.get('index')
        if index is not None:
            idx = int(index)
            if idx < 0 or idx >= len(history):
                return JsonResponse({'status': 'error', 'message': 'Filter index out of range.'})
            del history[idx]
        else:
            filter_name = data.get('filter_name')
            if not filter_name:
                return JsonResponse({'status': 'error', 'message': 'No filter selected.'})
            filtered = [entry for entry in history if entry.get('name') != filter_name]
            if len(filtered) == len(history):
                return JsonResponse({'status': 'error', 'message': 'Filter not found.'})
            history = filtered

        request.session['filter_history'] = history

        original_name = request.session.get('original_image_name')
        original_path = request.session.get('original_image_path')
        if not original_name and not original_path:
            return JsonResponse({'status': 'error', 'message': 'No original image found. Please upload first.'})

        original_path = original_path if original_path and os.path.exists(original_path) else default_storage.path(original_name)
        base_img = ImageProcessor.imread(original_path)
        result_img, applied = _apply_effect_list(base_img, history)

        original_filename = request.session.get('original_image_filename', 'result.jpg')
        _, original_ext = os.path.splitext(original_filename)
        original_ext = original_ext.lower() or '.jpg'
        unique_filename = f'edited_{uuid.uuid4().hex}{original_ext}'
        saved_name = _save_image_to_storage(result_img, unique_filename)

        request.session['image_name'] = saved_name
        request.session['image_path'] = default_storage.path(saved_name)
        request.session['image_filename'] = unique_filename

        return JsonResponse({
            'status': 'success',
            'applied_filters': applied,
            'image_url': default_storage.url(saved_name)
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ============================================
# API: RESET IMAGE
# ============================================

@csrf_exempt
def reset_image(request):
    """
    Restore the uploaded image as the current working image.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'})

    # Authentication check
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=403)

    try:
        original_image_name = request.session.get('original_image_name')
        original_image_path = request.session.get('original_image_path')
        if not original_image_name and not original_image_path:
            return JsonResponse({
                'status': 'error',
                'message': 'No original image found. Please upload first.'
            })

        if original_image_name:
            request.session['image_name'] = original_image_name
            request.session['image_path'] = default_storage.path(original_image_name)
            request.session['image_filename'] = request.session.get('original_image_filename', os.path.basename(original_image_name))
        else:
            request.session['image_path'] = original_image_path
            request.session['image_filename'] = request.session.get('original_image_filename', os.path.basename(original_image_path))
        request.session['filter_history'] = []

        return JsonResponse({
            'status': 'success',
            'image_url': default_storage.url(original_image_name) if original_image_name else f'/media/{os.path.basename(original_image_path)}'
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# ============================================
# API: SAVE IMAGE
# ============================================

@csrf_exempt
def save_image(request):
    """
    Return the path to the current image for download
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'})

    # Authentication check
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=403)

    try:
        image_name = request.session.get('image_name')
        image_path = request.session.get('image_path')
        if not image_name and not image_path:
            return JsonResponse({
                'status': 'error',
                'message': 'No image to save'
            })

        if image_name:
            filename = os.path.basename(image_name)
            image_url = default_storage.url(image_name)
        else:
            filename = os.path.basename(image_path)
            image_url = f'/media/{filename}'

        return JsonResponse({
            'status': 'success',
            'image_url': image_url,
            'filename': filename
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})