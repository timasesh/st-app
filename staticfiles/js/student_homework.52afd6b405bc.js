// Student Homework JavaScript
class StudentHomework {
    constructor() {
        this.initializeEventListeners();
        this.setupDragAndDrop();
        this.setupFormValidation();
    }

    initializeEventListeners() {
        // Предварительный просмотр
        const previewBtn = document.getElementById('preview-btn');
        if (previewBtn) {
            previewBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.showPreview();
            });
        }

        // Удаление фотографий
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-photo-btn')) {
                e.preventDefault();
                const photoId = e.target.dataset.photoId;
                this.deletePhoto(photoId);
            }
        });

        // Модальные окна
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('photo-view-btn')) {
                e.preventDefault();
                const photoUrl = e.target.dataset.photoUrl;
                const description = e.target.dataset.description || '';
                this.openPhotoModal(photoUrl, description);
            }
        });
    }

    setupDragAndDrop() {
        const dropZone = document.getElementById('file-upload-area');
        if (!dropZone) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('dragover');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('dragover');
            });
        });

        dropZone.addEventListener('drop', (e) => {
            const dt = e.dataTransfer;
            const files = dt.files;
            this.handleFiles(files);
        });
    }

    setupFormValidation() {
        const form = document.getElementById('homework-form');
        if (!form) return;

        form.addEventListener('submit', (e) => {
            if (!this.validateForm()) {
                e.preventDefault();
                return false;
            }
        });
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleFiles(files) {
        const fileInput = document.getElementById('photos');
        const selectedFiles = document.getElementById('selected-files');
        const photoDescriptions = document.getElementById('photo-descriptions');
        const submitBtn = document.getElementById('submit-btn');

        if (!fileInput || !selectedFiles || !photoDescriptions) return;

        selectedFiles.innerHTML = '';
        photoDescriptions.innerHTML = '';

        if (files.length > 0) {
            submitBtn.disabled = false;

            Array.from(files).forEach((file, index) => {
                // Проверяем тип файла
                if (!file.type.startsWith('image/')) {
                    this.showError(`Файл ${file.name} не является изображением`);
                    return;
                }

                // Проверяем размер файла (максимум 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    this.showError(`Файл ${file.name} слишком большой (максимум 5MB)`);
                    return;
                }

                // Добавляем файл в список
                const fileItem = this.createFileItem(file, index);
                selectedFiles.appendChild(fileItem);

                // Добавляем поле для описания
                const descriptionDiv = this.createDescriptionField(index);
                photoDescriptions.appendChild(descriptionDiv);
            });
        } else {
            submitBtn.disabled = true;
        }
    }

    createFileItem(file, index) {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.innerHTML = `
            <div class="file-preview">
                <img src="${URL.createObjectURL(file)}" alt="Preview" class="file-thumbnail">
            </div>
            <div class="file-info">
                <div class="file-name">${file.name}</div>
                <div class="file-size">${this.formatFileSize(file.size)}</div>
            </div>
            <div class="file-actions">
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="studentHomework.removeFile(${index})">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;
        return fileItem;
    }

    createDescriptionField(index) {
        const descriptionDiv = document.createElement('div');
        descriptionDiv.className = 'form-group';
        descriptionDiv.innerHTML = `
            <label for="photo_description_${index}">Описание фото ${index + 1}:</label>
            <input type="text" name="photo_descriptions" id="photo_description_${index}" 
                   class="form-control" placeholder="Краткое описание...">
        `;
        return descriptionDiv;
    }

    removeFile(index) {
        const fileInput = document.getElementById('photos');
        const dt = new DataTransfer();
        const files = fileInput.files;

        for (let i = 0; i < files.length; i++) {
            if (i !== index) {
                dt.items.add(files[i]);
            }
        }

        fileInput.files = dt.files;
        this.handleFiles(fileInput.files);
    }

    validateForm() {
        const fileInput = document.getElementById('photos');
        const photos = fileInput.files;

        if (photos.length === 0) {
            this.showError('Пожалуйста, загрузите хотя бы одну фотографию выполненной работы.');
            return false;
        }

        // Проверяем размер всех файлов
        let totalSize = 0;
        for (let i = 0; i < photos.length; i++) {
            totalSize += photos[i].size;
        }

        if (totalSize > 50 * 1024 * 1024) { // 50MB общий лимит
            this.showError('Общий размер файлов не должен превышать 50MB.');
            return false;
        }

        return true;
    }

    async showPreview() {
        const form = document.getElementById('homework-form');
        if (!form) return;

        const formData = new FormData(form);
        formData.append('action', 'preview');

        try {
            const response = await fetch(window.location.pathname + 'preview/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            const data = await response.json();
            if (data.success) {
                this.displayPreview(data.preview);
            } else {
                this.showError(data.error || 'Ошибка предварительного просмотра');
            }
        } catch (error) {
            this.showError('Ошибка сети при загрузке предварительного просмотра');
        }
    }

    displayPreview(previewData) {
        const modal = document.getElementById('previewModal');
        const modalBody = modal.querySelector('.modal-body');
        
        let previewHTML = '<div class="preview-content">';
        previewHTML += '<h6>Предварительный просмотр:</h6>';
        previewHTML += '<div class="preview-files">';
        
        previewData.forEach((file, index) => {
            previewHTML += `
                <div class="preview-file">
                    <div class="preview-file-info">
                        <strong>Фото ${index + 1}:</strong> ${file.name}
                    </div>
                    <div class="preview-file-size">${this.formatFileSize(file.size)}</div>
                    ${file.description ? `<div class="preview-file-desc">Описание: ${file.description}</div>` : ''}
                </div>
            `;
        });
        
        previewHTML += '</div>';
        previewHTML += '<div class="preview-summary">';
        previewHTML += `<p>Всего фотографий: ${previewData.length}</p>`;
        previewHTML += '</div>';
        previewHTML += '</div>';
        
        modalBody.innerHTML = previewHTML;
        $(modal).modal('show');
    }

    async deletePhoto(photoId) {
        if (!confirm('Вы уверены, что хотите удалить эту фотографию?')) {
            return;
        }

        try {
            const response = await fetch(`/student/homework/photo/${photoId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            });

            const data = await response.json();
            if (data.success) {
                this.showSuccess(data.message);
                // Удаляем элемент из DOM
                const photoElement = document.querySelector(`[data-photo-id="${photoId}"]`);
                if (photoElement) {
                    photoElement.remove();
                }
            } else {
                this.showError(data.error || 'Ошибка удаления фотографии');
            }
        } catch (error) {
            this.showError('Ошибка сети при удалении фотографии');
        }
    }

    openPhotoModal(photoUrl, description) {
        const modal = document.getElementById('photoModal');
        const modalPhoto = modal.querySelector('#modalPhoto');
        const modalDescription = modal.querySelector('#modalDescription');
        
        modalPhoto.src = photoUrl;
        modalDescription.textContent = description;
        
        $(modal).modal('show');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} notification`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
            ${message}
            <button type="button" class="close" onclick="this.parentElement.remove()">
                <span>&times;</span>
            </button>
        `;

        // Добавляем стили для уведомления
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(notification);

        // Автоматически удаляем через 5 секунд
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    window.studentHomework = new StudentHomework();
});

// CSS для анимаций
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    .file-item {
        display: flex;
        align-items: center;
        padding: 0.75rem;
        background: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border: 1px solid #e9ecef;
    }

    .file-preview {
        width: 50px;
        height: 50px;
        margin-right: 1rem;
        border-radius: 8px;
        overflow: hidden;
    }

    .file-thumbnail {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    .file-info {
        flex: 1;
    }

    .file-name {
        font-weight: 600;
        color: #343a40;
        margin-bottom: 0.25rem;
    }

    .file-size {
        font-size: 0.875rem;
        color: #6c757d;
    }

    .preview-content {
        padding: 1rem;
    }

    .preview-files {
        margin: 1rem 0;
    }

    .preview-file {
        padding: 0.75rem;
        background: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border: 1px solid #e9ecef;
    }

    .preview-file-info {
        font-weight: 600;
        margin-bottom: 0.25rem;
    }

    .preview-file-size {
        font-size: 0.875rem;
        color: #6c757d;
        margin-bottom: 0.25rem;
    }

    .preview-file-desc {
        font-size: 0.875rem;
        color: #495057;
        font-style: italic;
    }

    .preview-summary {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #e9ecef;
        text-align: center;
        font-weight: 600;
    }
`;
document.head.appendChild(style);