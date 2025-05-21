document.addEventListener('DOMContentLoaded', () => {
    const formComentario = document.getElementById('form-comentario');
    if (!formComentario) return;

    formComentario.addEventListener('submit', async (e) => {
        e.preventDefault();
        const textarea = formComentario.querySelector('textarea');
        const contenido = textarea.value.trim();
        if (!contenido) {
            alert('El comentario no puede estar vacío.');
            return;
        }

        const hiloId = window.location.pathname.split('/').pop();

        try {
            const response = await fetch(`/comentario_ajax/${hiloId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contenido })
            });

            if (!response.ok) {
                const data = await response.json();
                alert(data.error || 'Error al enviar comentario.');
                return;
            }

            const data = await response.json();

            // Agregar comentario al DOM
            const divComentarios = document.getElementById('comentarios');
            const nuevoComentario = document.createElement('div');
            nuevoComentario.classList.add('comentario');
            nuevoComentario.innerHTML = `<p><strong>${data.usuario}</strong> <small>${data.fecha}</small></p><p>${data.contenido}</p>`;

            divComentarios.appendChild(nuevoComentario);

            textarea.value = '';
        } catch (error) {
            alert('Error de red o servidor.');
        }
    });
});
