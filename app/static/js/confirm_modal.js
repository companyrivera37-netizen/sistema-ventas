(function () {
  const overlay = document.getElementById("confirm-modal-overlay");
  const tituloEl = document.getElementById("confirm-modal-titulo");
  const mensajeEl = document.getElementById("confirm-modal-mensaje");
  const cerrarBtn = document.getElementById("confirm-modal-cerrar");
  const cancelarBtn = document.getElementById("confirm-modal-cancelar");
  const aceptarBtn = document.getElementById("confirm-modal-aceptar");
  if (!overlay) return;

  let formPendiente = null;

  function cerrarModal() {
    overlay.hidden = true;
    formPendiente = null;
  }

  document.querySelectorAll("form[data-confirm-mensaje]").forEach((form) => {
    form.addEventListener("submit", (evento) => {
      if (form.dataset.confirmado === "true") return;
      evento.preventDefault();
      formPendiente = form;
      tituloEl.textContent = form.dataset.confirmTitulo || "Confirmar acción";
      mensajeEl.textContent = form.dataset.confirmMensaje;
      overlay.hidden = false;
    });
  });

  aceptarBtn.addEventListener("click", () => {
    if (formPendiente) {
      formPendiente.dataset.confirmado = "true";
      if (formPendiente.requestSubmit) {
        formPendiente.requestSubmit();
      } else {
        formPendiente.submit();
      }
    }
    cerrarModal();
  });
  cancelarBtn.addEventListener("click", cerrarModal);
  cerrarBtn.addEventListener("click", cerrarModal);
  overlay.addEventListener("click", (evento) => {
    if (evento.target === overlay) cerrarModal();
  });
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && !overlay.hidden) cerrarModal();
  });
})();
